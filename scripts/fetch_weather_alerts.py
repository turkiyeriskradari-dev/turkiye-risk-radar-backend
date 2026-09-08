"""
Meteorolojik erken uyari verisi: MGM MeteoUyari sistemi.

DURUM: TASLAK / TAMAMLANMAMIS
MGM'in il bazli renkli uyari haritasi (sel, firtina, dolu, cig, don,
toz tasinimi vb.) resmi bir API olarak yayinlanmiyor; mgm.gov.tr
uzerindeki "Meteorolojik Uyari" sayfasindan alinmasi gerekiyor.

YAPILACAKLAR (air_quality.py ile ayni yontem):
1. mgm.gov.tr uzerindeki uyari haritasi sayfasini tarayicida F12 ile incele,
   arka planda cagirilan JSON uc noktasini bul
2. Bulunursa dogrudan kullan; bulunamazsa BeautifulSoup ile HTML parse et

Uyari tipleri (il bazli, renk kodlu):
- Sel/Taskin, Firtina, Dolu, Yildirim, Cig, Buzlanma/Don, Toz Tasinimi,
  Kar Erimesi, Zirai Don, Sicak Hava, Soguk Hava, Sis

Bu yapinin hedef ciktisi (Android tarafinda il bazli renkli overlay icin):
{
  "province": "Istanbul",
  "alerts": [
    {"type": "Firtina", "level": "Turuncu", "valid_until": "2026-09-09T18:00:00"}
  ]
}
"""
import requests
from utils import save_json, save_error_fallback

SOURCE_NAME = "MGM MeteoUyari"
OUTPUT_FILE = "weather_alerts.json"

# TODO: Gercek endpoint tespit edildiginde buraya yazilacak
API_URL = "https://www.mgm.gov.tr/FTPDATA/uyari/uyari.json"  # DOGRULANMADI - TAHMINI


def normalize_record(raw):
    """TODO: Gercek veri yapisi netlesince guncellenecek."""
    return raw


def fetch():
    try:
        resp = requests.get(API_URL, timeout=20)
        resp.raise_for_status()
        raw_data = resp.json()

        normalized = [normalize_record(r) for r in raw_data]
        save_json(OUTPUT_FILE, normalized, SOURCE_NAME)

    except Exception as e:
        save_error_fallback(OUTPUT_FILE, SOURCE_NAME,
                             f"Endpoint henuz dogrulanmadi / degisti: {e}")


if __name__ == "__main__":
    fetch()
