import os
from PIL import Image

def crea_pdf_da_cartella():
    # 1. Chiediamo il percorso
    percorso = input("Inserisci il percorso della cartella con le tavole: ").strip()
    percorso = percorso.strip("'\"")

    if not os.path.exists(percorso):
        print("Errore: La cartella non esiste. Controlla il percorso.")
        return

    # 2. Cerchiamo e ordiniamo i file
    file_nella_cartella = os.listdir(percorso)
    immagini_file = [f for f in file_nella_cartella if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    immagini_file.sort()

    if not immagini_file:
        print("Nessuna immagine trovata in questa cartella.")
        return

    # Estraiamo il nome della cartella per dare il nome al PDF
    nome_cartella = os.path.basename(os.path.normpath(percorso))
    if not nome_cartella: # Fallback di sicurezza
        nome_cartella = "Manga"

    print(f"\nTrovate {len(immagini_file)} tavole in '{percorso}'.")
    print(f"Creazione del file '{nome_cartella}.pdf' in corso...")
    
    immagini_da_unire = []
    prima_immagine = None

    # 3. Apriamo le immagini con Pillow (che ignora le finte estensioni)
    for img_nome in immagini_file:
        percorso_completo = os.path.join(percorso, img_nome)
        try:
            # Apriamo l'immagine e forziamo i colori in RGB (obbligatorio per i PDF)
            img = Image.open(percorso_completo).convert('RGB')
            
            if prima_immagine is None:
                prima_immagine = img
            else:
                immagini_da_unire.append(img)
        except Exception as e:
            print(f"⚠️ Impossibile elaborare '{img_nome}': {e}")

    if prima_immagine is None:
        print("❌ Impossibile creare il PDF: nessuna immagine valida è stata letta.")
        return

    # 4. Salviamo tutto in un unico PDF col nome della cartella
    nome_pdf = os.path.join(percorso, f"{nome_cartella}.pdf")
    
    try:
        prima_immagine.save(
            nome_pdf,
            save_all=True,
            append_images=immagini_da_unire
        )
        print(f"\n✅ Successo! Il PDF è pronto a prova di bomba.")
        print(f"Lo trovi qui: {nome_pdf}")
    except Exception as e:
        print(f"\n❌ Errore durante il salvataggio finale del PDF: {e}")

# Avvia lo script
if __name__ == "__main__":
    crea_pdf_da_cartella()