"""Compresse les traces trop lourdes d'un essai avant commit (limite GitHub : 100 Mo par fichier).

    python3 banc-essai/cage/compresser.py banc-essai/resultats/<essai> [seuil en Mo, 20 par défaut]

Tout fichier .log, .txt ou .jsonl de plus de <seuil> Mo est remplacé par sa version gzip (même nom
+ .gz) ; une trace d'événements JSON se comprime d'un facteur 10 à 30. Lecture : `zcat fichier.gz`.
"""
import gzip
import shutil
import sys
from pathlib import Path

dossier = Path(sys.argv[1])
seuil = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0
for f in sorted(dossier.rglob("*")):
    if f.is_file() and f.suffix in (".log", ".txt", ".jsonl") and f.stat().st_size > seuil * 1024 * 1024:
        gz = f.with_name(f.name + ".gz")
        with open(f, "rb") as src, gzip.open(gz, "wb", compresslevel=9) as dst:
            shutil.copyfileobj(src, dst)
        avant, apres = f.stat().st_size, gz.stat().st_size
        f.unlink()
        print(f"{f} : {avant / 1e6:.1f} Mo -> {apres / 1e6:.1f} Mo (gzip)")
        if apres > 90 * 1024 * 1024:   # toujours trop lourd pour GitHub : gardé hors git, signalé
            hors = dossier / "hors-git"
            hors.mkdir(exist_ok=True)
            gz.rename(hors / gz.name)
            (f.parent / (f.name + ".HORS-GIT.txt")).write_text(
                f"Trace de {apres / 1e6:.0f} Mo après compression, trop lourde pour GitHub : gardée sur la machine "
                f"d'essai dans {hors.name}/{gz.name}.\n")
            print(f"  -> hors git : {hors / gz.name}")
