"""Manga Downloader: incolla il link di un capitolo e ottieni il PDF.

L'app scarica la pagina, trova le tavole, le scarica e le unisce in un PDF
che finisce nella cartella scelta (di default ~/Downloads/Manga).
"""

import io
import json
import os
import queue
import re
import subprocess
import sys
import threading
import traceback
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from tkinter import Menu, filedialog
from urllib.parse import unquote, urljoin, urlparse

import customtkinter as ctk
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageTk
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

APP_NAME = "MangaApp"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

IMG_ATTRS = ("data-src", "data-lazy-src", "data-original", "data-url", "data-cfsrc",
             "data-srcset", "srcset", "src")
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")
# Regex di riserva per i siti che mettono la lista delle tavole in uno script JS
IMG_URL_RE = re.compile(r"https?://[^\s\"'<>()]+?\.(?:jpe?g|png|webp)(?:\?[^\s\"'<>()]*)?", re.I)
DOWNLOAD_PARALLELI = 4


class ErroreDownload(Exception):
    """Errore da mostrare all'utente così com'è."""


class Annullato(Exception):
    pass


# ── percorsi e configurazione ───────────────────────────────────

def _resource(relative_path):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


def _file_config():
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home())
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / APP_NAME / "config.json"


def carica_config():
    config = {"cartella": str(Path.home() / "Downloads" / "Manga"), "tema": "system"}
    try:
        config.update(json.loads(_file_config().read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return config


def salva_config(config):
    try:
        f = _file_config()
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(config, indent=2), encoding="utf-8")
    except OSError:
        pass


def apri_nel_sistema(percorso, mostra_nella_cartella=False):
    """Apre un file (o lo evidenzia nel Finder / Esplora file)."""
    p = str(percorso)
    if sys.platform == "darwin":
        subprocess.Popen(["open", "-R", p] if mostra_nella_cartella else ["open", p])
    elif sys.platform == "win32":
        if mostra_nella_cartella:
            subprocess.Popen(f'explorer /select,"{p}"')
        else:
            os.startfile(p)
    else:
        env = os.environ.copy()
        # L'eseguibile PyInstaller altera LD_LIBRARY_PATH: xdg-open vuole quello originale
        if getattr(sys, "frozen", False):
            if "LD_LIBRARY_PATH_ORIG" in env:
                env["LD_LIBRARY_PATH"] = env["LD_LIBRARY_PATH_ORIG"]
            else:
                env.pop("LD_LIBRARY_PATH", None)
        subprocess.Popen(["xdg-open", os.path.dirname(p) if mostra_nella_cartella else p], env=env)


# ── scraping ────────────────────────────────────────────────────

def nuova_sessione():
    session = requests.Session()
    retry = Retry(total=2, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504))
    session.mount("http://", HTTPAdapter(max_retries=retry, pool_maxsize=DOWNLOAD_PARALLELI))
    session.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=DOWNLOAD_PARALLELI))
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    })
    return session


def normalizza_url(url):
    url = url.strip().strip("'\"<>")
    if not url:
        raise ErroreDownload("Incolla prima il link del capitolo.")
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url.lstrip("/")
    if not urlparse(url).netloc:
        raise ErroreDownload("Il link non sembra valido.")
    return url


def _e_immagine(url):
    return urlparse(url).path.lower().endswith(IMG_EXT)


def _candidati_tag(tag):
    for attr in IMG_ATTRS:
        val = (tag.get(attr) or "").strip()
        if not val:
            continue
        if "srcset" in attr:
            # "a.jpg 400w, b.jpg 800w": l'ultima di solito è la più grande
            voci = [v.split()[0] for v in val.split(",") if v.strip()]
            val = voci[-1] if voci else ""
        yield val


def trova_immagini(html, base_url):
    """Ritorna (soup, lista ordinata e senza doppioni degli URL delle tavole)."""
    soup = BeautifulSoup(html, "html.parser")
    trovate = {}

    def aggiungi_da(tag):
        for val in _candidati_tag(tag):
            assoluto = urljoin(base_url, val)
            if assoluto.startswith(("http://", "https://")) and _e_immagine(assoluto):
                trovate.setdefault(assoluto, None)
                return

    for img in soup.find_all("img"):
        aggiungi_da(img)
    # Molti siti con lazy-loading mettono la versione "vera" dentro <noscript>
    for noscript in soup.find_all("noscript"):
        for img in BeautifulSoup(noscript.get_text(), "html.parser").find_all("img"):
            aggiungi_da(img)

    if not trovate:
        for match in IMG_URL_RE.findall(html.replace("\\/", "/")):
            trovate.setdefault(match, None)

    return soup, list(trovate)


