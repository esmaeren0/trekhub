
# 📊 Big Number KPI Dashboard

<img width="1005" height="81" alt="Ekran Resmi 2026-02-09 17 30 40" src="https://github.com/user-attachments/assets/7c6e0874-f477-4442-bac7-466b0adde228" />


## 1. Amaç ve Kapsam
İstanbul genelindeki cafe verisinin:

* ölçeğini (data size),
* kalite seviyesini (rating),
* kullanıcı etkileşimini (reviews),
* operasyonel geçerliliğini (business status) **tanımlayıcı istatistikler (descriptive statistics)** aracılığıyla özetlemek amacıyla oluşturdum.

Bu KPI’lar:

* ileri seviye modelleme için **ön koşul (data sanity check)** ve dashboard’un geri kalanındaki analizlerin **istatistiksel olarak anlamlı olup olmadığını** doğrulamak için kullandım.
---
## 2. Veri Kaynağı

Tüm Big Number KPI’lar, aşağıdaki tabloya dayanmaktadır:

```sql

clean.cafes

```
Bu tablo:
* Google Places kaynaklı ham verinin
* temizlenmiş, normalize edilmiş ve
* PostGIS uyumlu hale getirilmiş halidir.
---

## 3. KPI Hesaplama Altyapısı

Big Number KPI’ları, aşağıdaki SQL sorgusu ile oluşturarak tek satırlık özet tablo üzerinden ürettim.

```sql

mart.kpi_overview

```

Bu tablo ile tüm KPI’ları **tek bir snapshot** olarak sakladım ve dashboard performansını artırmayı amaçladım.

---

## 4. KPI Bazlı Detaylı Açıklamalar

### 4.1 Total Cafes in Istanbul

<img width="157" height="72" alt="Ekran Resmi 2026-02-09 17 30 58" src="https://github.com/user-attachments/assets/1aed9d3d-41fc-4f90-961b-2894a3d35275" />

### superset chart ayarları :
<img width="1305" height="706" alt="Ekran Resmi 2026-02-09 17 37 58" src="https://github.com/user-attachments/assets/86b57515-d411-48f2-8524-4c111dbc8fde" />

**Gösterilen Değer:** `14,880`
#### Kullanılan SQL

```sql

COUNT(*) AS total_cafes

```

#### Matematiksel Tanım

Bu metrik, veri setindeki toplam gözlem sayısını ifade etmektedir.

[ N = \text{toplam cafe sayısı} ]

#### İstatistiksel Anlam

* Bu değer, analiz evreninin büyüklüğünü (sample size) temsil eder.
* Tüm ortalama ve oran hesaplamalarının güvenilirliği doğrudan bu büyüklüğe bağlıdır.

#### Analitik Yorum

> 14.880 cafe gözlemi, İstanbul ölçeğinde istatistiksel olarak anlamlı ve genellenebilir analizler yapılabilmesi için yeterli büyüklükte bir veri seti sunmaktadır.
---
### 4.2 Average Rating
<img width="156" height="73" alt="Ekran Resmi 2026-02-09 17 31 19" src="https://github.com/user-attachments/assets/7f0074ac-4fbb-4b98-814a-b8a8cc912a37" />

**Gösterilen Değer:** `4.24`


<img width="1302" height="701" alt="Ekran Resmi 2026-02-09 17 41 26" src="https://github.com/user-attachments/assets/6bcb4d98-e35d-44b1-ad05-9eadc3d602f9" />


#### Kullanılan SQL

```sql

AVG(rating) AS avg_rating

```
#### Matematiksel Tanım

Aritmetik ortalama kullanarak hesaplamayı yaptım.

[\bar{x} = \frac{1}{n} \sum_{i=1}^{n} x_i]

Burada:

* (x_i): her bir cafenin rating değeri

* (n): rating bilgisi bulunan cafe sayısı

#### İstatistiksel Anlam

* Ortalama rating, kullanıcıların **genel memnuniyet seviyesini** ölçer.
* Likert tipi (1–5) bir ölçek olduğu için ortalama değer yorumlanabilirdir.

#### Bilinen Kısıt

* Review sayısı dikkate alınmaz.

* Az sayıda yoruma sahip cafeler ile çok sayıda yoruma sahip cafeler eşit ağırlıktadır.

  #### Analitik Yorum
