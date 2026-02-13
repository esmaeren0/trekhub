
# All Cafes — Spatial Distribution (Map)


<img width="834" height="350" alt="Ekran Resmi 2026-02-13 09 12 00" src="https://github.com/user-attachments/assets/87ae7c96-aa2a-4e84-b0d6-106197f6fcf5" />

---

## `mart.map_points_lat_lon` Dataset’i

Bu dataset:

> İstanbul’daki tüm cafelerin **coğrafi konumlarını (latitude / longitude)**
> Superset’te **harita görselleştirmesi** için kullanılabilir hale getirmek amacıyla oluşturulmuştur.

Bu sayede:

* ham `clean.cafes` tablosu doğrudan görselleştirilmemiş,
* harita için gerekli olmayan kolonlar ayıklanmış,
* Superset tarafında **performanslı ve stabil** bir harita kurulmuştur.

---

## 1. `mart.map_points_lat_lon` Nasıl Ürettim?

### 1.1 Kullandığım SQL Mantığı

Bu dataset, `mart.map_points` tablosundan türetilmiştir.
Amaç: **geometry yerine sayısal koordinatlarla** harita çizmek.

```sql
SELECT
    place_id,
    name,
    district,
    rating,
    user_ratings_total,
    price_level,
    business_status,
    website,
    google_maps_url,

    ST_Y(geom) AS latitude,
    ST_X(geom) AS longitude

FROM mart.map_points
WHERE geom IS NOT NULL;
```

---

## 2. Kolon Bazında Açıklama

Aşağıda **harita görselleştirmesinde gerçekten kullanılan** kolonların
nereden geldiğini ve hangi amaçla kullanıldığını açıkladım.

---

### 2.1 `latitude` / `longitude`

**Kaynak:**

```sql
ST_Y(geom) AS latitude
ST_X(geom) AS longitude
```

**Veri Tipi:**

* `double precision`

**Amaç:**

> Cafelerin harita üzerindeki **noktasal konumlarını** göstermek

**Neden geometry değil?**

* Yüksek nokta sayısında (≈15.000) `lat/lon` daha performanslı
* Frontend tarafında SRID / geometry kaynaklı hataları önler
* Sadece **görselleştirme amacıyla** kullanılır

---


## 3. Bu Dataset Superset’te Nasıl Kullanıldı?

### “All Cafes — Spatial Distribution” Haritası

<img width="1467" height="810" alt="Ekran Resmi 2026-02-13 09 11 21" src="https://github.com/user-attachments/assets/406f418b-b46e-40b0-9192-77a4233dde3e" />
**Chart Type:**

* `deck.gl Scatterplot`

**Query Ayarları:**

* Longitude: `longitude`
* Latitude: `latitude`
* Row limit: `20000`
* Ignore null locations: ✔

 Bu görsel için **Superset tarafında ek bir SQL hesaplaması yapmadım**.

---

### Map Ayarları

* Map style: Streets (OSM)
* Auto zoom: Açık

**Amaç:**

* Haritanın otomatik olarak İstanbul ölçeğine odaklanması

---


## 4. Bu Harita Ne Gösteriyor?

Bu görsel:

> İstanbul’daki cafelerin **noktasal mekânsal dağılımını** gösterir.

Harita incelendiğinde:

* Cafeler şehir genelinde **eşit dağılmamıştır**
* Merkez ve sahil akslarında belirgin yoğunlaşma vardır
* Kadıköy – Beşiktaş – Şişli hattı güçlü bir kümelenme gösterir
* Kuzey bölgelerde cafe yoğunluğu düşüktür

---

## 5. Analitik Yorum


> Noktasal kümelenmeler, cafe pazarında **rekabetin mekânsal olarak yoğunlaştığını** göstermektedir.

Bu durum:

* aynı müşteri kitlesini paylaşan çok sayıda cafe,
* yüksek rekabet baskısı,
* lokasyonun açılış kararlarında kritik rol oynaması
  anlamına gelir.

---


## 6. Bu Görselleştirmenin Projedeki Rolü

Bu harita:

* heatmap analizleri için **referans zemin**,
* rekabet analizleri için **başlangıç noktası**,
* opportunity analizlerinin **coğrafi bağlamıdır**.

Bu nedenle dashboard’un **ilk ve temel katmanı** olarak konumlandırılmıştır.