def _segmenti_url(url):
    """'/manga/one-piece/capitolo-1100.html' -> ['Manga', 'One Piece', 'Capitolo 1100']"""
    segmenti = []
    for s in urlparse(url).path.split("/"):
        s = re.sub(r"\.(html?|php|aspx?)$", "", unquote(s), flags=re.I)
        s = re.sub(r"[\s_-]+", " ", s).strip()
        if s:
            segmenti.append(s.title())
    return segmenti


def nome_capitolo(soup, url):
    """Ricava un nome leggibile dal titolo della pagina, ripulito dal nome del sito."""
    titolo = ""
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        titolo = og["content"]
    elif soup.title and soup.title.string:
        titolo = soup.title.string
    elif soup.h1:
        titolo = soup.h1.get_text(" ")
    titolo = re.sub(r"\s+", " ", titolo).strip()

    host = urlparse(url).hostname or ""
    etichette = [e for e in host.split(".")[:-1] if e not in ("www", "m")]
    sito = max(etichette, key=len, default="").replace("-", "")

    def senza_sito(parte):
        normale = re.sub(r"[^a-z0-9]", "", parte.lower())
        return not sito or len(sito) < 4 or sito not in normale

    def pulisci(parte):
        parte = re.sub(r"^(read|leggi)\s+", "", parte.strip(), flags=re.I)
        return re.sub(r"\s+(online|in italiano)(\s+(free|gratis))?$", "", parte, flags=re.I)

    parti = [pulisci(p) for p in re.split(r"\s+(?:[|\-–—»·]|::)\s+", titolo) if p.strip()]
    utili = [p for p in parti if senza_sito(p)] or parti[:1]
    nome = " - ".join(utili)

    segmenti = _segmenti_url(url)
    if not nome:
        nome = " ".join(segmenti[-2:])
    elif segmenti and not re.search(r"\d", nome) and re.search(r"\d", segmenti[-1]):
        # Il titolo ha solo il nome del manga: aggiungiamo il capitolo preso dal link
        nome = f"{nome} {segmenti[-1]}"
    return nome_file_sicuro(nome)


def nome_file_sicuro(nome):
    nome = re.sub(r'[<>:"/\\|?*\x00-\x1f]', " ", nome)
    nome = re.sub(r"\s+", " ", nome).strip(" .")
    return nome[:120].rstrip(" .") or "Capitolo"


def percorso_libero(cartella, nome, estensione=".pdf"):
    percorso = cartella / f"{nome}{estensione}"
    n = 2
    while percorso.exists():
        percorso = cartella / f"{nome} ({n}){estensione}"
        n += 1
    return percorso


def _e_una_tavola(img):
    # Loghi, avatar e banner pubblicitari sono piccoli o molto stretti
    larghezza, altezza = img.size
    return max(larghezza, altezza) >= 400 and min(larghezza, altezza) >= 100


def _per_pdf(img):
    if img.mode in ("RGB", "L"):
        return img
    if img.mode in ("RGBA", "LA", "PA") or "transparency" in img.info:
        img = img.convert("RGBA")
        fondo = Image.new("RGB", img.size, "white")
        fondo.paste(img, mask=img.getchannel("A"))
        return fondo
    return img.convert("RGB")


def _scarica_tavola(session, url, referer):
    risposta = session.get(url, headers={"Referer": referer}, timeout=30)
    risposta.raise_for_status()
    img = Image.open(io.BytesIO(risposta.content))
    img.load()
    return img