> Ortalama rating değerinin 4.24 olması, İstanbul’daki cafelerin genel olarak yüksek kullanıcı memnuniyetine sahip olduğunu göstermektedir.
---

### 4.3 High Rating Cafes (Rating ≥ 4.5)
<img width="241" height="74" alt="Ekran Resmi 2026-02-09 17 31 45" src="https://github.com/user-attachments/assets/d157f7b1-3f71-466a-a5ea-fd4eff3e7dc5" />

**Gösterilen Değer:** `5.38k`

<img width="1307" height="705" alt="Ekran Resmi 2026-02-09 17 41 52" src="https://github.com/user-attachments/assets/303d1bd4-8f62-4532-9d93-b0f32da7453d" />


#### Kullanılan SQL
```sql

COUNT(*) FILTER (WHERE rating >= 4.5)

```
#### Matematiksel Tanım
Bu metrik, eşik tabanlı bir sayım işlemidir:
[\sum I(rating_i \ge 4.5)]

* (I(\cdot)): gösterge (indicator) fonksiyonudur.

#### İstatistiksel Anlam

* Rating dağılımının **üst kuyruk (right tail)** büyüklüğünü temsil eder.
* Yüksek kalite segmentinin pazardaki payını gösterir.

#### Analitik Yorum
> İstanbul’da yaklaşık 5.380 cafe, kullanıcı değerlendirmelerine göre yüksek kalite segmentinde yer almaktadır. Bu durum pazarda güçlü bir kalite rekabeti olduğunu göstermektedir.
---
### 4.4 Average User Reviews

<img width="234" height="68" alt="Ekran Resmi 2026-02-09 17 31 52" src="https://github.com/user-attachments/assets/54c5d65a-af75-418d-80b2-41c8706329ec" />

**Gösterilen Değer:** `205.43`

<img width="1302" height="702" alt="Ekran Resmi 2026-02-09 17 42 13" src="https://github.com/user-attachments/assets/a840dbdc-1c76-4d81-9b46-3b9b20953b97" />


#### Kullanılan SQL
```sql

AVG(user_ratings_total) AS avg_user_ratings_total

```
#### Matematiksel Tanım
Aritmetik ortalama kullanarak hesapladım.
#### İstatistiksel Özellik

* Review sayıları genellikle **sağa çarpık (heavy-tailed)** dağılım gösterir.
* Bu nedenle ortalama, yüksek etkileşimli cafelerden etkilenir.

#### Bu KPI Ne Ölçer?
* Kullanıcı etkileşiminin genel seviyesini
* Rating verilerinin güvenilirlik zeminini
#### Analitik Yorum
> Cafe başına ortalama 205 kullanıcı yorumu bulunması, veri setindeki rating değerlerinin büyük ölçüde kullanıcı etkileşimine dayandığını ve güvenilir olduğunu göstermektedir.

---
### 4.5 Operational Businesses (%)
<img width="156" height="73" alt="Ekran Resmi 2026-02-09 17 31 58" src="https://github.com/user-attachments/assets/54df5f7c-2c4a-4366-8a76-30ffbc5c289a" />

**Gösterilen Değer:** `%97.91`
<img width="1303" height="676" alt="Ekran Resmi 2026-02-09 17 42 44" src="https://github.com/user-attachments/assets/861c2374-07df-4f45-816b-a49921c732bd" />

#### Kullanılan SQL
```sql

ROUND( 100.0 * COUNT(*) FILTER (WHERE business_status ILIKE '%OPERATIONAL%')/ COUNT(*),2)

```
#### Matematiksel Tanım
Bir oran (proportion) hesaplaması: 
[\text{Operational %} =\frac{\text{Operational Cafes}}{\text{Total Cafes}} \times 100]
#### İstatistiksel Anlam
* Bu metrik, veri setinin **güncellik ve operasyonel doğruluk** seviyesini ölçer.
#### Analitik Yorum
> Cafelerin %97.91’inin aktif durumda olması, analiz edilen veri setinin büyük ölçüde güncel ve operasyonel gerçekliği yansıttığını göstermektedir.
---
## 5. Genel Değerlendirme (Big Number KPI’lar)

Bu dashboard bölümünde **temel tanımlayıcı istatistikler** tercih ettim.
Bu tercihi veri kalitesini doğrulamak,ileri analizler için sağlam bir zemin oluşturmak amacıyla yaptım.


  
