"""
Baraj doluluk orani verisi.

ONEMLI NOT - VERI KAYNAGI HAKKINDA:
Resmi kurumlarin (ISKI, DSI) siteleri robots.txt ile otomatik erisimi
yasakladigi icin, bunun yerine barajdolulukoranlari.com adli UCUNCU TARAF
(resmi olmayan, reklam destekli) bir siteyi kullaniyoruz. Bu site kendi
ifadesine gore "resmi istatistik veri tabanlarindan" veri derliyor ve
robots.txt ile bot erisimini engellemiyor.

BU VERI RESMI DEGILDIR. Uygulama tarafinda mutlaka "Kaynak: Turkiye
Barajlar (ucuncu taraf, gayriresmi)" seklinde belirtilmeli, ISKI/DSI
resmi verisiymis gibi sunulmamalidir.

Ayrica: bu site kucuk/nis bir proje oldugu icin sitenin yapisi
degisirse (HTML guncellenirse) bu script bozulabilir - fallback
mekanizmasi (eski veriyi koruma) bu riske karsi onemlidir.

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

ENTRY_PATTERN = re.compile(
    r'^(?P<name>.+?)'
    r'(?P<havza>' + _HAVZA_ALTERNATION + r')'
    r'\s*Havzası'
    r'(?:\s*·\s*(?P<il>[A-ZÇĞİŞÖÜ]+))?'
    r'(?P<percent>[\d.,]+)%'
    r'\s*📅\s*(?P<date>[\d]{1,2}\s\w+\s\d{4})'
    r'(?:\s*⚡\s*(?P<mw>[\d.,]+)\s*MW)?'
)


def parse_entry_text(text):
    """
    Bir <a href="/baraj/..."> etiketinin metnini yukaridaki bilinen
    havza listesiyle esleyerek ayristirir. Eslesme olmazsa None doner
    (o kayit atlanir, tum script cokmez).
    """
    text = " ".join(text.split())  # fazla bosluklari temizle
    m = ENTRY_PATTERN.match(text)
    if not m:
        return None

    d = m.groupdict()
    try:
        percent = float(d["percent"].replace(",", "."))
    except (TypeError, ValueError):
        percent = None

    mw = None
    if d.get("mw"):
        try:
            mw = float(d["mw"].replace(",", "."))
        except ValueError:
            mw = None

    return {
        "name": d["name"].strip(),
        "havza": d["havza"].strip(),
        "province": d["il"].strip() if d.get("il") else None,
        "fill_percentage": percent,
        "measured_date": d["date"].strip(),
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
        for link in dam_links:
            parsed = parse_entry_text(link.get_text())
            if parsed and parsed["name"] not in seen_names:
                records.append(parsed)
                seen_names.add(parsed["name"])

        if not records:
            save_error_fallback(
                OUTPUT_FILE, SOURCE_NAME,
                "Hic kayit ayristirilamadi - site yapisi degismis olabilir, "
                "ENTRY_PATTERN regex'inin guncellenmesi gerekebilir."
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
