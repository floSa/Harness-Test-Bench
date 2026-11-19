"""Masque toute chaîne qui ressemble à une clé dans les résultats d'un essai, avant tout commit.

    python3 banc-essai/cage/masquer.py banc-essai/resultats/<essai> [...]

Un harnais peut afficher ses variables d'environnement (dont la clé de l'essai) dans sa trace ;
la clé est supprimée du relais à la fin de l'essai, mais aucune clé ne doit figurer dans un fichier
suivi par git. Remplace « sk-… » (20 caractères ou plus) par « sk-*** » dans tous les fichiers texte
du dossier ; affiche le nombre de remplacements par fichier.
"""
import re
import sys
from pathlib import Path

CLE = re.compile(rb"sk-[A-Za-z0-9_\-]{20,}")
total = 0
for dossier in sys.argv[1:]:
    for f in Path(dossier).rglob("*"):
        if not f.is_file() or f.stat().st_size > 200 * 1024 * 1024:
            continue
        octets = f.read_bytes()
        if b"\0" in octets[:4096]:
            continue
        nouveau, n = CLE.subn(b"sk-***", octets)
        if n:
            f.write_bytes(nouveau)
            total += n
            print(f"{f} : {n} clé(s) masquée(s)")
print(f"masquage : {total} remplacement(s)")
