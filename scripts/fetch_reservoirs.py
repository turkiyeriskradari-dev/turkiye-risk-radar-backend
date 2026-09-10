"""
Baraj doluluk orani verisi.

ONEMLI NOT - VERI KAYNAGI HAKKINDA:
Resmi kurumlarin (ISKI, DSI) siteleri robots.txt ile otomatik erisimi
yasakladigi icin, bunun yerine barajdolulukoranlari.com adli UCUNCU TARAF
(resmi olmayan, reklam destekli) bir siteyi kullaniyoruz.

BU VERI RESMI DEGILDIR. Uygulama tarafinda mutlaka "Kaynak: Turkiye
Barajlar (ucuncu taraf, gayriresmi)" seklinde belirtilmeli, ISKI/DSI
resmi verisiymis gibi sunulmamalidir.

Kaynak: https://barajdolulukoranlari.com/
"""
import re
import requests
from bs4 import BeautifulSoup
from utils import save_json, save_error_fallback

SOURCE_NAME = "Türkiye Barajlar (barajdolulukoranlari.com) - ÜÇÜNCÜ TARAF, GAYRİRESMİ"
OUTPUT_FILE = "reservoirs.json"

PAGE_URL = "https://barajdolulukoranlari.com/"

HAVZALAR = [
    "Antalya", "Asi", "Batı Akdeniz", "Batı Karadeniz", "Büyük Menderes",
    "Ceyhan", "Doğu Akdeniz", "Doğu Karadeniz", "GEDİZ", "Gediz",
    "Kuzey Ege", "KÜÇÜK MENDERES", "Kızılırmak", "Marmara", "Sakarya",
    "Seyhan", "Susurluk", "Van Gölü", "Yeşilırmak",
]
_HAVZALAR_SORTED = sorted(HAVZALAR, key=len, reverse=True)
_HAVZA_ALTERNATION = "|".join(re.escape(h) for h in _HAVZALAR_SORTED)

MAIN_PATTERN = re.compile(
    r'^(?P<name>.+?)'
    r'(?P<havza>' + _HAVZA_ALTERNATION + r')'
    r'\s*Havzası'
    r'(?:\s*·\s*(?P<il>[A-ZÇĞİŞÖÜ]+))?'
    r'\s*(?P<percent>[\d.,]+)\s*%'
)
DATE_PATTERN = re.compile(r'(\d{1,2}\s+[A-Za-zÇĞİŞÖÜçğıöşü]+\s+\d{4})')
MW_PATTERN = re.compile(r'([\d.,]+)\s*MW')


def parse_entry_text(raw_text):
    text = " ".join(raw_text.split())

    m = MAIN_PATTERN.match(text)
    if not m:
        return None

    d = m.groupdict()
    try:
        percent = float(d["percent"].replace(",", "."))
    except (TypeError, ValueError):
        percent = None

    date_match = DATE_PATTERN.search(text)
    mw_match = MW_PATTERN.search(text)

    mw = None
    if mw_match:
        try:
            mw = float(mw_match.group(1).replace(",", "."))
        except ValueError:
            mw = None

    return {
        "name": d["name"].strip(),
        "havza": d["havza"].strip(),
        "province": d["il"].strip() if d.get("il") else None,
        "fill_percentage": percent,
        "measured_date": date_match.group(1) if date_match else None,
        "hes_capacity_mw": mw,
    }


def fetch():
    try:
        resp = requests.get(PAGE_URL, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (compatible; TurkiyeRiskRadarBot/1.0)"
        })
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        dam_links = soup.find_all("a", href=re.compile(r"/baraj/[^/]+$"))

        records = []
        seen_names = set()
        raw_texts_sample = []
        for link in dam_links:
            raw_text = link.get_text()
            if len(raw_texts_sample) < 5:
                raw_texts_sample.append(raw_text)
            parsed = parse_entry_text(raw_text)
            if parsed and parsed["name"] not in seen_names:
                records.append(parsed)
                seen_names.add(parsed["name"])

        if not records:
            save_error_fallback(
                OUTPUT_FILE, SOURCE_NAME,
                f"Hic kayit ayristirilamadi. Bulunan link sayisi: {len(dam_links)}. "
                f"Ilk 5 ham metin ornegi: {raw_texts_sample}"
            )
            return

        save_json(OUTPUT_FILE, records, SOURCE_NAME, extra_meta={
            "warning": "Bu veri resmi ISKI/DSI verisi DEGILDIR, ucuncu "
                       "taraf bir siteden derlenmistir.",
            "page_source": PAGE_URL,
        })

    except Exception as e:
        save_error_fallback(OUTPUT_FILE, SOURCE_NAME, str(e))


if __name__ == "__main__":
    fetch()
