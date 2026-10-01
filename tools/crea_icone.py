"""Genera icon.png, icon.ico e icon.icns a partire da un'immagine qualsiasi.

Uso:  python tools/crea_icone.py immagine_sorgente.png [--rientro 0.03] [--box x0,y0,x1,y1]

- Se l'immagine è una "piastrella" con angoli arrotondati su uno sfondo
  (tipico delle immagini generate), la piastrella viene ritagliata da sola.
- La piastrella viene rimessa in una forma "squircle" con angoli trasparenti,
  centrata con i margini e l'ombra previsti da macOS (824 px su 1024).
"""

import argparse
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat

RADICE = Path(__file__).resolve().parent.parent
TELA = 1024
CORPO = 824  # griglia icone macOS: 100 px di margine per lato
SS = 4  # sovracampionamento per bordi morbidi


def _squircle(lato, esponente=5.0):
    """Maschera a superellisse, la forma delle icone di macOS."""
    grande = lato * SS
    maschera = Image.new("L", (grande, grande), 0)
    r = grande / 2
    punti = []
    passi = 720
    for i in range(passi):
        t = 2 * math.pi * i / passi
        c, s = math.cos(t), math.sin(t)
        x = r + r * math.copysign(abs(c) ** (2 / esponente), c)
        y = r + r * math.copysign(abs(s) ** (2 / esponente), s)
        punti.append((x, y))
    ImageDraw.Draw(maschera).polygon(punti, fill=255)
    return maschera.resize((lato, lato), Image.LANCZOS)


def _ritaglia_piastrella(img):
    """Trova la piastrella su uno sfondo uniforme guardando il colore degli angoli."""
    rgb = img.convert("RGB")
    w, h = rgb.size
    campione = max(4, min(w, h) // 50)
    angoli = [rgb.crop(b) for b in ((0, 0, campione, campione), (w - campione, 0, w, campione),
                                    (0, h - campione, campione, h), (w - campione, h - campione, w, h))]
    sfondo = tuple(int(sum(ImageStat.Stat(a).mean[i] for a in angoli) / 4) for i in range(3))
    diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, sfondo)).convert("L")
    # Soglia alta abbastanza da ignorare l'ombra morbida attorno alla piastrella
    maschera = diff.point(lambda v: 255 if v > 18 else 0).filter(ImageFilter.MedianFilter(5))
    box = maschera.getbbox()
    if not box:
        return rgb
    x0, y0, x1, y1 = box
    # Rende quadrato attorno al centro
    lato = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    box = (int(cx - lato / 2), int(cy - lato / 2), int(cx + lato / 2), int(cy + lato / 2))
    return rgb.crop(box)


def crea(sorgente, rientro=0.0, box=None):
    img = Image.open(sorgente)
    img.load()
    if box:
        piastrella = img.convert("RGB").crop(box)
    elif img.mode == "RGBA" and img.getchannel("A").getextrema()[0] < 255:
        piastrella = img.crop(img.getchannel("A").getbbox())
    else:
        piastrella = _ritaglia_piastrella(img)
    if rientro:
        # Toglie una cornice (es. il bordo bianco) prima di applicare la forma
        l = piastrella.width
        m = int(l * rientro)
        piastrella = piastrella.crop((m, m, l - m, l - m))
    piastrella = piastrella.convert("RGBA").resize((CORPO, CORPO), Image.LANCZOS)
    maschera = _squircle(CORPO)
    piastrella.putalpha(maschera)

    # Ombra leggera sotto la piastrella, come le icone di sistema
    ombra = Image.new("RGBA", (TELA, TELA), (0, 0, 0, 0))
    alfa_ombra = Image.new("L", (TELA, TELA), 0)
    alfa_ombra.paste(maschera.point(lambda v: v * 0.35), (100, 112))
    ombra.putalpha(alfa_ombra.filter(ImageFilter.GaussianBlur(14)))
    icona = Image.alpha_composite(ombra, Image.new("RGBA", (TELA, TELA)))
    icona.alpha_composite(piastrella, (100, 100))

    icona.save(RADICE / "icon.png", optimize=True)
    icona.save(RADICE / "icon.icns")
    # Su Windows le icone piccole rendono meglio senza margini e senza ombra
    piastrella.save(RADICE / "icon.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    print("Create: icon.png, icon.icns, icon.ico")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sorgente")
    parser.add_argument("--rientro", type=float, default=0.0,
                        help="frazione di bordo da togliere (es. 0.03 per una cornice bianca)")
    parser.add_argument("--box", help="ritaglio manuale della piastrella: x0,y0,x1,y1")
    args = parser.parse_args()
    crea(args.sorgente, args.rientro, tuple(map(int, args.box.split(","))) if args.box else None)
