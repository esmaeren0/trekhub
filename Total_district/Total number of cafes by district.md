
# Total number of cafes by district



<img width="736" height="259" alt="Ekran Resmi 2026-02-09 17 59 18" src="https://github.com/user-attachments/assets/a339fe2a-a4eb-4ae5-979e-deacba48cb59" />

  
## `mart.district_summary` Tablosu
`mart.district_summary` tablosu:
> İstanbul’daki cafe verisini **ilçe (district) seviyesinde özetlemek**
> ve dashboard + karar modellerinde kullanılacak
> **temel istatistikleri tek yerde toplamak** için oluşturdum.

Bu tablo ile ham veriyle **doğrudan görselleştirme yapılmasını engelledim** ,  performans, tutarlılık ve tekrar kullanılabilirlik sağladım.

---
## 1. `mart.district_summary` Nasıl Ürettim 

### 1.1 Kullandığım SQL Bloğu

```sql

WITH base AS (

    SELECT

        district,

        COUNT(*) AS cafe_count,

        AVG(rating) AS avg_rating,

        COUNT(*) FILTER (WHERE rating >= 4.5) AS high_quality_count,

        AVG(price_level) AS avg_price_level,

        SUM(COALESCE(user_ratings_total, 0)) AS total_reviews,

        AVG(COALESCE(user_ratings_total, 0)) AS avg_reviews

    FROM clean.cafes

    WHERE district IS NOT NULL AND district <> ''

    GROUP BY district

)

```
---
<img width="1307" height="683" alt="Ekran Resmi 2026-02-09 17 59 32" src="https://github.com/user-attachments/assets/f042ef3e-bae6-47b5-b453-58c060705f73" />


Aşağıda **her kolonun nereden geldiği ve hangi işlemi uygulandığımı** gösterdim.

---

### 2. `district`
**Kaynak:**

```sql

clean.cafes.district

```

**İşlem:**

* `WHERE district IS NOT NULL AND district <> ''`

* `GROUP BY district`

**Amaç:**
> Tüm analizleri **ilçe kırılımında** yapmak
---
### 2.1 `cafe_count`
**Kaynak:**
```sql

COUNT(*)

```
**Matematiksel Tanım:**
[\text{cafe_count}_d = \sum I(cafe \in d)]

**Ne Ölçer?**
* İlçedeki toplam cafe arzı
* Pazar doygunluğunun ham göstergesi
---


## 3. Bu Tablo Barı Chart’ta Nasıl Kullandım?
### “Total Number of Cafes by District” Bar Chart:

* **X-axis:** `district`

* **Y-axis:** `cafe_count`

* **Aggregation:** Yok (zaten özet tablo)

Bu nedenle:
> Grafikte ek bir SQL hesaplaması yapılmamıştır.
---
## 4. Analitik Yorum
> `district_summary`, İstanbul cafe pazarının **arz tarafını** ilçe bazında nicel olarak ortaya koyar.
Bu tablo sayesinde:
* hangi ilçelerde **yoğunlaşma** olduğu,
* hangi ilçelerde **görece boşluk** bulunduğu açıkça gözlemlenebilir.
