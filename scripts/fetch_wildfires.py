"""
Orman yangini / sicak nokta verisi: NASA FIRMS (Fire Information for Resource
Management System) resmi API'si.

KURULUM GEREKLI:
1. https://firms.modis.gov/api/area/ adresinden ucretsiz bir MAP_KEY alin
   (NASA Earthdata hesabi ile kayit gerekiyor, tamamen ucretsiz).
2. Bu anahtari GitHub reposunda "Settings > Secrets and variables > Actions"
   kismina FIRMS_MAP_KEY adiyla ekleyin.
3. GitHub Actions workflow'u bu secret'i ortam degiskeni olarak scripte gecirir.

Kaynak: https://firms.modis.gov/api/area/csv/{MAP_KEY}/{SENSOR}/{AREA}/{DAY_RANGE}
"""
import csv
import io
import os
import requests
from utils import save_json, save_error_fallback

SOURCE_NAME = "NASA FIRMS (VIIRS_SNPP_NRT)"
OUTPUT_FILE = "wildfires.json"

MAP_KEY = os.environ.get("FIRMS_MAP_KEY", "")

# Turkiye'yi kapsayan bounding box: min_lon,min_lat,max_lon,max_lat
TR_AREA = "25,34,45,43"

# Son kac gunun verisi cekilsin (FIRMS max 10 gune kadar destekliyor)
DAY_RANGE = 1

API_URL = f"https://firms.modis.gov/api/area/csv/{MAP_KEY}/VIIRS_SNPP_NRT/{TR_AREA}/{DAY_RANGE}"

# Guven skoru bu esigin altindaki noktalari (duman/bulut kaynakli yanlis
# pozitifleri elemek icin) filtreden geciriyoruz. FIRMS confidence alani
# genelde "l" (low) / "n" (nominal) / "h" (high) ya da 0-100 sayisal olabilir.
MIN_CONFIDENCE_NUMERIC = 30


def normalize_row(row):
    try:
        confidence_raw = row.get("confidence", "")
        return {
            "latitude": float(row.get("latitude")),
            "longitude": float(row.get("longitude")),
            "brightness": float(row.get("bright_ti4", row.get("brightness", 0)) or 0),
            "confidence": confidence_raw,
            "acquired_date": row.get("acq_date"),
            "acquired_time": row.get("acq_time"),
            "satellite": row.get("satellite"),
            "daynight": row.get("daynight"),
        }
    except Exception:
        return None


def passes_confidence_filter(record):
    c = record.get("confidence")
    # Harf tabanli guven skoru: sadece 'n' (nominal) ve 'h' (high) kabul et
    if isinstance(c, str) and c.isalpha():
        return c.lower() in ("n", "h")
    # Sayisal guven skoru
    try:
        return float(c) >= MIN_CONFIDENCE_NUMERIC
    except (TypeError, ValueError):
        return True  # emin degilsek eleme, goster


def fetch():
    if not MAP_KEY:
        save_error_fallback(OUTPUT_FILE, SOURCE_NAME,
                             "FIRMS_MAP_KEY ortam degiskeni tanimli degil.")
        return

    try:
        resp = requests.get(API_URL, timeout=30)
        resp.raise_for_status()

        csv_reader = csv.DictReader(io.StringIO(resp.text))
        normalized = [normalize_row(r) for r in csv_reader]
        normalized = [r for r in normalized if r]
        normalized = [r for r in normalized if passes_confidence_filter(r)]

        save_json(OUTPUT_FILE, normalized, SOURCE_NAME,
                  extra_meta={"day_range": DAY_RANGE, "area_bbox": TR_AREA})

    except Exception as e:
        save_error_fallback(OUTPUT_FILE, SOURCE_NAME, str(e))


if __name__ == "__main__":
    fetch()
