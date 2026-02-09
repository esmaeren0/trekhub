# 1.RAW DATA : CLEAN.CAFES TABLOSUNUN OLUŞTURULMASI

Bu projede yaptığım tüm analizlerin, dashboardların ve karar skorlarının temelini `clean.cafes` tablosu oluşturur.


-  `clean.cafes` tablosu benim için bir “ara tablo” değil, **analitik sistemin temelini oluşturur**.

---

## 1. Neden raw veriyi doğrudan kullanmadım?

Ham veri (`raw.istanbul_cafes_ultra_kopyasi`) analiz için ciddi problemler içeriyordu:

* Sayısal olması gereken alanlar **string**
* Boş değerler **boş string (`''`) olarak çekilmiş**
* İlçe bilgisi bazı kayıtlarda var, bazılarında yok
* Koordinatlar var ama **mekânsal analiz yapılabilecek formatta değil**
* `types` alanı tek kolon içinde, çok değerli ama **analitik olarak kullanılamaz halde**

Bu haliyle:

* Ortalama almak,
* Normalize etmek,
* İlçe karşılaştırmak,
* Harita üzerinde mesafe hesaplamak

**istatistiksel olarak yanlış veya yanıltıcı sonuçlar üretirdi.**

Bu yüzden önce veriyi **temizlemek değil**, **anlamını sabitlemek** gerekiyordu.

---

## 2. Temel yaklaşımım: 

* Bu kolon ileride hangi hesaplamalarda kullanılacak?
* NULL gelirse bunu **bilinmeyen** mi sayacağım, **sıfır** mı?
* Bu veri türü normalize edilecek mi?
* Mekânsal bir join’e girecek mi?
* Dashboard’da filtrelenecek mi?

---

## 3. Şema ve altyapı hazırlığı

```sql
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS clean;
CREATE SCHEMA IF NOT EXISTS mart;
CREATE EXTENSION IF NOT EXISTS postgis;
```

* `raw`: gelen veriye dokunmuyorum
* `clean`: verinin anlamını düzelttiğim katman
* `mart`: iş mantığı ve skorların üretildiği katman

Bu ayrımı yapmamın nedeni şu:

> **Hangi katmanda hata yaparsam, etkisi nereye kadar gider, bunu bilmeye çalıştım.**

---

## 4. clean.cafes tablosunu neden bu şekilde oluşturdum?

```sql
CREATE TABLE clean.cafes AS
SELECT
    NULLIF(BTRIM(place_id), '')::text AS place_id,
    NULLIF(BTRIM(name), '')::text AS name,
    rating::double precision AS rating,
    user_ratings_total::integer AS user_ratings_total,
    price_level::integer AS price_level,
    NULLIF(BTRIM(business_status), '')::text AS business_status,
    latitude::double precision AS latitude,
    longitude::double precision AS longitude,
    NULLIF(BTRIM(district), '')::text AS district,
    NULLIF(BTRIM(types), '')::text AS types,
    CASE
        WHEN latitude IS NOT NULL AND longitude IS NOT NULL
        THEN ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        ELSE NULL
    END AS geom
FROM raw.istanbul_cafes_ultra_kopyasi;
```

---

## 5. Boş string → NULL dönüşümü 

```sql
NULLIF(BTRIM(col), '')
```

Bunu neredeyse tüm text kolonlara uyguladım.

> Boş string, istatistiksel olarak **hiçbir şey ifade etmez**
> ama çoğu zaman yanlışlıkla “0” gibi davranır. Bu da analizlerde ortalamyı olduğundan düşük hesaplanmasına sebep olmaktadır.

Örnek:

* `user_ratings_total = ''`
* bunu `0` kabul edersem:

  * düşük verili ilçeler yapay şekilde cezalandırılır
  * ortalamalar düşer
  * fırsat skorları bozulur

Benim için:

* `NULL` = **bilmiyorum**
* `0` = **biliyorum ve gerçekten sıfır**

Bu ayrımı yaptım ilk olarak 

---

## 6. Sayısal kolonları dönüştürme

### rating → double precision

Bu bir **sürekli değişken**.
Normalize edilecek, ağırlıklandırılacak, ortalaması alınacak.

### user_ratings_total → integer

Bu bir **count** verisi.
Log-transform uygulayacağım için tipinin net olması şart.

### price_level → integer

Bu sayısal gibi görünse de **ordinal** bir değişken.
İleride bucket’lara ayıracağım ama ham halde integer kalmalı.

---

## 7. Geometri kolonunu neden burada ürettim?

```sql
ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
```

Bunu `mart` katmanına bırakabilirdim ama bilinçli olarak burada yaptım.

Çünkü:

* Bir cafe’nin **konumu**, kimliğinin bir parçası
* Mekânsal analizler (rekabet, grid, trafik) bunun üstüne kurulacak
* Geometriyi sonradan üretmek, tutarsızlık riskini artırır

EPSG:4326 seçmemin nedeni:

* Global standart
* Superset ve web haritalarıyla birebir uyumlu
* Geography dönüşümlerinde sorunsuz

---

## 8. İndeksleri neden burada tanımladım?

```sql
CREATE INDEX ix_clean_cafes_geom ON clean.cafes USING GIST (geom);
CREATE INDEX ix_clean_cafes_district ON clean.cafes (district);
```

Çünkü bu tablo:

* İlçe bazlı gruplamalara girecek
* Mekansal join’lerde kullanılacak
* Defalarca okunacak

İndeksi `mart` katmanında değil, burada tanımlamamın nedeni:

> clean.cafes’in **sadece doğru değil, hızlı da olması** gerekiyordu.

---

## 9. clean.cafe_types neden ayrı bir tablo?

`types` alanı tek kolonda çok değerli bilgi içeriyor ama:

```
"cafe, bakery, restaurant"
```

Bu haliyle:

* sayamam, oranlayamam, ilçe bazında kıyaslayamam. Bu yüzden **ilişki tablosu** oluşturdum:

```sql
CROSS JOIN LATERAL UNNEST(...)
```

Bu sayede:

* İlçe × kategori matrisi
* Hangi ilçede hangi cafe türü eksik
* Niş fırsat analizi yapılabilir hale geldi.

---

## 10. Bu tablo downstream’de neyi garanti ediyor 

`clean.cafes` için :

* rating her zaman sayısal
* NULL = bilinmiyor
* geom varsa WGS84
* district boşsa NULL
* types ham ama tutarlı

Bu sayede:

* Skorlar  bozulmuyor
* Dashboard’daki değişimlerin **veriden mi modelden mi** geldiğini ayırt edebiliyorum

---

## 11. özet

> Bu projede clean.cafes tablosu,
> ham veriyi sadece temizlemek için değil,
> **analitik olarak güvenilir hale getirmek için** oluşturulmuştur.
>
> Burada verilen her karar,
> sonraki fırsat skorlarının, rekabet analizlerinin
> ve açılış kararlarının doğruluğunu doğrudan etkiler.


