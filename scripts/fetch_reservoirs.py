"""
Baraj doluluk orani verisi: Istanbul icin ISKI, diger sehirler icin
ilgili su idareleri (ASKI, IZSU, BUSKI vb.).

DURUM: TASLAK / TAMAMLANMAMIS - V1'de yalnizca ISKI (Istanbul) kapsanacak.

YAPILACAKLAR:
1. iski.istanbul adresindeki "baraj doluluk oranlari" sayfasini incele
2. F12 > Network ile JSON uc nokta ara; yoksa HTML tablo parse et
3. V2'de ASKI/IZSU/BUSKI ayni yapiya eklenebilir (province alani ile
   ayni "reservoirs.json" icinde birden fazla sehir barindirilabilir)

Hedef format:
{
  "province": "Istanbul",
  "reservoir_name": "Omerli Barji",
  "fill_percentage": 62.4,
  "measured_at": "2026-09-08"
}
"""
import requests
from utils import save_json, save_error_fallback

SOURCE_NAME = "ISKI Baraj Doluluk Oranlari"
OUTPUT_FILE = "reservoirs.json"

# TODO: Gercek endpoint tespit edildiginde buraya yazilacak
API_URL = "https://www.iski.istanbul/web/tr-TR/baraj-doluluk-oranlari"  # DOGRULANMADI - HTML SAYFASI


def normalize_record(raw):
    """TODO: Gercek veri yapisi netlesince guncellenecek."""
    return raw


def fetch():
    try:
        resp = requests.get(API_URL, timeout=20)
        resp.raise_for_status()
        # NOT: Bu muhtemelen JSON degil HTML donecek - BeautifulSoup ile
        # parse edilmesi gerekecek. Simdilik iskelet olarak birakildi.
        raw_data = []  # TODO: HTML parse sonrasi doldurulacak

        normalized = [normalize_record(r) for r in raw_data]
        save_json(OUTPUT_FILE, normalized, SOURCE_NAME)

    except Exception as e:
        save_error_fallback(OUTPUT_FILE, SOURCE_NAME,
                             f"Endpoint/parse henuz tamamlanmadi: {e}")


if __name__ == "__main__":
    fetch()
