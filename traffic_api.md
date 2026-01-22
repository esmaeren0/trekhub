

#  TrekHub — Gerçek Trafik Verisi Entegrasyonu (TomTom API)

## Geo-Grid Based Real-Time Traffic Flow Pipeline (PostGIS → API → PostgreSQL → Superset)

**Geliştirici:** Esma Eren

**Proje Türü:** Veri Zenginleştirme (Data Enrichment) · API Pipeline · Geo Analytics · BI Dashboard

**Kapsam:** İstanbul 500m Grid Hücreleri Üzerinden Trafik Yoğunluğu (Real-Time Flow)

> Bu doküman, TrekHub İstanbul mekan verisi projemde **gerçek trafik yoğunluğu** verisini TomTom API’den çekerek PostgreSQL’e yazdığım ve Superset’te görselleştirmeye hazır hale getirdiğim uçtan uca sistemi anlatır.
> Amaç, elimdeki cafe verisindeki “proxy trafik” (review bazlı tahmini yoğunluk) yaklaşımını **gerçek trafik verisiyle karşılaştırmak** ve dashboard’da “Traffic & Accessibility” sayfasını endüstri standardına taşımaktır.

---

##  İçindekiler

1. [Amaç ve Vizyon](#-1-amaç-ve-vizyon)
2. [Neden Trafik Verisi? (Proxy vs Real)](#-2-neden-trafik-verisi-proxy-vs-real)
3. [Mimari: End-to-End Traffic Pipeline](#-3-mimari-end-to-end-traffic-pipeline)
4. [Kullanılan Tablolar ve Veri Modeli](#-4-kullanılan-tablolar-ve-veri-modeli)
5. [TomTom Traffic API: Çekilen Alanlar](#-5-tomtom-traffic-api-çekilen-alanlar)
6. [ETL Akışı: Grid → API → DB Insert/Upsert](#-6-etl-akışı-grid--api--db-insertupsert)
7. [Hatalar ve Debugging Süreci](#-7-hatalar-ve-debugging-süreci)
8. [Doğrulama: Veri Çekildi mi?](#-8-doğrulama-veri-çekildi-mi)
9. [Superset Kullanımı: Traffic Dashboard (Sayfa 2)](#-9-superset-kullanımı-traffic-dashboard-sayfa-2)
10. [Proxy vs Real Trafik Karşılaştırması](#-10-proxy-vs-real-trafik-karşılaştırması)
11. [Roadmap](#-11-roadmap)

---

# 1) Amaç ve Vizyon

TrekHub projesinde İstanbul’daki 14,879 mekân için çok sayıda feature topladım. Ancak lokasyon analitiği (geo analytics) tarafında projenin “wow effect” kazanması için yalnızca **kafe yoğunluğu** değil, aynı zamanda:

**Gerçek trafik yoğunluğu / akış verisi (traffic flow)**

**erişilebilirlik (accessibility)**

**insan hareketliliği proxy’si ile doğrulama** gibi ileri seviye katmanlara ihtiyaç vardı.

Bu yüzden projeye ayrı bir modül olarak “Real Traffic API Enrichment Pipeline” ekledim.

---

#  2) Neden Trafik Verisi? (Proxy vs Real)

## 2.1 Proxy Traffic (tahmin)

Ben elimdeki cafe dataset’inden trafik yoğunluğu için bir proxy üretebiliyorum:

* `user_ratings_total` (review) = **foot traffic proxy**
* `cafe_count` = mekan yoğunluğu
* `proxy_traffic_index` = grid üzerinde yoğunluk skoru ama bu yaklaşım **tahmin**.

## 2.2 Real Traffic (gerçek)

Gerçek veri ile doğrulama için:

* TomTom Traffic API’den **currentSpeed** / **freeFlowSpeed** aldım
* trafik sıkışıklığını bir skora indirdim: `congestion_index`

> Bu modül sayesinde dashboard’da “proxy ile gerçek trafik aynı mı?” sorusuna cevap verebiliyorum.

---

#  3) Mimari: End-to-End Traffic Pipeline

Bu sistem, İstanbul’u **500m grid** hücrelere bölüp her hücre merkezi için trafik verisi çeker.

```
mart.grid_heatmap_500m   (PostGIS grid + centroid)
        |
        v
Python: traffic_api.py   (TomTom requests + parsing)
        |
        v
mart.real_traffic_flow_grid (upsert ile güncellenen gerçek trafik tablosu)
        |
        v
Superset Page 2 (Traffic & Accessibility)
```

---

#  4) Kullanılan Tablolar ve Veri Modeli

## 4.1 Kaynak: 500m Grid Tablosu

### `mart.grid_heatmap_500m`

Bu tabloyu PostGIS ile ürettim. İstanbul sınırındaki alan:

* 500m kare grid’e bölündü
* her hücre:

  * polygon geometry (`cell_geom_3857`)
  * merkez nokta (`cell_centroid_4326`)
  * yoğunluk metrikleri (`cafe_count`, `total_reviews`, `proxy_traffic_index`) içerir

Trafik çekimi için kullandığım minimum alanlar:

* `grid_id`
* `cell_centroid_4326`

lat/lon türetme:

* `lat = ST_Y(cell_centroid_4326)`
* `lon = ST_X(cell_centroid_4326)`

---

## 4.2 Hedef: Real Traffic Çıktı Tablosu

### `mart.real_traffic_flow_grid`

Bu tablo TomTom’dan çektiğim gerçek trafik verisini saklar.

**Şema (son hali):**

| Kolon            | Tip              | Açıklama                           |
| ---------------- | ---------------- | ---------------------------------- |
| grid_id          | bigint           | Primary Key (grid hücresi kimliği) |
| lat              | double precision | Grid merkez enlemi                 |
| lon              | double precision | Grid merkez boylamı                |
| current_speed    | double precision | Anlık hız                          |
| free_flow_speed  | double precision | Trafiksiz hız                      |
| confidence       | double precision | Ölçüm güveni                       |
| road_closure     | boolean          | Yol kapalı mı                      |
| congestion_index | double precision | Trafik yoğunluk skoru (türetilmiş) |
| fetched_at       | timestamptz      | Verinin çekildiği timestamp        |

### 4.2.1 Neden grid_id Primary Key?

Bu modül tekrar çalıştırılabilir bir pipeline olduğu için:

* aynı grid için trafik sürekli değişebilir
* ben tek satır tutup güncellemek istiyorum
* duplicate istemiyorum

Bu yüzden `grid_id` PK yapıp **UPSERT** kullandım.

---

#  5) TomTom Traffic API: Çekilen Alanlar

## 5.1 Kullanılan veri kaynağı

TomTom Traffic Flow Segment Data (Flow verisi).

Her grid noktası için:

* `point=lat,lon`
* `key=API_KEY`

## 5.2 Çektiğim alanlar

* `currentSpeed`: anlık hız (km/h)
* `freeFlowSpeed`: trafik yokken beklenen hız
* `confidence`: ölçüm güven skoru
* `roadClosure`: yol kapalı mı

## 5.3 Trafik yoğunluğu skoru (congestion_index)

Ben API’nin hız değerlerini direkt kullanmak yerine tek bir skora indirgedim:

**Formül:**

```
congestion_index = 1 - (current_speed / free_flow_speed)
```

**Yorum:**

* 0.00 → akış normal
* 0.30 → orta yoğunluk
* 0.60+ → yüksek yoğunluk
* 0.80+ → aşırı sıkışıklık

---

# 6) ETL Akışı: Grid → API → DB Insert/Upsert

Bu modülün ETL mantığı:

## 6.1 Extract

DB’den grid noktalarını çek:

```sql
SELECT
  grid_id,
  ST_Y(cell_centroid_4326) AS lat,
  ST_X(cell_centroid_4326) AS lon
FROM mart.grid_heatmap_500m
WHERE cell_centroid_4326 IS NOT NULL
ORDER BY grid_id;
```

## 6.2 Transform

Python script içinde:

* TomTom response parse
* hızları al
* congestion_index hesapla
* satır formatla

## 6.3 Load

Batch insert ile DB’ye yaz:

* 300 satır biriktir
* `execute_values` ile insert et
* `ON CONFLICT(grid_id) DO UPDATE` ile güncelle

Bu sayede:
- hızlı
- güvenli
- tekrar çalıştırılabilir
- duplicate üretmez

---

# 7) Hatalar ve Debugging Süreci

Bu entegrasyon sırasında gerçek senaryoda 3 kritik problem çözüldü:



## 7.1 Transaction aborted spam

Hata:

```
current transaction is aborted, commands ignored...
```

Sebep:

* psycopg2’de transaction içinde hata olunca rollback yapılmazsa
* sonrası sürekli fail olur

Çözüm:

* Python try/except içinde `conn.rollback()` ekledim

---

## 7.2 MAX_REQUESTS ile kontrollü çekim

İstanbul grid büyük olduğu için:

* önce test amaçlı `MAX_REQUESTS` ile sınırlı çekim yaptım
* sonra limit artırarak kademeli doldurdum

Bu strateji:

* quota / rate limit riskini azalttı
* pipeline’ı güvenli hale getirdi

---

# 8) Doğrulama: Veri Çekildi mi?

## 8.1 DB satır kontrolü

```sql
SELECT COUNT(*) AS rows
FROM mart.real_traffic_flow_grid;
```

## 8.2 Dolu veri kontrolü

```sql
SELECT
  COUNT(*) total,
  COUNT(current_speed) with_speed,
  MIN(fetched_at) min_time,
  MAX(fetched_at) max_time
FROM mart.real_traffic_flow_grid;
```

## 8.3 En yoğun grid’ler

```sql
SELECT *
FROM mart.real_traffic_flow_grid
ORDER BY congestion_index DESC
LIMIT 20;
```

---

# 9) Superset Kullanımı: Traffic Dashboard (Sayfa 2)

Bu tablo Superset’te “Traffic & Accessibility” sayfasında kullanılıyor.

### Harita 1 — Real Traffic Scatter / Heatmap

* Dataset: `mart.real_traffic_flow_grid`
* Viz: Deck.gl Scatter veya Heatmap
* Lat/Lon: `lat`, `lon`
* Color: `congestion_index`
* Tooltip: current_speed, free_flow_speed, fetched_at

---

# 🔍 10) Proxy vs Real Trafik Karşılaştırması

Bu bölüm projenin en güçlü tarafı: proxy doğruluğunu ölçmek.

## 10.1 Join view

```sql
CREATE OR REPLACE VIEW mart.v_proxy_vs_real_traffic AS
SELECT
  g.grid_id,
  g.proxy_traffic_index,
  r.congestion_index,
  r.current_speed,
  r.free_flow_speed,
  r.fetched_at
FROM mart.grid_heatmap_500m g
JOIN mart.real_traffic_flow_grid r
  ON r.grid_id = g.grid_id;
```

## 10.2 Korelasyon analizi

```sql
SELECT corr(proxy_traffic_index, congestion_index) AS corr_proxy_real
FROM mart.v_proxy_vs_real_traffic;
```

Bu skor sayesinde:

* proxy yaklaşımımın doğruluğunu ölçüyorum
* gerektiğinde proxy formülünü iyileştirebiliyorum

---

# 11) Roadmap

* Trafik verisini zaman serisi olarak tutmak (daily snapshots)
* Saat bazlı farklılık analizi (peak hour analysis)
* Opportunity Score içine trafik bileşeni eklemek

