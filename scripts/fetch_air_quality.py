"""
Hava kalitesi verisi: Open-Meteo Air Quality API.

NEDEN UHKIA (havaizleme.gov.tr) DEGIL DE BU KAYNAK KULLANILIYOR:
havaizleme.gov.tr sitesi robots.txt ile otomatik erisimi (bot/scraping)
acikca yasaklamis durumda. Bunun yerine, tamamen resmi API olarak sunulan,
API anahtari gerektirmeyen, CC-BY 4.0 lisansli Open-Meteo Air Quality
API'sini kullaniyoruz. Bu veri UHKIA'nin kendi istasyon olcumleri degil,
uydu + model tabanli bir tahmindir; ama surdurulebilir, dokumante edilmis
ve her zaman erisilebilir olmasi V1 icin daha guvenilir bir tercih.

Ileride UHKIA'nin gercek istasyon verisine (resmi API acilirsa veya
kullanim izni alinirsa) gecis yapilabilir.

Dokumantasyon: https://open-meteo.com/en/docs/air-quality-api
"""
import requests
from utils import save_json, save_error_fallback

SOURCE_NAME = "Open-Meteo Air Quality API (uydu/model tabanli tahmin)"
OUTPUT_FILE = "air_quality.json"

API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Turkiye'nin 81 il merkezinin yaklasik koordinatlari.
# NOT: Bunlar il merkezi konumlaridir, UHKIA'nin gercek istasyon
# konumlari degildir - "il bazli genel durum" gostermek icin yeterlidir.
PROVINCES = [
    ("Adana", 37.0000, 35.3213), ("Adıyaman", 37.7648, 38.2786),
    ("Afyonkarahisar", 38.7507, 30.5567), ("Ağrı", 39.7191, 43.0503),
    ("Amasya", 40.6499, 35.8353), ("Ankara", 39.9334, 32.8597),
    ("Antalya", 36.8969, 30.7133), ("Artvin", 41.1828, 41.8183),
    ("Aydın", 37.8560, 27.8416), ("Balıkesir", 39.6484, 27.8826),
    ("Bilecik", 40.1451, 29.9792), ("Bingöl", 38.8855, 40.4966),
    ("Bitlis", 38.3938, 42.1232), ("Bolu", 40.5760, 31.5788),
    ("Burdur", 37.7203, 30.2908), ("Bursa", 40.1826, 29.0665),
    ("Çanakkale", 40.1553, 26.4142), ("Çankırı", 40.6013, 33.6134),
    ("Çorum", 40.5506, 34.9556), ("Denizli", 37.7765, 29.0864),
    ("Diyarbakır", 37.9144, 40.2306), ("Edirne", 41.6771, 26.5557),
    ("Elazığ", 38.6810, 39.2264), ("Erzincan", 39.7500, 39.5000),
    ("Erzurum", 39.9000, 41.2700), ("Eskişehir", 39.7767, 30.5206),
    ("Gaziantep", 37.0662, 37.3833), ("Giresun", 40.9128, 38.3895),
    ("Gümüşhane", 40.4386, 39.5086), ("Hakkari", 37.5744, 43.7408),
    ("Hatay", 36.2023, 36.1613), ("Isparta", 37.7648, 30.5566),
    ("Mersin", 36.8000, 34.6333), ("İstanbul", 41.0082, 28.9784),
    ("İzmir", 38.4237, 27.1428), ("Kars", 40.6013, 43.0975),
    ("Kastamonu", 41.3887, 33.7827), ("Kayseri", 38.7312, 35.4787),
    ("Kırklareli", 41.7333, 27.2167), ("Kırşehir", 39.1425, 34.1709),
    ("Kocaeli", 40.8533, 29.8815), ("Konya", 37.8746, 32.4932),
    ("Kütahya", 39.4242, 29.9833), ("Malatya", 38.3552, 38.3095),
    ("Manisa", 38.6191, 27.4289), ("Kahramanmaraş", 37.5753, 36.9228),
    ("Mardin", 37.3212, 40.7245), ("Muğla", 37.2153, 28.3636),
    ("Muş", 38.9462, 41.7539), ("Nevşehir", 38.6939, 34.6857),
    ("Niğde", 37.9667, 34.6833), ("Ordu", 40.9839, 37.8764),
    ("Rize", 41.0201, 40.5234), ("Sakarya", 40.7569, 30.3781),
    ("Samsun", 41.2867, 36.3300), ("Siirt", 37.9333, 41.9500),
    ("Sinop", 42.0231, 35.1531), ("Sivas", 39.7477, 37.0179),
    ("Tekirdağ", 40.9833, 27.5167), ("Tokat", 40.3167, 36.5500),
    ("Trabzon", 41.0027, 39.7168), ("Tunceli", 39.1079, 39.5401),
    ("Şanlıurfa", 37.1591, 38.7969), ("Uşak", 38.6823, 29.4082),
    ("Van", 38.4891, 43.4089), ("Yozgat", 39.8181, 34.8147),
    ("Zonguldak", 41.4564, 31.7987), ("Aksaray", 38.3687, 34.0360),
    ("Bayburt", 40.2552, 40.2249), ("Karaman", 37.1759, 33.2287),
    ("Kırıkkale", 39.8468, 33.5153), ("Batman", 37.8812, 41.1351),
    ("Şırnak", 37.4187, 42.4918), ("Bartın", 41.5811, 32.4610),
    ("Ardahan", 41.1105, 42.7022), ("Iğdır", 39.9167, 44.0333),
    ("Yalova", 40.6500, 29.2667), ("Karabük", 41.2061, 32.6204),
    ("Kilis", 36.7184, 37.1212), ("Osmaniye", 37.0742, 36.2478),
    ("Düzce", 40.8438, 31.1565),
]

CURRENT_VARS = "european_aqi,us_aqi,pm10,pm2_5,dust,ozone,nitrogen_dioxide"


def build_params():
    lats = ",".join(str(p[1]) for p in PROVINCES)
    lons = ",".join(str(p[2]) for p in PROVINCES)
    return {"latitude": lats, "longitude": lons, "current": CURRENT_VARS}


def normalize_response(raw_response):
    """
    Open-Meteo birden fazla konum istendiginde bir LISTE dondurur (her
    eleman bir konumun sonucu), tek konum istendiginde ise TEK bir obje
    dondurur. Bu yuzden ikisini de guvenle isleyebilecek sekilde yaziyoruz.
    """
    if isinstance(raw_response, dict):
        raw_response = [raw_response]

    records = []
    for i, item in enumerate(raw_response):
        if i >= len(PROVINCES):
            break
        province_name = PROVINCES[i][0]
        current = item.get("current", {})
        records.append({
            "province": province_name,
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
            "measured_at": current.get("time"),
            "european_aqi": current.get("european_aqi"),
            "us_aqi": current.get("us_aqi"),
            "pm10": current.get("pm10"),
            "pm2_5": current.get("pm2_5"),
            "dust": current.get("dust"),
            "ozone": current.get("ozone"),
            "nitrogen_dioxide": current.get("nitrogen_dioxide"),
        })
    return records


def fetch():
    try:
        resp = requests.get(API_URL, params=build_params(), timeout=30)
        resp.raise_for_status()
        raw = resp.json()

        normalized = normalize_response(raw)
        save_json(OUTPUT_FILE, normalized, SOURCE_NAME)

    except Exception as e:
        save_error_fallback(OUTPUT_FILE, SOURCE_NAME, str(e))


if __name__ == "__main__":
    fetch()
