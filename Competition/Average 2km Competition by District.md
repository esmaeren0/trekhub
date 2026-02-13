

# Average 2km Competition by District
<img width="1421" height="297" alt="Ekran Resmi 2026-02-13 10 12 53" src="https://github.com/user-attachments/assets/669f4a52-a91a-4987-b00c-f101b2c1ab2b" />


Bu görseli üretme amacım, İstanbul’daki ilçelerde **bir cafe için çevresel rekabetin ne kadar yoğun olduğunu** nicel ve karşılaştırılabilir bir metrikle ölçmekti.

Burada sorduğum temel soru şudur:

> **“İstanbul’daki bir cafe, bulunduğu ilçede ortalama olarak 2 km yarıçap içinde kaç rakip cafe ile rekabet ediyor?”**

Bu soru doğrudan şu karar problemlerine hizmet eder:

* yeni şube açma kararlarında **rekabet sertliğini** ölçmek,
* pazarın **doygun olduğu ilçeleri** nicel olarak ayırt etmek,
* fırsat analizi yapılırken **arz tarafını** izole etmek.

 
 Bu analiz **bilinçli olarak**:

* talebi,
* kaliteyi,
* trafiği ölçmez.
Amaç yalnızca **rekabet (arz) boyutunu** saf hâliyle ortaya koymaktır.

---

## 2. Superset’te gördüğüm bu grafik hangi dataset’ten geliyor?

Bu bar chart **doğrudan** aşağıdaki tablodan beslenmektedir:

```sql
mart.cafe_competition_2km
```

Superset yapılandırması:

* **X-axis:** `district`
* **Metric:** `AVG(competitors_within_2km)`
* **Sort:** Ortalama rekabet (DESC)
* **Filter:** `district IS NOT NULL`
* **Aggregation:** Yok (hesaplama SQL tarafında)

Superset bu grafikte **hiçbir istatistiksel hesap yapmaz**.
Tüm hesaplama mantığı **PostgreSQL + PostGIS** tarafında deterministik olarak üretilmiştir.

---

## 3. `mart.cafe_competition_2km` tablosu nasıl ürettim?



```sql
CREATE TABLE mart.cafe_competition_2km AS
SELECT
    a.place_id,
    a.name,
    a.district,
    a.geom,

    ST_Buffer(a.geom::geography, 2000)::geometry AS buffer_2km_geom,

    COUNT(b.place_id) - 1 AS competitors_within_2km,

    AVG(b.rating) FILTER (WHERE b.place_id <> a.place_id)
        AS avg_competitor_rating_2km,

    SUM(COALESCE(b.user_ratings_total, 0))
        FILTER (WHERE b.place_id <> a.place_id)
        AS total_competitor_reviews_2km

FROM clean.cafes a
JOIN clean.cafes b
  ON a.geom IS NOT NULL
 AND b.geom IS NOT NULL
 AND ST_DWithin(a.geom::geography, b.geom::geography, 2000)
GROUP BY a.place_id, a.name, a.district, a.geom;
```

Bu noktada **analizin çekirdeği** oluşur.

Bu tablo:

* **cafe seviyesinde** çalışır,
* her satır **tek bir cafe’yi** temsil eder,
* ilçesel sonuçlar bu mikro ölçümün **agregasyonu**dur.

---

## 4. Kullanılan ana veri kaynağı: `clean.cafes`

Bu tablonun kökü:

```sql
raw.istanbul_cafes_ultra_kopyasi
```

ham datasının temizlenmesiyle oluşturulan:

```sql
clean.cafes
```

tablosudur.

Bu aşamada:

* latitude / longitude → `geom (POINT, SRID 4326)`
* rating → `double precision`
* user_ratings_total → `integer`
* district → `text`

tipleri **bilinçli olarak normalize edilmiştir**.

Bu normalizasyon sayesinde:

* mekânsal fonksiyonlar (ST_DWithin)
* mesafe hesapları
* küresel koordinat hataları

önlenmiş ve analiz **coğrafi olarak güvenilir** hâle getirilmiştir.

---

## 5. 2 km rekabet nasıl tanımlandı? (kritik metodoloji)

### 5.1 Neden `ST_DWithin` + `geography`?

```sql
ST_DWithin(a.geom::geography, b.geom::geography, 2000)
```

Bu tercih şunları garanti eder:

