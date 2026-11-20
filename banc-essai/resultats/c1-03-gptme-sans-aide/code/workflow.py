"""Workflow d'extraction : lit un dossier de PDF, écrit un JSON par document.

Usage : python workflow.py {entree} {sortie}
"""
import json
import os
import re
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract  # noqa: E402

CLES = extract.CLES
NUM_KEYS = {"volume_dose_ml", "volume_nominal_ml", "tolerance_ml",
            "debit_ml_min", "pression_bar"}
DATE_KEYS = {"date_intervention", "date_validation"}


def to_number(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace('\u00a0', ' ').replace(' ', '')
    s = s.replace(',', '.')
    m = re.search(r'-?\d+(?:\.\d+)?', s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


def to_date(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s or set(s) <= {'_', '-', ' '}:
        return None
    m = re.search(r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})', s)
    if m:
        y, mo, d = m.groups()
        return f'{int(y):04d}-{int(mo):02d}-{int(d):02d}'
    m = re.search(r'(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})', s)
    if m:
        d, mo, y = m.groups()
        y = int(y)
        if y < 100:
            y += 2000
        return f'{y:04d}-{int(mo):02d}-{int(d):02d}'
    return None


def norm_txt(s):
    if s is None:
        return None
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', s).strip().lower()


def to_statut(v):
    n = norm_txt(v)
    if not n:
        return None
    if 'non' in n and 'conform' in n:
        return 'non_conforme'
    if 'revoir' in n or 'review' in n or 'follow' in n:
        return 'a_revoir'
    if 'conform' in n or 'compliant' in n or 'ok' in n:
        return 'conforme'
    return None


def clean_reference(v):
    if v is None:
        return None
    s = str(v).strip()
    s = re.sub(r'\s*[-,]?\s*(Rev(?:ision)?\.?|Indice|Ind\.?)\s*[A-Z]\b\.?\s*$', '', s, flags=re.I)
    return s.strip() or None


def postprocess(obj):
    out = {}
    for k in CLES:
        v = obj.get(k) if isinstance(obj, dict) else None
        if k in NUM_KEYS:
            out[k] = to_number(v)
        elif k in DATE_KEYS:
            out[k] = to_date(v)
        elif k == 'statut':
            out[k] = to_statut(v)
        elif k == 'reference_rapport':
            out[k] = clean_reference(v)
        else:
            if v is None:
                out[k] = None
            else:
                s = str(v).strip()
                out[k] = s if s and s.lower() not in {'null', 'none', 'n/a', '—', '-'} else None
    return out


def process(pdf_path):
    try:
        obj = extract.extract(str(pdf_path))
    except Exception:
        obj = None
    return pdf_path, postprocess(obj)


def main():
    if len(sys.argv) < 3:
        print('usage: workflow.py {entree} {sortie}', file=sys.stderr)
        return 2
    entree = Path(sys.argv[1])
    sortie = Path(sys.argv[2])
    sortie.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(entree.glob('*.pdf'))
    if not pdfs:
        print(f'aucun PDF dans {entree}', file=sys.stderr)
        return 1
    workers = min(6, max(1, len(pdfs)))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for pdf_path, obj in ex.map(process, pdfs):
            (sortie / (pdf_path.stem + '.json')).write_text(
                json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f'{pdf_path.name} -> {pdf_path.stem}.json', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
