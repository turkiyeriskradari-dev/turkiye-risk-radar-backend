# Türkiye Risk Radar — Backend

Bu depo, Türkiye Risk Radar Android uygulamasının veri katmanlarını besleyen
"sunucusuz backend"tir. Gerçek bir sunucu barındırmak yerine **GitHub Actions**
ile periyodik olarak veri çeker, temizler ve **GitHub Pages** üzerinden
statik JSON dosyaları olarak yayınlar.

## Nasıl çalışıyor?

```
GitHub Actions (her 15 dakikada bir, otomatik)
   → scripts/fetch_*.py dosyalarını çalıştırır
   → data/*.json dosyalarını günceller
   → değişikliği otomatik commit + push eder
GitHub Pages
   → data/ klasörünü statik web sitesi olarak yayınlar
Android Uygulaması
   → bu JSON URL'lerine düz HTTP GET isteği atar
```

## Kurulum Adımları

### 1. Bu depoyu GitHub'a yükleyin
```bash
git init
git add .
git commit -m "İlk kurulum"
git branch -M main
git remote add origin https://github.com/KULLANICI_ADINIZ/turkiye-risk-radar-backend.git
git push -u origin main
```

### 2. GitHub Pages'i etkinleştirin
Repo → Settings → Pages → Source: **Deploy from a branch** → Branch: **main**, klasör: **/ (root)**
(Ya da isterseniz sadece `data/` klasörünü yayınlamak için `/docs` gibi bir klasöre taşıyıp onu seçebilirsiniz — şimdilik root yeterli.)

Birkaç dakika sonra veriler şu adreslerden erişilebilir olur:
```
https://KULLANICI_ADINIZ.github.io/turkiye-risk-radar-backend/data/earthquakes.json
https://KULLANICI_ADINIZ.github.io/turkiye-risk-radar-backend/data/wildfires.json
https://KULLANICI_ADINIZ.github.io/turkiye-risk-radar-backend/data/air_quality.json
https://KULLANICI_ADINIZ.github.io/turkiye-risk-radar-backend/data/weather_alerts.json
https://KULLANICI_ADINIZ.github.io/turkiye-risk-radar-backend/data/reservoirs.json
```
Android uygulaması sadece bu URL'leri bilecek, kaynak kurumları (AFAD, MGM vb.) hiç tanımayacak.

### 3. NASA FIRMS için API anahtarı alın (orman yangını katmanı için gerekli)
1. https://firms.modis.gov/api/area/ sayfasından ücretsiz bir MAP_KEY alın
2. Repo → Settings → Secrets and variables → Actions → **New repository secret**
3. Adı: `FIRMS_MAP_KEY`, değeri: aldığınız anahtar

### 4. Workflow'u test edin
Repo → Actions sekmesi → "Veri Güncelleme" → **Run workflow** ile elle bir kere çalıştırıp
`data/` klasöründe dosyaların oluştuğunu kontrol edin.

## Veri Kaynaklarının Durumu

| Katman | Script | Durum |
|---|---|---|
| Deprem | `fetch_earthquakes.py` | ✅ Çalışır durumda (Kandilli topluluk API'si) |
| Orman yangını | `fetch_wildfires.py` | ✅ Çalışır durumda (NASA FIRMS resmi API, sadece MAP_KEY gerekli) |
| Hava kalitesi | `fetch_air_quality.py` | 🚧 Taslak — gerçek endpoint birlikte tespit edilecek |
| MGM meteorolojik uyarı | `fetch_weather_alerts.py` | 🚧 Taslak — gerçek endpoint birlikte tespit edilecek |
| Baraj doluluk oranı | `fetch_reservoirs.py` | 🚧 Taslak — İSKİ sayfası HTML parse gerektirebilir |

## Standart JSON Formatı

Her dosya aynı "zarf" (envelope) yapısını kullanır, böylece Android tarafı
tek bir ortak parser yazabilir:

```json
{
  "source": "Kandilli Rasathanesi (...)",
  "last_updated": "2026-09-08T12:00:00+00:00",
  "record_count": 12,
  "data": [ ... ]
}
```

## Sırada Ne Var?

1. Taslak halindeki 3 script için gerçek endpoint'leri birlikte tespit edip tamamlamak
   (tarayıcı Geliştirici Araçları ile "Network" sekmesinden inceleme yapılacak)
2. Depoyu GitHub'a yükleyip Pages ve Actions'ı devreye almak
3. İlk birkaç saat boyunca Actions loglarını izleyip veri akışının düzgün çalıştığını doğrulamak
4. Android tarafında bu JSON uç noktalarını okuyan Retrofit servislerini yazmaya başlamak
