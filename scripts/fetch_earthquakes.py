"""
Deprem verisi: Kandilli Rasathanesi verisini acik/ucretsiz sekilde JSON olarak
sunan topluluk API'sini kullanir (api.orhanaydogdu.com.tr).

NOT: Bu resmi bir Kandilli/AFAD API'si degildir, gonullu bir gelistirici
tarafindan Kandilli verisini duzenli cekip JSON'a cevirerek sundugu bir
"wrapper" servistir. Turkiye'de deprem uygulamasi gelistiren pek cok kisi
tarafindan yaygin kullanilir. Ileride bu servis calismaz hale gelirse
AFAD'in kendi "deprem sorgulama" sayfasindan scraping yapan alternatif bir
fonksiyon yazip bunun yerine koyabiliriz.

Kaynak: https://api.orhanaydogdu.com.tr/deprem/kandilli/live
"""
import requests
from utils import save_json, save_error_fallback

SOURCE_NAME = "Kandilli Rasathanesi (api.orhanaydogdu.com.tr uzerinden)"
API_URL = "https://api.orhanaydogdu.com.tr/deprem/kandilli/live?limit=100"
OUTPUT_FILE = "earthquakes.json"

# Turkiye ve yakin cevresini kapsayan kaba bir bounding box.
# Kaynagin zaten cogunlukla Turkiye/civarini dondurdugunu varsayiyoruz,
# yine de guvenlik icin filtreliyoruz.
TR_BBOX = {"min_lat": 34.0, "max_lat": 43.0, "min_lon": 25.0, "max_lon": 45.0}


def normalize_record(raw):
    """
    Kaynaktan gelen ham kaydi, uygulamamizin standart deprem formatina cevirir.
    API'nin tam alan adlari zaman icinde degisebilir; bu yuzden birden fazla
    olasi anahtar adi deneniyor (get ile guvenli erisim).
    """
    try:
        geojson = raw.get("geojson", {})
        coords = geojson.get("coordinates", [None, None])
        lon, lat = coords[0], coords[1]

        return {
            "id": raw.get("earthquake_id") or raw.get("_id"),
            "title": raw.get("title"),
            "magnitude": raw.get("mag"),
            "depth_km": raw.get("depth"),
            "date_utc": raw.get("date"),
            "latitude": lat,
            "longitude": lon,
            "location_name": (raw.get("location_properties", {}) or {})
                .get("epiCenter", {}).get("name") if raw.get("location_properties") else raw.get("title"),
        }
    except Exception:
        return None


def in_turkey_bbox(record):
    lat, lon = record.get("latitude"), record.get("longitude")
    if lat is None or lon is None:
        return False
    return (TR_BBOX["min_lat"] <= lat <= TR_BBOX["max_lat"] and
            TR_BBOX["min_lon"] <= lon <= TR_BBOX["max_lon"])


def fetch():
    try:
        resp = requests.get(API_URL, timeout=20)
        resp.raise_for_status()
        payload = resp.json()

        raw_list = payload.get("result", [])
        normalized = [normalize_record(r) for r in raw_list]
        normalized = [r for r in normalized if r and in_turkey_bbox(r)]

        save_json(OUTPUT_FILE, normalized, SOURCE_NAME)

    except Exception as e:
        save_error_fallback(OUTPUT_FILE, SOURCE_NAME, str(e))


if __name__ == "__main__":
    fetch()