* mesafe **metre cinsinden** ölçülür,
* Dünya eğriliği hesaba katılır,
* düz (planar) koordinat hatası oluşmaz.

 Yani bu analiz:

> “kuş bakışı yaklaşık mesafe” değil,
> **gerçek dünyadaki yürüme / erişim ölçeğine yakın** bir ölçümdür.

---

### 5.2 Rakip sayısı neden `COUNT(*) - 1`?

```sql
COUNT(b.place_id) - 1
```

Buradaki `-1`:

* cafenin **kendini rakip saymaması** içindir.

Matematiksel olarak ölçülen şey şudur:

[
competitors_within_2km(i)
=========================

\left| { j \neq i \mid dist(i, j) \le 2000m } \right|
]

Yani:

> “Bu cafe’nin çevresinde, **kendisi hariç**, kaç cafe var?”

---

## 6. `competitors_within_2km` kolonu neyi temsil eder?

Bu kolon:

* **her bir cafe için**
* **mikro ölçekte**
* **lokasyon bazlı rekabet yoğunluğunu**

temsil eder.

Örnek yorum:

* `competitors_within_2km = 350`
  → aşırı doygun, merkezî bir mikro-pazar

* `competitors_within_2km = 60`
  → görece daha az baskılı, potansiyel alan

Bu metrik:

* kaliteye bakmaz,
* talebi ölçmez,
* **sadece arz yoğunluğunu** ölçer.

Bu bilinçli bir tercihtir.

---

## 7. İlçe bazında ortalama neden ve nasıl alındı?

Superset’te görülen değerler şu mantığın sonucudur:

```sql
SELECT
    district,
    AVG(competitors_within_2km)
FROM mart.cafe_competition_2km
GROUP BY district;
```

Bu şu soruya cevap verir:

> “Bu ilçedeki **ortalama bir cafe**, çevresinde kaç rakiple faaliyet gösteriyor?”

### Neden ortalama?

* İlçenin **genel rekabet sertliğini** temsil eder,
* tekil uç noktaları (extreme hotspot’ları) **bilinçli olarak görünür kılar**,
* pazarın “gerçek baskı seviyesini” yumuşatmaz.

 Median tercih edilmemiştir çünkü bu analizde:

> **yoğun merkezlerin rekabet baskısını bastırmak değil, göstermeyi** amaçladım.

---

## 8. Veri tipleri (kanıt)

| Kolon                        | Tip                   | Açıklama                |
| ---------------------------- | --------------------- | ----------------------- |
| place_id                     | text                  | Cafe kimliği            |
| district                     | text                  | İlçe                    |
| geom                         | geometry(Point, 4326) | Cafe konumu             |
| buffer_2km_geom              | geometry(Polygon)     | 2 km etki alanı         |
| competitors_within_2km       | bigint                | Rakip sayısı            |
| avg_competitor_rating_2km    | double precision      | Rakip kalite ortalaması |
| total_competitor_reviews_2km | bigint                | Rakip popülerliği       |



---

## 9. Bu görsel analitik olarak ne anlatır?

<img width="1462" height="770" alt="Ekran Resmi 2026-02-13 10 11 44" src="https://github.com/user-attachments/assets/04feae9a-3cf6-4e04-bf2b-d6e88f07673f" />


Bu grafik:

* hangi ilçelerde **rekabetin yapısal olarak sert** olduğunu,
* hangi ilçelerde **görece daha az baskı** bulunduğunu

açık biçimde gösterir.

Yüksek barlar:

* merkezî,
* doygun,
* yeni giriş için **farklılaşma zorunluluğu olan** ilçeleri temsil eder.

Düşük barlar:

* rekabet baskısı düşük olabilir,
* **ama bu tek başına fırsat anlamına gelmez**.

---

## 10. Executive seviyesinde yorumum

> **“Bu grafik, İstanbul’daki cafe pazarının büyük bölümünün yüksek rekabet koşulları altında faaliyet gösterdiğini ve rekabetin istisna değil, norm olduğunu göstermektedir.”**

Stratejik çıkarım şudur:

* yüksek rekabet → otomatik elenme sebebi değildir,
* düşük rekabet → talep yoksa risklidir.

Bu nedenle bu metrik:

* karar verdirmez,
* ama **çok güçlü bir eleme ve bağlam katmanıdır**.

---

