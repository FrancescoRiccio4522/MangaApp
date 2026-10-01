# 🏴‍☠️ Manga Downloader

Incolla il link di un capitolo manga, premi **Scarica PDF**: l'app trova le tavole, le scarica e ti dà il PDF pronto.

Funziona su **macOS** (chip Apple e Intel), **Windows** e **Linux**.

---

## Indice

- [Scaricare l'app](#scaricare-lapp)
- [Installazione su macOS](#installazione-su-macos)
- [Installazione su Windows](#installazione-su-windows)
- [Installazione su Linux](#installazione-su-linux)
- [Come si usa](#come-si-usa)
- [Aggiornare l'app](#aggiornare-lapp)
- [Problemi comuni](#problemi-comuni)
- [Per sviluppatori](#per-sviluppatori)

---

## Scaricare l'app

L'app viene creata in automatico da GitHub a ogni modifica del codice. Per scaricarla serve essere **loggati su GitHub**.

### 1. Apri l'elenco delle versioni

| Versione | Link |
|---|---|
| **Stabile** (branch `main`) | [Apri le build di main](https://github.com/FrancescoRiccio4522/MangaApp/actions/workflows/build.yml?query=branch%3Amain) |
| **Di prova** (branch `manga-test`) | [Apri le build di manga-test](https://github.com/FrancescoRiccio4522/MangaApp/actions/workflows/build.yml?query=branch%3Amanga-test) |

### 2. Scegli la build più recente

Clicca la **prima riga in alto** che ha la spunta verde ✅. Le righe con la ❌ rossa non hanno prodotto l'app; quelle con il pallino giallo 🟡 sono ancora in corso (servono 2-3 minuti).

### 3. Scarica il file per il tuo sistema

Scorri la pagina fino alla sezione **Artifacts** in fondo e clicca il nome giusto:

| Sistema | Clicca su | Cosa trovi dentro |
|---|---|---|
| Mac con **chip Apple** (M1, M2, M3, M4…) | `MangaApp-macOS-AppleSilicon` | `MangaApp.dmg` |
| Mac con **processore Intel** | `MangaApp-macOS-Intel` | `MangaApp.dmg` |
| **Windows** 10/11 | `MangaApp-Windows` | `MangaApp.exe` |
| **Linux** | `MangaApp-Linux` | `MangaApp` |

Viene scaricato un file `.zip` (circa 20-35 MB).

> **Che Mac ho?** Clicca la mela in alto a sinistra → **Informazioni su questo Mac**.
> Se alla voce *Chip* c'è "Apple M…" scegli **AppleSilicon**; se alla voce *Processore* c'è "Intel" scegli **Intel**.

> I file restano scaricabili per 90 giorni dalla build. Se una build è scaduta, prendine una più recente.

---

## Installazione su macOS

1. **Estrai lo zip.** Safari di solito lo fa da solo: nella cartella *Download* trovi direttamente `MangaApp.dmg`. Con Chrome o Firefox fai doppio clic sul file `.zip`.
2. **Apri `MangaApp.dmg`** con un doppio clic. Si apre una finestra con l'icona di MangaApp e la cartella Applicazioni.
3. **Trascina MangaApp sulla cartella Applicazioni.**
4. **Espelli il disco** "MangaApp" (tasto destro sull'icona nella Scrivania o nel Finder → *Espelli*). Ora puoi cancellare il `.dmg` e lo `.zip`.
5. **Apri l'app** da *Applicazioni*, Launchpad o Spotlight (Cmd+Spazio → "MangaApp").

### Primo avvio: "Apple non può verificare l'app"

È normale: l'app non è firmata con un account sviluppatore Apple a pagamento. Va autorizzata **una sola volta**.

**macOS 15 Sequoia, macOS 26 Tahoe e successivi**
1. Apri MangaApp: compare l'avviso, clicca **Fine**.
2. Apri **Impostazioni di Sistema → Privacy e sicurezza**.
3. Scorri in basso fino a *"MangaApp" è stata bloccata…* e clicca **Apri comunque**.
4. Inserisci la password del Mac e clicca di nuovo **Apri comunque**.

**macOS 14 Sonoma e precedenti**
1. In *Applicazioni* fai **tasto destro** (o Ctrl+clic) su MangaApp → **Apri**.
2. Nell'avviso clicca **Apri**.

Dalla volta successiva si apre normalmente con un doppio clic.

### Permesso per la cartella Download

La prima volta che salvi un PDF, macOS chiede se MangaApp può accedere alla cartella *Download*: clicca **Consenti**.

### Se macOS dice che l'app "è danneggiata"

Apri il **Terminale** (Cmd+Spazio → "Terminale"), incolla questo comando e premi Invio:
```bash
xattr -dr com.apple.quarantine /Applications/MangaApp.app
```
Poi riapri l'app.

---

## Installazione su Windows

1. Fai clic destro sullo zip → **Estrai tutto…**
2. Doppio clic su `MangaApp.exe` (puoi spostarlo dove vuoi, ad esempio sul Desktop).
3. Se compare *"Windows ha protetto il PC"* → **Ulteriori informazioni** → **Esegui comunque**.

---

## Installazione su Linux

```bash
unzip MangaApp-Linux.zip
chmod +x MangaApp
./MangaApp
```
Oppure doppio clic sul file, dopo aver abilitato *"Consenti l'esecuzione come programma"* nelle sue proprietà.

---

## Come si usa

1. Sul sito del manga apri il capitolo e copia il link della **pagina di lettura** (quella dove si vedono le tavole).
2. Incollalo nell'app: Cmd+V su Mac, Ctrl+V su Windows/Linux, oppure il pulsante **Incolla**.
3. Premi **Scarica PDF** (o Invio).

Fatto. Il PDF finisce in **Download/Manga** e prende il nome del capitolo dalla pagina. Alla fine puoi aprirlo subito con **Apri PDF** o vederlo con **Mostra nella cartella**.

| Cosa | Dove |
|---|---|
| Cambiare la cartella dei PDF | **Cambia…** in basso (l'app se la ricorda) |
| Tema chiaro / scuro | **Sistema / Chiaro / Scuro** in alto (anche questo viene ricordato) |
| Fermare un download | il pulsante diventa **Annulla** mentre scarica |
| Capire cosa è andato storto | **Mostra dettagli** |

---

## Aggiornare l'app

Scarica la nuova versione come descritto sopra e sostituisci quella vecchia:
- **macOS**: trascina la nuova MangaApp in *Applicazioni* e scegli **Sostituisci**. Potrebbe servire di nuovo l'autorizzazione del primo avvio.
- **Windows / Linux**: sostituisci il vecchio file con quello nuovo.

Impostazioni (cartella e tema) e PDF già scaricati restano dove sono.

---

## Problemi comuni

**"Nessuna tavola trovata"** — controlla che il link sia la pagina del capitolo e non la scheda del manga. Alcuni siti caricano le tavole con JavaScript o mostrano una tavola per pagina: cerca sul sito l'opzione "lettura verticale" / "tutte le pagine" e usa quel link.

**"Il sito è protetto da Cloudflare"** — quel sito blocca i download automatici: prova con un altro sito.

**Nella sezione Artifacts non vedo nulla** — la build è ancora in corso (attendi qualche minuto) oppure è fallita (❌): prendi la build verde precedente.

**Non riesco a scaricare gli Artifacts** — devi essere loggato su GitHub.

---

## Per sviluppatori

Avviare dal codice sorgente (Python 3.10+):
```bash
pip install -r requirements.txt
python3 MangaApp.py
```
Su macOS con il Python di Homebrew serve anche `brew install python-tk`.

Creare l'app per il sistema in uso (su macOS crea `dist/MangaApp.app`):
```bash
pip install pyinstaller
pyinstaller --noconfirm MangaApp.spec
```

Cambiare icona: `python3 tools/crea_icone.py nuova_icona.png` rigenera `icon.png`, `icon.icns` (macOS) e `icon.ico` (Windows).
L'icona attuale è stata creata da `tools/icona-sorgente.jpg` con `--box 609,154,1391,936` (solo il disegno, senza la cornice bianca).

Ogni push su un qualsiasi branch avvia la build su GitHub Actions per tutti i sistemi, con una prova di avvio dell'app.
