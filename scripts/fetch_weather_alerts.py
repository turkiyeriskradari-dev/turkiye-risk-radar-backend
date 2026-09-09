"""
Meteorolojik risk gostergesi.

ONEMLI NOT - STRATEJI DEGISIKLIGI:
MGM'in resmi "MeteoUyari" sayfasi (mgm.gov.tr/Meteouyari/turkiye.aspx)
robots.txt ile otomatik erisimi (bot/scraping) acikca yasaklamis durumda
(tipki havaizleme.gov.tr gibi). Bu yuzden resmi MGM uyarisini birebir
almak yerine, zaten kullandigimiz Open-Meteo Forecast API'sinden gelen
ham tahmin verilerini (yagis, ruzgar, sicaklik) kendi belirledigimiz
esiklerle degerlendirip KENDI RISK GOSTERGEMIZI hesapliyoruz.

BU VERI MGM'IN RESMI UYARISI DEGILDIR. Uygulama tarafinda bu katman
"MGM Uyarisi" olarak DEGIL, "Hava Durumu Risk Gostergesi (bagimsiz
hesaplama)" gibi dogru bir isimle sunulmalidir - Play Store'un yaniltici
isimlendirme kurallarina uyum ve kullanici guveni acisindan onemli.

Esikler kabaca MGM'in kamuya acik yayinlarinda kullandigi mertebelere
yakin tutulmustur ama resmi/hesaplanmis degerler degildir, sadece
"kabaca ne kadar riskli" hissi vermek icin basitlestirilmis bir modeldir.

Dokumantasyon: https://open-meteo.com/en/docs
"""
import requests
from utils import save_json, save_error_fallback

SOURCE_NAME = "Hava Durumu Risk Gostergesi (Open-Meteo tahminine dayali, bagimsiz hesaplama)"
OUTPUT_FILE = "weather_alerts.json"

API_URL = "https://api.open-meteo.com/v1/forecast"

# Ayni il listesi fetch_air_quality.py'de de var; ileride ortak bir
# dosyaya (turkiye_iller.py) tasinabilir, simdilik basitlik icin
# burada da tekrar taniml
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

DAILY_VARS = "precipitation_sum,windspeed_10m_max,temperature_2m_max,temperature_2m_min"


def build_params():
    lats = ",".join(str(p[1]) for p in PROVINCES)
    lons = ",".join(str(p[2]) for p in PROVINCES)
    return {
        "latitude": lats,
        "longitude": lons,
        "daily": DAILY_VARS,
        "forecast_days": 2,
        "timezone": "auto",
    }


def classify_level(precipitation, wind, temp_max, temp_min):
    """
    Kabaca esiklere dayali basit bir risk seviyesi hesaplar.
    Bu RESMI MGM esikleri DEGILDIR, sadece genel bir yaklasimdir.
    """
    alerts = []

    if precipitation is not None:
        if precipitation >= 50:
            alerts.append({"type": "Sel/Taşkın Riski", "level": "Turuncu"})
        elif precipitation >= 20:
            alerts.append({"type": "Sel/Taşkın Riski", "level": "Sarı"})

    if wind is not None:
        if wind >= 70:
            alerts.append({"type": "Fırtına", "level": "Turuncu"})
        elif wind >= 50:
            alerts.append({"type": "Fırtına", "level": "Sarı"})

    if temp_max is not None:
        if temp_max >= 40:
            alerts.append({"type": "Aşırı Sıcak", "level": "Turuncu"})
        elif temp_max >= 35:
            alerts.append({"type": "Aşırı Sıcak", "level": "Sarı"})

    if temp_min is not None:
        if temp_min <= -10:
            alerts.append({"type": "Aşırı Soğuk", "level": "Turuncu"})
        elif temp_min <= 0:
            alerts.append({"type": "Aşırı Soğuk", "level": "Sarı"})

    return alerts


def normalize_response(raw_response):
    if isinstance(raw_response, dict):
        raw_response = [raw_response]

    records = []
    for i, item in enumerate(raw_response):
        if i >= len(PROVINCES):
            break
        province_name = PROVINCES[i][0]
        daily = item.get("daily", {})

        precipitation_list = daily.get("precipitation_sum", [])
        wind_list = daily.get("windspeed_10m_max", [])
        tmax_list = daily.get("temperature_2m_max", [])
        tmin_list = daily.get("temperature_2m_min", [])
        dates = daily.get("time", [])

        precipitation = precipitation_list[0] if precipitation_list else None
        wind = wind_list[0] if wind_list else None
        tmax = tmax_list[0] if tmax_list else None
        tmin = tmin_list[0] if tmin_list else None
        forecast_date = dates[0] if dates else None

        alerts = classify_level(precipitation, wind, tmax, tmin)

        records.append({
            "province": province_name,
            "forecast_date": forecast_date,
            "precipitation_mm": precipitation,
            "wind_speed_max_kmh": wind,
            "temperature_max_c": tmax,
            "temperature_min_c": tmin,
            "alerts": alerts,  # bos liste = ozel bir risk tespit edilmedi
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
