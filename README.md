# 🏴‍☠️ Manga Downloader

Incolla il link di un capitolo manga, premi **Scarica PDF**: l'app trova le tavole, le scarica e ti dà il PDF pronto.

---

## Download

Vai alla pagina [**Actions**](https://github.com/FrancescoRiccio4522/MangaApp/actions) → ultima build riuscita → sezione **Artifacts**:

| Sistema | File da scaricare |
|---|---|
| **macOS** (chip Apple M1/M2/M3/M4) | `MangaApp-macOS-AppleSilicon` → `MangaApp.dmg` |
| **macOS** (processore Intel) | `MangaApp-macOS-Intel` → `MangaApp.dmg` |
| **Windows** | `MangaApp-Windows` → `MangaApp.exe` |
| **Linux** | `MangaApp-Linux` → `MangaApp` |

Non sai che Mac hai? Menu Apple (la mela in alto a sinistra) → **Informazioni su questo Mac**: se c'è scritto "Chip Apple M…" prendi *AppleSilicon*, se c'è "Processore Intel" prendi *Intel*.

---

## Installazione

### macOS
1. Scarica lo zip giusto per il tuo Mac ed estrailo: dentro c'è `MangaApp.dmg`
2. Apri `MangaApp.dmg` e trascina **MangaApp** nella cartella **Applicazioni**
3. Apri MangaApp da Applicazioni (o da Launchpad / Spotlight)
4. Al primo avvio macOS dirà che l'app non è verificata (non è firmata con un account sviluppatore Apple):
   - **macOS 15 Sequoia e successivi**: chiudi l'avviso, vai in **Impostazioni di Sistema → Privacy e Sicurezza**, scorri in basso e clicca **Apri comunque**
   - **macOS 14 e precedenti**: tasto destro (o Ctrl+clic) su MangaApp → **Apri** → **Apri**
5. La prima volta che salvi un PDF, macOS chiede il permesso per la cartella Download: clicca **Consenti**

Se macOS dice che l'app "è danneggiata", apri il Terminale ed esegui:
```bash
xattr -dr com.apple.quarantine /Applications/MangaApp.app
```

### Windows
1. Scarica ed estrai `MangaApp-Windows`
2. Doppio click su `MangaApp.exe`
3. Se Windows mostra "PC protetto" → **Ulteriori informazioni** → **Esegui comunque**

### Linux
1. Scarica ed estrai `MangaApp-Linux`
2. Nel terminale:
   ```bash
   chmod +x MangaApp
   ./MangaApp
   ```

---

## Utilizzo

1. Copia il link della **pagina di lettura** del capitolo (quella dove si vedono le tavole)
2. Incollalo nell'app (Cmd+V / Ctrl+V, oppure il pulsante **Incolla**)
3. Premi **Scarica PDF** (o Invio)

Fatto: il PDF finisce in `Download/Manga`, con il nome del capitolo preso dalla pagina. Al termine puoi aprirlo subito con **Apri PDF** o vederlo con **Mostra nella cartella**.

- **Cambia…** in basso sceglie un'altra cartella (l'app se la ricorda)
- **Sistema / Chiaro / Scuro** in alto cambia il tema (anche questo viene ricordato)
- **Mostra dettagli** fa vedere cosa sta facendo l'app, utile se qualcosa va storto
- Durante il download il pulsante diventa **Annulla**

---

## Problemi comuni

**"Nessuna tavola trovata"** — controlla che il link sia la pagina del capitolo e non la scheda del manga. Alcuni siti caricano le tavole con JavaScript o mostrano una tavola per pagina: in quel caso cerca l'opzione "lettura verticale / tutte le pagine" sul sito e usa quel link.

**"Il sito è protetto da Cloudflare"** — quel sito blocca i download automatici: prova un altro sito.

---

## Per sviluppatori

Avviare dal codice sorgente (Python 3.10+):
```bash
pip install -r requirements.txt
python3 MangaApp.py
```
Su macOS con Python di Homebrew serve anche `brew install python-tk`.

Creare l'eseguibile per il sistema in uso:
```bash
pip install pyinstaller
pyinstaller --noconfirm MangaApp.spec
```

Cambiare icona: `python3 tools/crea_icone.py nuova_icona.png` rigenera `icon.png`, `icon.icns` (macOS) e `icon.ico` (Windows).
