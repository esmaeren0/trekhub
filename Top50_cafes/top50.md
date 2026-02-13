
# TOP 50 CAFES

<img width="710" height="301" alt="Ekran Resmi 2026-02-13 10 15 36" src="https://github.com/user-attachments/assets/9d7f4b5d-f5de-4e70-a7b6-fe099b56be19" />


## 1. Bu tabloyu neden oluşturdum?

Bu çalışmada amacım, İstanbul’daki cafeleri **sadece ham rating’e bakarak değil**,  
**yorum sayısını, örneklem güvenilirliğini ve popülerliği birlikte dikkate alan**  
daha **adil ve istatistiksel olarak savunulabilir** bir yöntemle sıralamaktı.

Çünkü tek başına:

- 5.0 rating ama 3 yorumu olan bir cafe ile
    
- 4.6 rating ama 20.000 yorumu olan bir cafe
    
aynı şekilde değerlendirilmemelidir.

Bu nedenle “Top 50 Cafes” tablosunu, **Bayesian yaklaşım + log ölçekli popülerlik** kullanan bir skor modeliyle ürettim.

---

## 2. Superset’te gördüğüm tablo hangi kaynaktan geliyor?

<img width="1467" height="804" alt="Ekran Resmi 2026-02-13 10 16 31" src="https://github.com/user-attachments/assets/f178112e-8f12-4614-9eba-a988ece14eae" />



Bu görselleştirme **doğrudan** şu tablodan beslenmektedir:

```sql
mart.top50_cafes
```

Superset ayarında:

- Query mode: **Raw records**
    
- Order by: `rank ASC`
    
- Row limit: **50**
    

Superset tarafında **hiçbir hesaplama yoktur**.  
Sıralama, skor ve rank tamamen **SQL tarafında kilitlenmiştir**.

---

## 3. `mart.top50_cafes` tablosunun kaynağı nedir?

Bu tablo, doğrudan:

```sql
clean.cafes
```

tablosundan üretilmiştir.

`clean.cafes`:

- Ham veriden temizlenmiş
    
- Tipleri normalize edilmiş
    
- Geometrisi oluşturulmuş
    
- Analitik için güvenilir hale getirilmiş
    

tekil cafe kayıtlarını içerir.

---

## 4. Kullanılan kolonlar ve veri tipleri
Top 50 tablosunda yer alan ana kolonlar:

|Kolon|Tip|Anlam|
|---|---|---|
|`rank`|integer|Nihai sıralama|
|`place_id`|text|Cafe benzersiz ID|
|`name`|text|Cafe adı|
|`district`|text|İlçe|
|`rating`|double precision|Ham kullanıcı puanı|
|`user_ratings_total`|integer|Toplam yorum sayısı|
|`price_level`|integer|Fiyat seviyesi|
|`bayesian_rating`|numeric|Düzeltilmiş puan|
|`weighted_score`|numeric|Nihai sıralama skoru|
|`geom`|geometry|Cafe konumu|

Bu kolonlardan **`bayesian_rating` ve `weighted_score` bu tabloya özel olarak üretilmiştir.**

---

## 5. Bayesian Rating neden ve nasıl hesaplandı?

### 5.1 Neden Bayesian yaklaşım kullandım?

Ham rating, özellikle düşük yorum sayısına sahip cafelerde **yanıltıcıdır**.  
Bayesian yaklaşım, bu problemi şu şekilde çözer:

- Az yorumu olan cafeleri **genel ortalamaya yaklaştırır**
    
- Çok yorumu olan cafelerin **kendi rating’ine daha çok güvenir**
    

Bu yöntem, IMDb ve benzeri platformlarda da kullanılan **endüstri standardı** bir yaklaşımdır.

---

### 5.2 Kullanılan parametreler

```sql
SELECT AVG(rating) AS C, 50::numeric AS m
FROM clean.cafes
WHERE rating IS NOT NULL
```

- `C` → İstanbul genelindeki **ortalama rating**
    
- `m` → Minimum güven eşiği (50 yorum)
    

Bu değerler **sabit varsayım değildir**, veriden hesaplanmıştır.

---

### 5.3 Bayesian Rating formülü

```sql
bayesian_rating =
(
  (v / (v + m)) * R
  +
  (m / (v + m)) * C
)
```

SQL’de karşılığı:

```sql
(
 (user_ratings_total / (user_ratings_total + m)) * rating
 +
 (m / (user_ratings_total + m)) * C
)
```

Burada:

- `v` = cafe’nin yorum sayısı
    
- `R` = cafe’nin ham rating’i
    
- `C` = genel ortalama
    
- `m` = eşik değer
    

 Bu skor, **rating’i istatistiksel olarak stabilize eder**.

---

## 6. Log dönüşümü neden eklendi?

Bayesian rating, kaliteyi düzeltir.  
Ancak popülerliği tam yansıtmaz.

Bu yüzden ikinci bir bileşen ekledim:

```sql
LN(1 + user_ratings_total) AS log_reviews
```

### Neden log?

- Review sayıları **çok sağa çarpık** dağılır
    
- 10.000 yorum ile 50.000 yorum arasındaki fark  
    lineer olarak değil, **azalan marjinal etkiyle** hissedilmelidir
    

Log dönüşümü:

- Aşırı büyük değerleri baskılar
    
- Popülerliği kontrollü şekilde modele sokar
    

---

## 7. Nihai skor (`weighted_score`) nasıl hesaplandı?

```sql
weighted_score =
bayesian_rating + 0.15 * log_reviews
```

### Bu formülün mantığı:

- Ana belirleyici: **kalite (bayesian_rating)**
    
- Yardımcı sinyal: **popülerlik (log_reviews)**
    

0.15 katsayısı bilinçli olarak:

- Popülerliği ödüllendiren
    
- Ama kaliteyi gölgelemeyen
    

bir denge kurmak için seçildi.

 Bu katsayı **deneysel olarak test edilebilir**, sabit değildir.

---

## 8. Rank nasıl üretildi?

```sql
ROW_NUMBER() OVER (ORDER BY weighted_score DESC) AS rank
```

Bu sayede:

- Skorlar eşit olsa bile
    
- Sıralama deterministik olur
    

Superset’te görülen `rank`:

- Sonradan hesaplanmaz
    
- SQL tarafında **kilitlenmiş halidir**
    

---

## 9. Bu tablo analitik olarak ne anlatır?

Bu tablo şunu anlatır:

- İstanbul’da **kalitesi yüksek**
    
- Aynı zamanda **toplumsal olarak karşılık bulmuş**
    
- Yorum sayısı bakımından **güvenilir örnekleme sahip**
    

cafeleri gösterir.

Bu nedenle listede:

- Tarihi ve köklü cafeler
    
- Zincir ama güçlü markalar
    
- Yüksek rating + yüksek review kombinasyonu
    

öne çıkar.

---

## 10. Executive (yönetici) seviyesinde nasıl anlatırım?

> **“Bu liste, İstanbul’daki cafeleri yalnızca kullanıcı puanına göre değil, yorum sayısının güvenilirliğini ve popülerliği de hesaba katan istatistiksel bir sıralama modeliyle sunmaktadır.”**

- Üst sıralar: **kanıtlanmış kalite**
    
- Alt sıralar: **iyi ama görece daha az güvenilir örneklem**
    

Bu tablo:

- Öneri listesi
    
- Benchmark
    
- Rakip analizi
    
- Marka karşılaştırması
    

amaçlarıyla kullanılabilir.

---
