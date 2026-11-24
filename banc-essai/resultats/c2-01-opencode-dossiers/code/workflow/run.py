#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from extraction import extract_piece
from consolidation import consolidate


def dossiers_de(entree: Path) -> list[Path]:
    def pdfs(d):
        return sorted(list(d.glob("*.pdf")) + list(d.glob("*.PDF")))
    subs = sorted([p for p in entree.iterdir() if p.is_dir() and pdfs(p)])
    if subs:
        return subs
    if pdfs(entree):
        return [entree]
    return []


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: run.py {entree} {sortie}", file=sys.stderr)
        return 2
    entree = Path(sys.argv[1])
    sortie = Path(sys.argv[2])
    sortie.mkdir(parents=True, exist_ok=True)

    dossiers = dossiers_de(entree)
    if not dossiers:
        print(f"aucun dossier PDF trouvé dans {entree}", file=sys.stderr)
        return 1

    taches = []
    for d in dossiers:
        for pdf in sorted(list(d.glob("*.pdf")) + list(d.glob("*.PDF"))):
            taches.append((d.name, pdf))

    resultats: dict[str, list[dict]] = {d.name: [] for d in dossiers}
    echecs = 0
    workers = min(6, max(1, len(taches)))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futurs = {ex.submit(extract_piece, str(pdf)): (nom, pdf) for nom, pdf in taches}
        for fut in as_completed(futurs):
            nom, pdf = futurs[fut]
            try:
                obj = fut.result()
                resultats[nom].append(obj)
            except Exception:
                echecs += 1
                print(f"échec d'extraction : {pdf}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)

    for nom, pieces in resultats.items():
        try:
            sortie_json = consolidate(pieces)
        except Exception:
            print(f"échec de consolidation : {nom}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            echecs += 1
            continue
        with open(sortie / f"{nom}.json", "w", encoding="utf-8") as f:
            json.dump(sortie_json, f, ensure_ascii=False, indent=2)

    print(f"{len(dossiers)} dossiers traités, {len(taches)} pièces, {echecs} échec(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