def _scarica_pagina(session, url):
    try:
        risposta = session.get(url, timeout=20)
    except requests.RequestException as e:
        raise ErroreDownload(f"Impossibile raggiungere il sito. Controlla la connessione.\n({e})")
    if risposta.status_code in (403, 503) and (
        "cf-ray" in risposta.headers or "Just a moment" in risposta.text
    ):
        raise ErroreDownload("Il sito è protetto da Cloudflare e blocca i download automatici.")
    if risposta.status_code == 404:
        raise ErroreDownload("Pagina non trovata (404): controlla il link.")
    if risposta.status_code != 200:
        raise ErroreDownload(f"Il sito ha risposto con un errore (HTTP {risposta.status_code}).")
    return risposta.text


def crea_pdf_da_link(url, cartella, log, progresso, stop):
    """Scarica tutte le tavole del capitolo e le salva in un unico PDF.

    `log(testo)` e `progresso(valore 0..1, testo)` vengono chiamate dal thread
    di lavoro; `stop` è un threading.Event per annullare.
    """
    url = normalizza_url(url)
    cartella = Path(cartella).expanduser()
    session = nuova_sessione()

    progresso(0.02, "Apro la pagina…")
    log(f"Pagina: {url}")
    html = _scarica_pagina(session, url)

    soup, urls = trova_immagini(html, url)
    nome = nome_capitolo(soup, url)
    log(f"Capitolo: {nome}")
    log(f"Immagini trovate: {len(urls)}")
    if not urls:
        raise ErroreDownload(
            "Nessuna tavola trovata. Assicurati che il link sia la pagina di lettura "
            "del capitolo (quella con le tavole), non la scheda del manga."
        )

    tavole = [None] * len(urls)
    fatte = 0
    with ThreadPoolExecutor(max_workers=DOWNLOAD_PARALLELI) as pool:
        futuri = {pool.submit(_scarica_tavola, session, u, url): i for i, u in enumerate(urls)}
        try:
            for futuro in _in_ordine_di_arrivo(futuri, stop):
                i = futuri[futuro]
                try:
                    img = futuro.result()
                    if _e_una_tavola(img):
                        tavole[i] = img
                    else:
                        log(f"  · ignorata immagine piccola {img.size[0]}×{img.size[1]}")
                except Exception as e:
                    log(f"  ⚠ immagine {i + 1} non scaricata: {e}")
                fatte += 1
                progresso(0.05 + 0.80 * fatte / len(urls), f"Scarico le tavole… {fatte}/{len(urls)}")
        except Annullato:
            pool.shutdown(wait=False, cancel_futures=True)
            raise

    tavole = [t for t in tavole if t is not None]
    log(f"Tavole valide: {len(tavole)}")
    if not tavole:
        raise ErroreDownload("Non sono riuscito a scaricare nessuna tavola da questa pagina.")

    pagine = []
    for i, img in enumerate(tavole):
        if stop.is_set():
            raise Annullato()
        pagine.append(_per_pdf(img))
        progresso(0.85 + 0.10 * (i + 1) / len(tavole), f"Creo il PDF… {i + 1}/{len(tavole)}")

    try:
        cartella.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise ErroreDownload(f"Non riesco a creare la cartella '{cartella}': {e}")
    destinazione = percorso_libero(cartella, nome)
    temporaneo = destinazione.with_name(destinazione.name + ".part")
    try:
        pagine[0].save(temporaneo, "PDF", save_all=True, append_images=pagine[1:],
                       title=nome, quality=90)
        os.replace(temporaneo, destinazione)
    except OSError as e:
        temporaneo.unlink(missing_ok=True)
        raise ErroreDownload(f"Non riesco a salvare il PDF: {e}")

    progresso(1.0, "Fatto!")
    log(f"PDF salvato: {destinazione}")
    return destinazione


def _in_ordine_di_arrivo(futuri, stop):
    in_attesa = set(futuri)
    while in_attesa:
        if stop.is_set():
            raise Annullato()
        completati, in_attesa = wait(in_attesa, timeout=0.2, return_when=FIRST_COMPLETED)
        yield from completati


# ── interfaccia ─────────────────────────────────────────────────

TEMI = {"Sistema": "system", "Chiaro": "light", "Scuro": "dark"}
LARGHEZZA = 620
ROSSO = ("#c62828", "#d32f2f")
ROSSO_HOVER = ("#a31f1f", "#b71c1c")
VERDE = ("#2e7d32", "#66bb6a")
GRIGIO_TESTO = ("#5f6368", "#a0a4a8")
# Pulsanti secondari neutri: il rosso resta solo per l'azione principale
SECONDARIO = dict(fg_color=("gray84", "gray27"), hover_color=("gray77", "gray33"),
                  text_color=("gray10", "gray92"))


