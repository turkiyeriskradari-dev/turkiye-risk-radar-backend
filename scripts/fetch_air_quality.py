"""
Hava kalitesi verisi: Ulusal Hava Kalitesi Izleme Agi (UHKIA).

DURUM: TASLAK / TAMAMLANMAMIS
Bu kaynagin resmi, dokumante edilmis bir API'si yok. Veri
havaizleme.gov.tr / sim.csb.gov.tr uzerinden web sayfasi icinde sunuluyor.
Once tarayici Gelistirici Araclari (F12 > Network sekmesi) ile sitenin
kendi ic API cagrilarini (network isteklerini) tespit etmemiz gerekiyor -
bircok kamu sitesi, sayfayi render etmek icin arka planda kendi JSON
uc noktalarini cagiriyor; bunu bulursak scraping yerine dogrudan o
uc noktayi kullanabiliriz (daha stabil olur).

YAPILACAKLAR (bir sonraki adimda birlikte yapacagiz):
1. havaizleme.gov.tr adresini tarayicida acip F12 > Network sekmesinde
   "XHR/Fetch" filtresiyle sayfa yuklenirken hangi istekler atiliyor incele
2. Eger JSON donen bir ic API bulunursa, asagidaki fetch() fonksiyonunu
   o uc noktaya gore guncelle
3. Bulunamazsa, BeautifulSoup ile HTML tablosunu parse eden bir alternatif
   yazariz (requirements.txt'de bs4 zaten hazir)

Asagidaki kod, YAPI ISKELETI olarak hazir - gercek endpoint netlesince
sadece API_URL ve normalize_record() fonksiyonunu guncellememiz yeterli
olacak, geri kalan (kaydetme, hata yonetimi) hazir.
"""
import requests
from utils import save_json, save_error_fallback

SOURCE_NAME = "Ulusal Hava Kaliteci Izleme Agi (UHKIA)"
OUTPUT_FILE = "air_quality.json"

# TODO: Gercek endpoint tespit edildiginde buraya yazilacak
API_URL = "https://www.havaizleme.gov.tr/Services/HaIstasyon"  # DOGRULANMADI


def normalize_record(raw):
    """
    TODO: Gercek API/HTML yapisi netlesince bu fonksiyon guncellenecek.
    Hedef format (diger katmanlarla tutarli olacak sekilde):
    {
        "station_name": "Kadikoy",
        "province": "Istanbul",
        "aqi": 87,
        "aqi_category": "Orta",
        "pm10": 45.2,
        "pm2_5": 22.1,
        "latitude": 40.98,
        "longitude": 29.03,
        "measured_at": "2026-09-08T10:00:00"
    }
    """
    return raw  # placeholder - dogrudan gecirir


def fetch():
    try:
        resp = requests.get(API_URL, timeout=20)
        resp.raise_for_status()
        raw_data = resp.json()  # endpoint netlesince format degisebilir

        normalized = [normalize_record(r) for r in raw_data]
        save_json(OUTPUT_FILE, normalized, SOURCE_NAME)

    except Exception as e:
        save_error_fallback(OUTPUT_FILE, SOURCE_NAME,
                             f"Endpoint henuz dogrulanmadi / degisti: {e}")


if __name__ == "__main__":
    fetch()
