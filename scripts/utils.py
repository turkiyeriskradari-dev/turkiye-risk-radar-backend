"""
Tum fetch_*.py scriptlerinin ortak kullandigi yardimci fonksiyonlar.
"""
import json
import os
from datetime import datetime, timezone

# Bu dosyanin bulundugu yerden bir ust dizindeki 'data' klasoru
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def utc_now_iso():
    """Su anki zamani ISO 8601 formatinda dondurur (UTC)."""
    return datetime.now(timezone.utc).isoformat()


def save_json(filename, records, source_name, extra_meta=None):
    """
    Cekilen veriyi standart bir zarf (envelope) icinde data/ klasorune yazar.

    Standart format (tum kaynaklar icin ayni sekilde):
    {
        "source": "AFAD/Kandilli",
        "last_updated": "2026-09-08T12:00:00+00:00",
        "record_count": 12,
        "data": [ ... ]
    }

    Boylece Android tarafi her katman icin ayni sekilde
    "last_updated" ve "data" alanlarini okuyabilir.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    payload = {
        "source": source_name,
        "last_updated": utc_now_iso(),
        "record_count": len(records),
        "data": records,
    }
    if extra_meta:
        payload["meta"] = extra_meta

    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[OK] {filename} yazildi -> {len(records)} kayit ({source_name})")
    return filepath


def save_error_fallback(filename, source_name, error_message):
    """
    Veri cekme basarisiz olursa, eski dosyayi SILMEDEN sadece bir hata
    logu tutar. Boylece uygulama en son basarili veriyi gostermeye devam eder
    ("veri yok" hatasi yerine "eski ama var olan veri" tercih edilir).
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    log_path = os.path.join(DATA_DIR, "_fetch_errors.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{utc_now_iso()} | {source_name} | HATA: {error_message}\n")
    print(f"[HATA] {source_name}: {error_message} (eski veri korunuyor)")
