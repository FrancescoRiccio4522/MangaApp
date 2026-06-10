import os
import sys
import threading
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import filedialog, messagebox


def _resource(relative_path):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MangaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self._build_ui()

    def _build_ui(self):
        self.title("🏴‍☠️ Manga Downloader")
        self.geometry("700x620")
        self.resizable(False, False)

        try:
            icon_path = _resource("icon.png")
            img = ImageTk.PhotoImage(Image.open(icon_path))
            self.iconphoto(True, img)
        except Exception:
            pass

        # Header
        header = ctk.CTkLabel(
            self, text=" MANGA DOWNLOADER & PDF CREATOR",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header.pack(pady=(24, 16))

        # Form frame
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=24, pady=4)
        form.columnconfigure(1, weight=1)

        # URL
        ctk.CTkLabel(form, text="Link capitolo:", anchor="w").grid(row=0, column=0, padx=12, pady=10, sticky="w")
        self.url_entry = ctk.CTkEntry(form, placeholder_text="https://...", width=420)
        self.url_entry.grid(row=0, column=1, columnspan=2, padx=8, pady=10, sticky="ew")

        # Cartella destinazione
        ctk.CTkLabel(form, text="Cartella:", anchor="w").grid(row=1, column=0, padx=12, pady=10, sticky="w")
        self.path_entry = ctk.CTkEntry(form, placeholder_text="es. /home/utente/Downloads", width=340)
        self.path_entry.grid(row=1, column=1, padx=8, pady=10, sticky="ew")
        ctk.CTkButton(form, text="Sfoglia", width=70, command=self._scegli_cartella).grid(row=1, column=2, padx=8)

        # Nome capitolo
        ctk.CTkLabel(form, text="Nome capitolo:", anchor="w").grid(row=2, column=0, padx=12, pady=10, sticky="w")
        self.nome_entry = ctk.CTkEntry(form, placeholder_text="es. Cap22")
        self.nome_entry.grid(row=2, column=1, columnspan=2, padx=8, pady=10, sticky="ew")

        # Pulsanti azione
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=16)

        self.btn_download = ctk.CTkButton(
            btn_frame, text="📥  Solo Download", width=180,
            command=lambda: self._avvia(solo_pdf=False, solo_download=True)
        )
        self.btn_download.grid(row=0, column=0, padx=8)

        self.btn_pdf = ctk.CTkButton(
            btn_frame, text="📄  Solo PDF", width=180,
            fg_color="#2e7d32", hover_color="#1b5e20",
            command=lambda: self._avvia(solo_pdf=True, solo_download=False)
        )
        self.btn_pdf.grid(row=0, column=1, padx=8)

        self.btn_tutto = ctk.CTkButton(
            btn_frame, text="🚀  Fai Tutto!", width=180,
            fg_color="#6a1b9a", hover_color="#4a148c",
            command=lambda: self._avvia(solo_pdf=False, solo_download=False)
        )
        self.btn_tutto.grid(row=0, column=2, padx=8)

        # Progress bar
        self.progress = ctk.CTkProgressBar(self, width=650)
        self.progress.pack(pady=(4, 0))
        self.progress.set(0)

        self.progress_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12))
        self.progress_label.pack(pady=(2, 8))

        # Log
        self.log_box = ctk.CTkTextbox(self, width=650, height=220, font=ctk.CTkFont(family="monospace", size=12))
        self.log_box.pack(padx=24, pady=(0, 16))
        self.log_box.configure(state="disabled")

    # ── helpers UI ──────────────────────────────────────────────

    def _scegli_cartella(self):
        path = filedialog.askdirectory()
        if path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, path)

    def _log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _set_progress(self, value, label=""):
        self.progress.set(value)
        self.progress_label.configure(text=label)

    def _set_buttons(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for b in (self.btn_download, self.btn_pdf, self.btn_tutto):
            b.configure(state=state)

    # ── logica ──────────────────────────────────────────────────

    def _avvia(self, solo_pdf: bool, solo_download: bool):
        self._set_buttons(False)
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self._set_progress(0)
        threading.Thread(target=self._run, args=(solo_pdf, solo_download), daemon=True).start()

    def _run(self, solo_pdf: bool, solo_download: bool):
        try:
            if solo_pdf:
                percorso = self.path_entry.get().strip().strip("'\"")
                nome = self.nome_entry.get().strip() or os.path.basename(percorso) or "Manga_Capitolo"
                self._crea_pdf(percorso, nome)
            elif solo_download:
                self._scarica_capitolo()
            else:
                percorso = self._scarica_capitolo()
                if percorso:
                    nome = os.path.basename(percorso)
                    self._crea_pdf(percorso, nome)
        finally:
            self.after(0, lambda: self._set_buttons(True))

    def _scarica_capitolo(self):
        url = self.url_entry.get().strip()
        if not url:
            self.after(0, lambda: messagebox.showerror("Errore", "Inserisci un link!"))
            return None

        percorso_base = self.path_entry.get().strip().strip("'\"") or "."
        nome_cartella = self.nome_entry.get().strip() or "Tavole_Manga"
        percorso_completo = os.path.join(percorso_base, nome_cartella)
        os.makedirs(percorso_completo, exist_ok=True)

        self.after(0, lambda: self._log("Connessione alla pagina..."))
        self.headers["Referer"] = url

        try:
            risposta = requests.get(url, headers=self.headers)
            if risposta.status_code != 200:
                msg = f"Errore di connessione: {risposta.status_code}"
                self.after(0, lambda: self._log(f"❌ {msg}"))
                return None
        except Exception as e:
            self.after(0, lambda: self._log(f"❌ Errore rete: {e}"))
            return None

        soup = BeautifulSoup(risposta.text, "html.parser")

        ATTRS = ["data-src", "data-lazy-src", "data-original", "data-url", "data-cfsrc", "src"]
        ESTENSIONI_VALIDE = (".jpg", ".jpeg", ".png", ".webp")

        def estrai_src(img_tag):
            for attr in ATTRS:
                val = img_tag.get(attr, "").strip()
                if val and any(val.lower().split("?")[0].endswith(ext) for ext in ESTENSIONI_VALIDE):
                    return val
            return None

        immagini_src = []

        # Cerca in tutti i tag <img> normali
        for img in soup.find_all("img"):
            src = estrai_src(img)
            if src and src not in immagini_src:
                immagini_src.append(src)

        # Cerca anche dentro tag <noscript> (lazy loading comune)
        for noscript in soup.find_all("noscript"):
            inner = BeautifulSoup(noscript.get_text(), "html.parser")
            for img in inner.find_all("img"):
                src = estrai_src(img)
                if src and src not in immagini_src:
                    immagini_src.append(src)

        # Debug: mostra tutti i tag img trovati nel log
        tutti_img = soup.find_all("img")
        self.after(0, lambda n=len(tutti_img): self._log(f"🔍 Tag <img> totali nella pagina: {n}"))
        self.after(0, lambda n=len(immagini_src): self._log(f"🔍 Con URL immagine valido: {n}"))

        totale = len(immagini_src)
        if totale == 0:
            self.after(0, lambda: self._log("❌ Nessuna tavola trovata nella pagina."))
            return None

        self.after(0, lambda: self._log(f"Inizio download..."))
        contatore = 1

        for i, src in enumerate(immagini_src):
            try:
                img_risposta = requests.get(src, headers=self.headers, timeout=15)
                if img_risposta.status_code == 200 and len(img_risposta.content) > 5000:
                    estensione = ".png" if ".png" in src else ".webp" if ".webp" in src else ".jpg"
                    nome_file = os.path.join(percorso_completo, f"{contatore:03d}{estensione}")
                    with open(nome_file, "wb") as f:
                        f.write(img_risposta.content)
                    n = contatore
                    self.after(0, lambda n=n: self._log(f"  ✅ Tavola {n:02d} salvata"))
                    contatore += 1
                elif img_risposta.status_code != 200:
                    self.after(0, lambda: self._log(f"  ⚠️ Saltata (HTTP {img_risposta.status_code})"))
                # else: immagine troppo piccola (icona/logo), ignorata silenziosamente
            except Exception as e:
                self.after(0, lambda e=e: self._log(f"  ⚠️ Errore: {e}"))

            progress_val = (i + 1) / totale * 0.9
            label = f"Download: {i+1}/{totale}"
            self.after(0, lambda v=progress_val, l=label: self._set_progress(v, l))

        finale = contatore - 1
        self.after(0, lambda: self._log(f"\n🎉 Download completato! {finale} tavole in '{percorso_completo}'"))
        return percorso_completo

    def _crea_pdf(self, percorso, nome_capitolo):
        if not percorso or not os.path.exists(percorso):
            self.after(0, lambda: messagebox.showerror("Errore", "Cartella non trovata!"))
            return

        file_list = sorted([
            f for f in os.listdir(percorso)
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
        ])

        if not file_list:
            self.after(0, lambda: self._log("❌ Nessuna immagine trovata nella cartella."))
            return

        self.after(0, lambda: self._log(f"\nCreazione PDF da {len(file_list)} tavole..."))

        immagini_da_unire = []
        prima_immagine = None

        for i, nome_file in enumerate(file_list):
            try:
                img = Image.open(os.path.join(percorso, nome_file)).convert("RGB")
                if prima_immagine is None:
                    prima_immagine = img
                else:
                    immagini_da_unire.append(img)
            except Exception as e:
                self.after(0, lambda e=e: self._log(f"  ⚠️ Impossibile leggere '{nome_file}': {e}"))

            progress_val = 0.9 + (i + 1) / len(file_list) * 0.1
            label = f"PDF: {i+1}/{len(file_list)}"
            self.after(0, lambda v=progress_val, l=label: self._set_progress(v, l))

        if prima_immagine is None:
            self.after(0, lambda: self._log("❌ Impossibile creare PDF."))
            return

        nome_pdf = os.path.join(percorso, f"{nome_capitolo}.pdf")
        try:
            prima_immagine.save(nome_pdf, save_all=True, append_images=immagini_da_unire)
            self.after(0, lambda: self._set_progress(1.0, "Completato!"))
            self.after(0, lambda: self._log(f"\n✅ PDF pronto: {nome_pdf}"))
        except Exception as e:
            self.after(0, lambda: self._log(f"\n❌ Errore salvataggio PDF: {e}"))


if __name__ == "__main__":
    app = MangaApp()
    app.mainloop()
