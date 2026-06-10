import os
import requests
from bs4 import BeautifulSoup

def scarica_manga():
    # 1. Chiediamo il link all'utente direttamente dal terminale
    url = input("Inserisci il link del capitolo: ").strip()
    
    if not url:
        print("Nessun link inserito. Uscita.")
        return

    # 2. Chiediamo come chiamare la cartella di salvataggio
    nome_cartella = input("Inserisci il nome della cartella dove salvare le tavole (es. Cap_1080): ").strip()
    
    # Se l'utente preme invio senza scrivere nulla, usiamo un nome di default
    if not nome_cartella:
        nome_cartella = "Tavole_Manga"

    # Creiamo la cartella
    os.makedirs(nome_cartella, exist_ok=True)
    
    print("\nConnessione alla pagina in corso...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": url
    }
    
    try:
        risposta = requests.get(url, headers=headers)
    except Exception as e:
        print(f"Errore di connessione: {e}")
        return
        
    if risposta.status_code != 200:
        print(f"Errore di connessione alla pagina: {risposta.status_code}")
        return
        
    soup = BeautifulSoup(risposta.text, "html.parser")
    immagini = soup.find_all("img")
    contatore = 1
    
    print("\nInizio download delle tavole...")
    for img in immagini:
        src = img.get("data-src") or img.get("src")
        
        if src and ("manga" in src or "cdn" in src) and not src.endswith(".gif"):
            try:
                img_risposta = requests.get(src, headers=headers)
                
                if img_risposta.status_code == 200:
                    # Cerchiamo di mantenere l'estensione originale se presente nel link
                    estensione = ".jpg"
                    if ".png" in src:
                        estensione = ".png"
                    elif ".webp" in src:
                        estensione = ".webp"
                        
                    nome_file = os.path.join(nome_cartella, f"{contatore:03d}{estensione}")
                    
                    with open(nome_file, "wb") as file_immagine:
                        file_immagine.write(img_risposta.content)
                        
                    print(f"Salvata tavola {contatore:02d}")
                    contatore += 1
                else:
                    print(f"Immagine ignorata (Errore server {img_risposta.status_code})")
            except Exception as e:
                print(f"Errore scaricando una tavola: {e}")

    print(f"\nFinito! Hai scaricato {contatore - 1} tavole nella cartella '{nome_cartella}'.")

# Avvia lo script
if __name__ == "__main__":
    scarica_manga()