def _font_mono():
    if sys.platform == "darwin":
        return "Menlo"
    if sys.platform == "win32":
        return "Consolas"
    return "DejaVu Sans Mono"


def _abbrevia(percorso):
    home = str(Path.home())
    p = str(percorso)
    return "~" + p[len(home):] if p.startswith(home) else p


class MangaApp(ctk.CTk):
    def __init__(self):
        self.config_app = carica_config()
        ctk.set_appearance_mode(self.config_app.get("tema", "system"))
        ctk.set_default_color_theme("blue")
        super().__init__()

        self._coda = queue.Queue()
        self._stop = threading.Event()
        self._lavoro_attivo = False
        self._ultimo_pdf = None

        self._imposta_icona()
        self._costruisci_ui()
        self._applica_tema_finestra(self.config_app.get("tema", "system"))
        self.after(60, self._processa_coda)

    # ── costruzione UI ──────────────────────────────────────────

    def _imposta_icona(self):
        try:
            if sys.platform == "win32":
                # Su Windows CustomTkinter sostituisce l'icona se non si usa iconbitmap
                self.iconbitmap(_resource("icon.ico"))
            else:
                img = Image.open(_resource("icon.png")).resize((256, 256), Image.LANCZOS)
                self._icona = ImageTk.PhotoImage(img)
                self.iconphoto(True, self._icona)
        except Exception:
            pass

    def _costruisci_ui(self):
        self.title("Manga Downloader")
        # Larghezza fissa, altezza che si adatta al contenuto (dettagli, risultato…)
        self.minsize(LARGHEZZA, 0)
        self.resizable(False, False)
        self.columnconfigure(0, weight=1)

        # Intestazione: titolo + selettore tema
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        top.columnconfigure(0, weight=1)
        ctk.CTkLabel(top, text="Manga Downloader",
                     font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w")
        etichetta_tema = next((k for k, v in TEMI.items() if v == self.config_app.get("tema")),
                              "Sistema")
        self.tema = ctk.CTkSegmentedButton(
            top, values=list(TEMI), command=self._cambia_tema,
            fg_color=("gray84", "gray20"), unselected_color=("gray84", "gray20"),
            unselected_hover_color=("gray78", "gray26"),
            selected_color=("white", "gray38"), selected_hover_color=("white", "gray42"),
            text_color=("gray10", "gray92"),
        )
        self.tema.set(etichetta_tema)
        self.tema.grid(row=0, column=1, sticky="e")
        ctk.CTkLabel(top, text="Incolla il link del capitolo: al resto pensa l'app.",
                     text_color=GRIGIO_TESTO).grid(row=1, column=0, columnspan=2, sticky="w")

        # Link + Incolla
        riga_link = ctk.CTkFrame(self, fg_color="transparent")
        riga_link.grid(row=1, column=0, sticky="ew", padx=24, pady=(18, 0))
        riga_link.columnconfigure(0, weight=1)
        self.url_entry = ctk.CTkEntry(riga_link, height=40, placeholder_text="https://…")
        self.url_entry.grid(row=0, column=0, sticky="ew")
        self.url_entry.bind("<Return>", lambda _e: self._avvia_o_annulla())
        self.btn_incolla = ctk.CTkButton(riga_link, text="Incolla", width=90, height=40,
                                         command=self._incolla, **SECONDARIO)
        self.btn_incolla.grid(row=0, column=1, padx=(8, 0))
        self._menu_contestuale()

        # Pulsante principale
        self.btn_scarica = ctk.CTkButton(
            self, text="Scarica PDF", height=46,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=ROSSO, hover_color=ROSSO_HOVER,
            command=self._avvia_o_annulla,
        )
        self.btn_scarica.grid(row=2, column=0, sticky="ew", padx=24, pady=(12, 0))

        # Stato + barra di avanzamento (la barra si vede solo mentre lavora)
        self.stato = ctk.CTkLabel(self, text="Pronto.", anchor="w", justify="left",
                                  text_color=GRIGIO_TESTO, wraplength=LARGHEZZA - 48)
        self.stato.grid(row=3, column=0, sticky="ew", padx=24, pady=(14, 0))
        self.progress = ctk.CTkProgressBar(self, height=8, progress_color=ROSSO)
        self.progress.set(0)

        # Risultato (compare a fine lavoro)
        self.risultato = ctk.CTkFrame(self)
        self.risultato.columnconfigure(0, weight=1)
        self.risultato_testo = ctk.CTkLabel(self.risultato, text="", anchor="w",
                                            text_color=VERDE, font=ctk.CTkFont(weight="bold"))
        self.risultato_testo.grid(row=0, column=0, sticky="ew", padx=(14, 8), pady=10)
        ctk.CTkButton(self.risultato, text="Apri PDF", width=90, **SECONDARIO,
                      command=lambda: self._apri_ultimo(False)).grid(row=0, column=1, padx=4)
        ctk.CTkButton(self.risultato, text="Mostra nella cartella", width=150, **SECONDARIO,
                      command=lambda: self._apri_ultimo(True)).grid(row=0, column=2, padx=(4, 10))

        # Dettagli (log) nascosti di default
        self.btn_dettagli = ctk.CTkButton(
            self, text="▸ Mostra dettagli", width=0, fg_color="transparent",
            hover=False, text_color=GRIGIO_TESTO, anchor="w", command=self._toggle_dettagli,
        )
        self.btn_dettagli.grid(row=6, column=0, sticky="w", padx=18, pady=(10, 0))
        self.log_box = ctk.CTkTextbox(self, height=160,
                                      font=ctk.CTkFont(family=_font_mono(), size=12))
        self.log_box.configure(state="disabled")

        # Piè di pagina: dove si salva
        piede = ctk.CTkFrame(self, fg_color="transparent")
        piede.grid(row=8, column=0, sticky="ew", padx=24, pady=(10, 18))
        piede.columnconfigure(0, weight=1)
        self.cartella_label = ctk.CTkLabel(piede, text="", anchor="w", text_color=GRIGIO_TESTO)
        self.cartella_label.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(piede, text="Cambia…", width=80, **SECONDARIO,
                      command=self._scegli_cartella).grid(row=0, column=1)
        self._aggiorna_cartella_label()

        self.url_entry.focus_set()

    def _menu_contestuale(self):
        menu = Menu(self, tearoff=0)
        menu.add_command(label="Incolla", command=self._incolla)
        menu.add_command(label="Svuota", command=lambda: self.url_entry.delete(0, "end"))

        def mostra(evento):
            menu.tk_popup(evento.x_root, evento.y_root)

        # Tasto destro: Button-2 / Ctrl+clic su macOS, Button-3 altrove
        if sys.platform == "darwin":
            self.url_entry.bind("<Button-2>", mostra)
            self.url_entry.bind("<Control-Button-1>", mostra)
        else:
            self.url_entry.bind("<Button-3>", mostra)

    # ── azioni UI ───────────────────────────────────────────────

    def _incolla(self):
        try:
            testo = self.clipboard_get().strip()
        except Exception:
            return
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, testo)

    def _cambia_tema(self, etichetta):
        tema = TEMI[etichetta]
        ctk.set_appearance_mode(tema)
        self._applica_tema_finestra(tema)
        self.config_app["tema"] = tema
        salva_config(self.config_app)

    def _applica_tema_finestra(self, tema):
        # Su macOS allinea anche la barra del titolo della finestra al tema scelto
        if sys.platform == "darwin":
            aspetto = {"light": "aqua", "dark": "darkaqua"}.get(tema, "auto")
            try:
                self.tk.call("::tk::unsupported::MacWindowStyle", "appearance", self._w, aspetto)
            except Exception:
                pass

    def _scegli_cartella(self):
        iniziale = Path(self.config_app["cartella"]).expanduser()
        while not iniziale.exists() and iniziale != iniziale.parent:
            iniziale = iniziale.parent
        scelta = filedialog.askdirectory(parent=self, initialdir=str(iniziale),
                                         title="Dove salvo i PDF?")
        if scelta:
            self.config_app["cartella"] = scelta
            salva_config(self.config_app)
            self._aggiorna_cartella_label()

    def _aggiorna_cartella_label(self):
        self.cartella_label.configure(text=f"Salva in: {_abbrevia(self.config_app['cartella'])}")

    def _toggle_dettagli(self):
        if self.log_box.winfo_ismapped():
            self.log_box.grid_remove()
            self.btn_dettagli.configure(text="▸ Mostra dettagli")
        else:
            self.log_box.grid(row=7, column=0, sticky="nsew", padx=24, pady=(4, 0))
            self.btn_dettagli.configure(text="▾ Nascondi dettagli")

    def _apri_ultimo(self, mostra_nella_cartella):
        if self._ultimo_pdf and self._ultimo_pdf.exists():
            try:
                apri_nel_sistema(self._ultimo_pdf, mostra_nella_cartella)
            except Exception as e:
                self._log(f"Impossibile aprire: {e}")

    def _log(self, testo):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", testo + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _imposta_stato(self, testo, errore=False):
        self.stato.configure(text=testo, text_color=ROSSO if errore else GRIGIO_TESTO)

    # ── lavoro in background ────────────────────────────────────

    def _avvia_o_annulla(self):
        if self._lavoro_attivo:
            self._stop.set()
            self.btn_scarica.configure(state="disabled", text="Annullo…")
            return

        url = self.url_entry.get()
        cartella = self.config_app["cartella"]
        self._stop.clear()
        self._lavoro_attivo = True
        self._ultimo_pdf = None
        self.risultato.grid_remove()
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self.progress.set(0)
        self.progress.grid(row=4, column=0, sticky="ew", padx=24, pady=(6, 0))
        self._imposta_stato("Inizio…")
        self.btn_scarica.configure(text="Annulla", fg_color=("gray55", "gray35"),
                                   hover_color=("gray45", "gray30"))
        self.url_entry.configure(state="disabled")
        self.btn_incolla.configure(state="disabled")
        threading.Thread(target=self._lavora, args=(url, cartella), daemon=True).start()

    def _lavora(self, url, cartella):
        # Gira nel thread secondario: comunica con la UI solo tramite la coda
        manda = self._coda.put
        try:
            pdf = crea_pdf_da_link(
                url, cartella,
                log=lambda t: manda(("log", t)),
                progresso=lambda v, t: manda(("progresso", v, t)),
                stop=self._stop,
            )
            manda(("fine", pdf, None))
        except Annullato:
            manda(("fine", None, "Download annullato."))
        except ErroreDownload as e:
            manda(("fine", None, str(e)))
        except Exception as e:
            manda(("log", traceback.format_exc()))
            manda(("fine", None, f"Errore imprevisto: {e}"))

    def _processa_coda(self):
        try:
            while True:
                messaggio = self._coda.get_nowait()
                tipo = messaggio[0]
                if tipo == "log":
                    self._log(messaggio[1])
                elif tipo == "progresso":
                    self.progress.set(messaggio[1])
                    self._imposta_stato(messaggio[2])
                elif tipo == "fine":
                    self._fine(messaggio[1], messaggio[2])
        except queue.Empty:
            pass
        self.after(60, self._processa_coda)

    def _fine(self, pdf, errore):
        self._lavoro_attivo = False
        self.btn_scarica.configure(state="normal", text="Scarica PDF",
                                   fg_color=ROSSO, hover_color=ROSSO_HOVER)
        self.url_entry.configure(state="normal")
        self.btn_incolla.configure(state="normal")
        self.progress.grid_remove()
        if errore:
            self._imposta_stato(errore, errore=True)
            self._log(errore)
            return
        self._ultimo_pdf = pdf
        self._imposta_stato("Fatto! Il PDF è pronto.")
        nome = pdf.name if len(pdf.name) <= 42 else pdf.name[:39] + "…"
        self.risultato_testo.configure(text=f"✓  {nome}")
        self.risultato.grid(row=5, column=0, sticky="ew", padx=24, pady=(14, 0))


if __name__ == "__main__":
    app = MangaApp()
    if os.environ.get("MANGAAPP_SMOKE_TEST"):  # usato dalla CI per provare la build
        app.after(2000, app.destroy)
    app.mainloop()
