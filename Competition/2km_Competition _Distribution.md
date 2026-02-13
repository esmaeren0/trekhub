

# 2km Competition Distribution


<img width="569" height="332" alt="Ekran Resmi 2026-02-13 09 20 03" src="https://github.com/user-attachments/assets/dd0ee1c1-e2b0-4d51-900e-69982dde4e82" />

---
> “**2 km çevrede X rakip var**” bilgisinin
> İstanbul genelinde **ne kadar yaygın** olduğunu gösterir.

Yani şuna cevap verir:

* “250+ rakip” **uç bir durum mu**, yoksa **norm mu?**
* “Düşük rekabet” dediğimiz şey **gerçekten nadir mi?**
* Cafe’lerin çoğu **hangi rekabet bandında** faaliyet gösteriyor?

---

## Kullanılan Dataset

**Superset Chart Source:**

```
mart.v_competition_distribution
```

Bu view, **tek tek cafelerden gelen 2km rekabet bilgisini**
analitik olarak **bucket (band) bazında özetlemek** için oluşturulmuştur.

---

## 1. Veri Nasıl Üretildi? (Kaynak → Görsel)

### 1.1 Temel Rekabet Hesabı: `mart.cafe_competition_2km`

Rekabet hesabının **en ham ve temel hali** burada üretilmiştir:

```sql
CREATE TABLE mart.cafe_competition_2km AS
SELECT
    a.place_id,
    a.name,
    a.district,
    a.geom,
    ST_Buffer(a.geom::geography, 2000)::geometry AS buffer_2km_geom,
    COUNT(b.place_id) - 1 AS competitors_within_2km
FROM clean.cafes a
JOIN clean.cafes b
  ON ST_DWithin(a.geom::geography, b.geom::geography, 2000)
GROUP BY a.place_id, a.name, a.district, a.geom;
```

### Açıklama

* Her cafe için **2 km yarıçaplı buffer** oluşturulur (12.6 km)
* Aynı yarıçap içindeki **diğer cafeler sayılır**
* `-1` çıkarılması:

  * Cafenin **kendini rakip saymaması** içindir

---

## 2. Rekabet Bandlarının Oluşturulması

Ham sayı (`competitors_within_2km`) doğrudan görselleştirilmez.
Bunun yerine **yorumlanabilir bantlara** ayrılır.

Bu işlem **`mart.v_cafe_competition_band`** view’inde yapılır.

### 2.1 Competition Band Tanımı

Mantık (SQL’den birebir):

```sql
CASE
  WHEN competitors_within_2km BETWEEN 0 AND 49 THEN '0–49'
  WHEN competitors_within_2km BETWEEN 50 AND 99 THEN '50–99'
  WHEN competitors_within_2km BETWEEN 100 AND 149 THEN '100–149'
  WHEN competitors_within_2km BETWEEN 150 AND 249 THEN '150–249'
  ELSE '250+'
END AS competition_band_label
```

### Neden Band Kullanıldı?

* Rekabet **lineer algılanmaz**
* 120 ile 130 rakip arasında fark yoktur
* Ama 40 → 200 **yapısal farktır**

Bu yüzden:

> Sayısal değeri değil, **rekabet seviyesi** analiz edilir

---

## 3. Dağılımın Üretilmesi: `mart.v_competition_distribution`

Bu view, **band bazında kaç cafe olduğunu** hesaplar.

Mantık:

```sql
SELECT
    competition_band_label,
    competition_band_order,
    COUNT(*) AS cafe_count
FROM mart.v_cafe_competition_band
GROUP BY competition_band_label, competition_band_order;
```

### Kolonlar

#### `competition_band_label`

* Görselde X ekseninde görülen etiket
* İnsan gözüyle okunabilir seviye tanımı

#### `competition_band_order`

* Superset’te doğru sıralama için kullanılır
* Metinsel sıralama hatasını önler

#### `cafe_count`

* İlgili rekabet bandında bulunan **toplam cafe sayısı**
* Grafikte Y ekseninde gösterilir

---

## 4. Superset’te Grafik Nasıl Kuruldu?

### Chart Tipi

* **Bar Chart**
  
<img width="1442" height="821" alt="Ekran Resmi 2026-02-13 09 19 28" src="https://github.com/user-attachments/assets/d334d191-a321-48c8-a45f-5a5635454586" />

### Query Ayarları

* **X-axis:** `competition_band_label`
* **Metric:** `SUM(cafe_count)`
* **Sort by:** `competition_band_order`
* **Row limit:** 10.000

---

## 5. Bu Grafik Ne Gösteriyor?

Grafikten açıkça görülenler:

* Cafelerin **çok büyük bir kısmı**
  **150+ rakip** olan bölgelerde yer alıyor
* `250+` bandı **en yüksek frekansa sahip**
* `0–49` ve `50–99` bandları **azınlıkta**

Bu, İstanbul’da cafe açmanın:

> **doğası gereği yüksek rekabetli** bir iş olduğunu gösterir.

---

## 6. Analitik Yorum

### Veri analisti yorumu

* “Yüksek rekabet” **istisna değil, normdur**
* Düşük rekabetli alanlar:

  * nadirdir
  * coğrafi olarak sınırlıdır
* Bu nedenle rekabet metriği:

  * tek başına **diskalifiye edici** olmamalıdır

---

### Executive düzeyde yorum

> İstanbul’da cafe açmak, çoğu zaman 150–250+ rakiple aynı pazarı paylaşmak anlamına gelir.
> Bu nedenle başarılı lokasyon stratejileri, **rekabetten kaçmak** yerine
> **rekabet içinde farklılaşmayı** hedeflemelidir.

---

## 7. Bu Görselin Projedeki Rolü

Bu grafik:

* Rekabet metriğinin **ölçeğini kalibre eder**
* Decision score’da kullanılan rekabet bileşeninin
  **neden ters (inverse) işlendiğini** açıklar
* “250 rakip çok mu?” sorusuna **veriye dayalı cevap** verir
