"""Construit kit-harnais-securise.zip à partir du dossier du kit (sans .env, espace, journaux ni cache).

    python3 livrables/construire-zip.py
"""
import zipfile
from pathlib import Path

ICI = Path(__file__).resolve().parent
KIT = ICI / "kit-harnais-securise"
INTERDITS = {".env", "__pycache__"}
with zipfile.ZipFile(ICI / "kit-harnais-securise.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(KIT.rglob("*")):
        rel = f.relative_to(KIT)
        if f.is_dir() or INTERDITS & set(rel.parts):
            continue
        if rel.parts[0] in ("espace", "journaux", "certificats") and f.name != ".gitkeep":
            continue
        info = zipfile.ZipInfo(f"kit-harnais-securise/{rel.as_posix()}", date_time=(2026, 11, 20, 0, 0, 0))
        info.external_attr = (0o755 if f.stat().st_mode & 0o111 else 0o644) << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, f.read_bytes())
        print(rel)
