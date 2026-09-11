"""
Nobetci eczane verisi: nobetcieczanen.com

ROBOTS.TXT DURUMU: Sadece /config/, /api/, /admin/ yasakli. Genel
veri sayfalari (il/ilce) serbest, ozel bir AI-bot yasagi yok.

NEDEN BU KAYNAK: Site, her il/ilce sayfasinda schema.org uyumlu
JSON-LD yapisi (<script type="application/ld+json">) icinde
Pharmacy nesneleri sunuyor - bu, kirilgan CSS/class tabanli scraping
yerine cok daha saglam, standart bir veri cikarma yontemi sagliyor.

YAPI: Iki asamali crawling gerekiyor:
  1) Her il sayfasi (/{il-slug}) o ile ait ilce linklerini listeliyor
  2) Her ilce sayfasi (/{il-slug}/{ilce-slug}) o ilcenin GUNCEL
     nobetci eczanelerini JSON-LD icinde sunuyor
Toplam ~900 istek oldugu icin bu script GUNDE BIR KEZ calistirilmali
(15 dakikada bir DEGIL) - hem kaynak siteye saygili olmak hem de
nobetci listesinin zaten gunde en fazla 1-2 kez degismesi nedeniyle.

BU VERI RESMI DEGILDIR (TEB/Eczaci Odasi verisi degil, bagimsiz bir
rehber sitesi). Uygulama tarafinda "Kaynak: nobetcieczanen.com
(ucuncu taraf)" seklinde belirtilmeli.
"""
import json
import re
import time
import requests
from bs4 import BeautifulSoup
from utils import save_json, save_error_fallback

SOURCE_NAME = "nobetcieczanen.com - ÜÇÜNCÜ TARAF, GAYRİRESMİ"
OUTPUT_FILE = "pharmacies.json"
BASE_URL = "https://nobetcieczanen.com"
REQUEST_DELAY = 0.35

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TurkiyeRiskRadarBot/1.0)"}

PROVINCES_TR = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara",
    "Antalya", "Artvin", "Aydın", "Balıkesir", "Bilecik", "Bingöl",
    "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum",
    "Denizli", "Diyarbakır", "Edirne", "Elazığ", "Erzincan", "Erzurum",
    "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkari", "Hatay",
    "Isparta", "Mersin", "İstanbul", "İzmir", "Kars", "Kastamonu",
    "Kayseri", "Kırklareli", "Kırşehir", "Kocaeli", "Konya", "Kütahya",
    "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla", "Muş",
    "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt",
    "Sinop", "Sivas", "Tekirdağ", "Tokat", "Trabzon", "Tunceli",
    "Şanlıurfa", "Uşak", "Van", "Yozgat", "Zonguldak", "Aksaray",
    "Bayburt", "Karaman", "Kırıkkale", "Batman", "Şırnak", "Bartın",
    "Ardahan", "Iğdır", "Yalova", "Karabük", "Kilis", "Osmaniye", "Düzce",
]

_TR_MAP = str.maketrans({
    "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ı": "i", "I": "i",
    "İ": "i", "ö": "o", "Ö": "o", "ş": "s", "Ş": "s", "ü": "u", "Ü": "u",
})


def slugify_tr(ad):
    return ad.lower().translate(_TR_MAP)


def get_district_slugs(il_slug):
    url = f"{BASE_URL}/{il_slug}"
    resp = requests.get(url, timeout=20, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    districts = []
    seen = set()
    pattern = re.compile(rf"^/{re.escape(il_slug)}/([a-z0-9\-]+)$")
    for a in soup.find_all("a", href=True):
        m = pattern.match(a["href"])
        if m:
            ilce_slug = m.group(1)
            if ilce_slug not in seen:
                seen.add(ilce_slug)
                districts.append(ilce_slug)
    return districts


def extract_pharmacies_from_jsonld(html):
    soup = BeautifulSoup(html, "lxml")
    results = []

    for script_tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script_tag.string)
        except Exception:
            continue

        graph = data.get("@graph", [data]) if isinstance(data, dict) else data
        for node in graph:
            main_entity = node.get("mainEntity") if isinstance(node, dict) else None
            if not main_entity:
                continue
            items = main_entity.get("itemListElement", [])
            for item in items:
                pharmacy = item.get("item", {})
                if pharmacy.get("@type") != "Pharmacy":
                    continue
                address = pharmacy.get("address", {})
                results.append({
                    "name": pharmacy.get("name"),
                    "phone": pharmacy.get("telephone"),
                    "address": address.get("streetAddress"),
                    "district": address.get("addressLocality"),
                    "province": address.get("addressRegion"),
                })
    return results


def fetch():
    all_records = []
    failed = []
    diagnostic_samples = []

    for il_adi in PROVINCES_TR:
        il_slug = slugify_tr(il_adi)
        try:
            district_slugs = get_district_slugs(il_slug)
            time.sleep(REQUEST_DELAY)
        except Exception as e:
            failed.append(f"{il_adi} (ilce listesi alinamadi: {e})")
            continue

        if not district_slugs and len(diagnostic_samples) < 2:
            diagnostic_samples.append(f"{il_adi}: ilce linki bulunamadi")

        for ilce_slug in district_slugs:
            url = f"{BASE_URL}/{il_slug}/{ilce_slug}"
            try:
                resp = requests.get(url, timeout=20, headers=HEADERS)
                resp.raise_for_status()
                records = extract_pharmacies_from_jsonld(resp.text)
                all_records.extend(records)
            except Exception as e:
                failed.append(f"{il_adi}/{ilce_slug} ({e})")
            time.sleep(REQUEST_DELAY)

    if not all_records:
        save_error_fallback(
            OUTPUT_FILE, SOURCE_NAME,
            f"Hic kayit alinamadi. Basarisiz sayfa sayisi: {len(failed)}. "
            f"Ornekler: {failed[:10]}. Teshis: {diagnostic_samples}"
        )
        return

    extra_meta = {
        "warning": "Bu veri resmi TEB/Eczaci Odasi verisi DEGILDIR, "
                   "ucuncu taraf bir siteden (nobetcieczanen.com) "
                   "derlenmistir.",
        "failed_page_count": len(failed),
    }
    if failed:
        extra_meta["failed_pages_sample"] = failed[:10]

    save_json(OUTPUT_FILE, all_records, SOURCE_NAME, extra_meta=extra_meta)


if __name__ == "__main__":
    fetch()
