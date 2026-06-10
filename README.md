# 🏴‍☠️ Manga Downloader & PDF Creator

Scarica capitoli manga da internet e convertili in PDF con un click.

---

## Download

Vai alla pagina [**Actions**](https://github.com/FrancescoRiccio4522/MangaApp/actions) → ultima build → sezione **Artifacts**:

| Sistema | File da scaricare |
|---|---|
| **Windows** | `MangaApp-Windows.zip` → estrai → `MangaApp.exe` |
| **Linux** | `MangaApp-Linux.zip` → estrai → `MangaApp` |
| **macOS** | `MangaApp-macOS.zip` → estrai → `MangaApp` |

---

## Installazione

### Windows
1. Scarica `MangaApp-Windows.zip` dalla sezione **Actions → ultima build → Artifacts**
2. Estrai lo zip
3. Doppio click su `MangaApp.exe`
4. Se Windows mostra avviso "PC protetto" → clicca **Ulteriori informazioni** → **Esegui comunque**

### Linux
1. Scarica `MangaApp-Linux.zip`
2. Estrai lo zip
3. Apri terminale nella cartella ed esegui:
   ```bash
   chmod +x MangaApp
   ./MangaApp
   ```
   Oppure doppio click sul file (potrebbe richiedere di abilitare "Esegui come programma" nelle proprietà)

### macOS
1. Scarica `MangaApp-macOS.zip`
2. Estrai lo zip
3. Apri terminale nella cartella ed esegui:
   ```bash
   chmod +x MangaApp
   ./MangaApp
   ```
   Se macOS blocca l'app ("sviluppatore non verificato") → **Impostazioni di Sistema → Privacy e Sicurezza → Apri comunque**

---

## Utilizzo

### Scaricare un capitolo
1. Apri l'app
2. Incolla il **link della pagina del capitolo** nel campo "Link capitolo"
3. Clicca **Sfoglia** per scegliere dove salvare (oppure scrivi il percorso a mano)
4. Scrivi il nome della cartella (es. `Cap100`)
5. Clicca **📥 Solo Download**

### Creare un PDF da tavole già scaricate
1. Nel campo "Cartella" inserisci il percorso della cartella con le immagini
2. Nel campo "Nome capitolo" scrivi il titolo del PDF
3. Clicca **📄 Solo PDF**

### Scaricare e creare PDF in una volta sola
1. Compila link, cartella e nome
2. Clicca **🚀 Fai Tutto!**

Il log in basso mostra lo stato in tempo reale. Al termine trovi il PDF dentro la cartella del capitolo.

---

## Requisiti

Nessuno — l'app è un file singolo che include tutto il necessario.

---

## Problemi comuni

**"Nessuna tavola trovata"** — il sito potrebbe bloccare i download automatici. Prova con un link diverso o un altro sito.

**L'app non si apre su Linux** — assicurati di aver dato i permessi di esecuzione con `chmod +x MangaApp`.
