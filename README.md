
# 📍 TrekHub: İstanbul Mekân Veri Toplama ve İşleme Hattı (End-to-End Data Pipeline)

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Status](https://img.shields.io/badge/Status-Production_Ready-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

> **Geliştirici:** Esma Eren  
> **Proje Türü:** Veri Analizi, ETL Pipeline, Coğrafi Veri Analitiği  
> **Kapsam:** İstanbul, Türkiye Genelinde 14879 Mekân  

---

## 📋 İçindekiler

1. [Proje Özeti ve Vizyon](#-1-proje-özeti-ve-vizyon)
2. [Veri Toplama Yolculuğu: Denenen Yöntemler ve Karar Matrisi](#-2-veri-toplama-denenen-yöntemler-ve-karar-matrisi)
    - [Faz 1: OCR Tabanlı Scraping](#faz-1-ocr-tabanlı-scraping-görüntü-işleme)
    - [Faz 2: Selenium UI Scraping](#faz-2-selenium-ui-scraping-scroll--drag)
    - [Faz 3: TextSearch API](#faz-3-textsearch-api-kısıtlı-sonuç)
3. [Nihai Çözüm Mimarisi: Geo-Grid Based Nearby Search](#-3-nihai-çözüm-mimarisi-geo-grid-based-nearby-search)
4. [Veri Toplama ve Zenginleştirme Süreci (ETL)](#-4-veri-toplama-ve-zenginleştirme-süreci-etl)
5. [Dataset Sözlüğü (Data Dictionary)](#-5-dataset-sözlüğü-data-dictionary)
6. [Teknik Kurulum ve Kullanım](#-6-teknik-kurulum-ve-kullanım)
7. [Klasör Yapısı](#-7-klasör-yapısı)

---

## 🚀 1. Proje Özeti ve Vizyon

**TrekHub**, İstanbul'daki tüm kafe ve kahve mekânlarını tespit etmek, detaylı verilerini toplamak ve tekilleştirilmiş bir veri seti oluşturmak amacıyla geliştirilmiş kapsamlı bir veri analizi projesidir.

Proje boyunca **4 farklı yöntem** test edilmiş, başarısızlıklar analiz edilmiş ve sonuç olarak endüstri standardı olan **Geo-Grid Based Nearby Search** mimarisi uygulanarak tam kapsama (%100 coverage) sağlanmıştır.

Bu proje sayesinde:
* İstanbul'daki tüm kafeler harita üzerinde kör nokta kalmadan tespit edilmiş,
* Her mekan için **30+ özellik (feature)** toplanmış,
* Analiz ve makine öğrenmesi modellerine hazır **ULTRA Dataset** oluşturulmuştur.

---

## 🧪 2. Veri Toplama Yolculuğu: Denenen Yöntemler ve Karar Matrisi

Bu projenin nihai mimarisine ulaşmadan önce, farklı veri toplama stratejileri gerçek senaryolarda test edilmiştir. Aşağıda bu yöntemler ve neden elendikleri detaylandırılmıştır.

### Faz 1: OCR Tabanlı Scraping (Görüntü İşleme)
Google Maps arayüzünün ekran görüntüleri alınıp, **Tesseract OCR** ile metne dönüştürülmesi hedeflendi.

* **Kullanılan Araçlar:** Selenium, Tesseract OCR, Python Pillow, Regex.
* **Yöntem:** "Kafe" araması -> Screenshot -> Crop -> OCR -> Text Parsing.
<p align="center">
  
<img width="350" height="350" alt="maps_kafe" src="https://github.com/user-attachments/assets/2997e64b-c7e7-4fa8-9cac-c06525b48b5c" /> <img width="350" height="350" alt="maps_istanbul" src="https://github.com/user-attachments/assets/fa23535c-e6ea-446b-8b28-e8cbeb8e4dbb" />

  
<img width="150" height="350" alt="maps_kafe_panel" src="https://github.com/user-attachments/assets/72fac12c-1c45-45e5-a397-0cd6fa52cf7c" />

<img width="150" height="350" alt="maps_panel" src="https://github.com/user-attachments/assets/f0e509a4-95a9-48c6-a0a1-edf99434ac2d" />



  <img width="350" height="350" alt="Ekran Resmi 2025-11-19 19 42 15" src="https://github.com/user-attachments/assets/22cb940a-34ae-4f07-9524-2b1a8968bcc5" />



* **❌ Başarısızlık Nedeni:**
    * **Düşük Doğruluk:** OCR sayısal verileri (Rating: 4.8 -> 1.8) hatalı okuyordu.
    * **Sabit Olmayan Yapı:** Ekran çözünürlüğü değişince crop alanları bozuluyordu.
    * **Unique ID Sorunu:** `place_id` alınamadığı için veri tekrarı (duplication) engellenemedi.

### Faz 2: Selenium UI Scraping (Scroll + Drag)
Web tarayıcısını kod ile yöneterek harita üzerinde gezinme ve HTML verisini toplama yöntemi.

* **Kullanılan Araçlar:** Selenium WebDriver, Otomatik Scroll.
* **Yöntem:** Haritayı sürükle -> Sol paneli scroll et -> HTML elementlerini topla.

<p align="center">

<img width="2940" height="1418" alt="scroll" src="https://github.com/user-attachments/assets/7ca8a2c3-f618-4b47-b259-7d7a84f01225" />

</p>

* **❌ Başarısızlık Nedeni:**
    * **Anti-Bot Koruması:** Google CAPTCHA ve IP bloklamaları.
    * **Performans:** Tarayıcı tabanlı olduğu için çok yavaştı.
    * **Bakım Maliyeti:** HTML yapısı (class isimleri) sürekli değiştiği için kod kararsızdı.

### Faz 3: TextSearch API (Kısıtlı Sonuç)
Google Places API `TextSearch` endpoint'i kullanılarak yapılan aramalar.

* **Yöntem:** `query="Cafe in Istanbul"` sorguları.
* **❌ Başarısızlık Nedeni:**
    * **Limit:** Google API tek sorguda maksimum **60 sonuç** döndürür.
    * **Kapsam:** İstanbul'daki 20.000+ kafenin sadece %5'ine erişilebildi (Low Coverage).

---

## 🟩 3. Nihai Çözüm Mimarisi: Geo-Grid Based Nearby Search

Veri bütünlüğünü (%100 Coverage) sağlamak için **Coğrafi Izgara (Geo-Grid)** algoritması geliştirilmiştir. Bu yöntem, profesyonel veri sağlayıcıların endüstri standardıdır.

### ⚙️ Algoritma Mantığı

1.  **Boundary Box (Sınır Belirleme):** İstanbul'un coğrafi sınırları (Kuzey-Güney-Doğu-Batı) belirlendi.
2.  **Grid Generation (Izgara Bölme):** Bu alan, her biri **1500 metre yarıçaplı** yaklaşık 5000 adet kare hücreye bölündü.
3.  **Hücresel Tarama:** Her hücrenin merkezi için Google Places API `/nearbysearch` isteği gönderildi.
4.  **Deduplication (Tekilleştirme):** Google'ın benzersiz `place_id` anahtarı kullanılarak mükerrer kayıtlar temizlendi.

> **Sonuç:** Bu mimari ile **14879 tekil mekân** başarıyla tespit edildi.

---

## 🔄 4. Veri Toplama ve Zenginleştirme Süreci (ETL)

Sistem, ham verinin API'den alınıp, temizlenerek analize hazır hale getirilmesi için 3 aşamalı bir ETL süreci işletir.

### Adım 1: Discovery (Keşif)
* **API:** `/place/nearbysearch`
* **Amaç:** Mekanların `place_id` ve konum verisini toplamak.
* **Çıktı:** `istanbul_cafes_raw.csv`

### Adım 2: Enrichment (Zenginleştirme)
* **API:** `/place/details`
* **Amaç:** Her `place_id` için detaylı veri (telefon, saatler, fiyat vb.) çekmek.
* **Çıktı:** `istanbul_cafes_details.json`

### Adım 3: Cleaning & Transformation (Temizleme)
* **Araç:** Pandas (Henüz Yapılmadı)
* **İşlemler:**
    * Zincir mağazaların etiketlenmesi.
    * Rating ve yorum sayılarının tip dönüşümü.
    * `Quality_Score` hesaplanması.
    * Adres ayrıştırma (İlçe/Mahalle).

---


## 📊 5. Dataset Sözlüğü (Data Dictionary)

Oluşturulan `istanbul_cafes_ULTRA.csv` dosyası, analiz ve modelleme için zenginleştirilmiş **30+ kolon** içerir. Aşağıda veri setindeki gerçek kolon isimleri ve açıklamaları yer almaktadır:

### 🆔 Kimlik ve Lokasyon
| Kolon Adı | Veri Tipi | Açıklama |
| :--- | :--- | :--- |
| `place_id` | String | Google tarafından verilen benzersiz kimlik (Primary Key) |
| `name` | String | İşletmenin resmi adı |
| `formatted_address` | String | Tam açık adres |
| `vicinity` | String | Kısa adres / Muhit bilgisi |
| `district` | String | Ayrıştırılmış İlçe Bilgisi (Örn: Kadıköy, Avcılar) |
| `latitude` | Float | Enlem koordinatı |
| `plus_code_global` | String | Google Plus Code (Global Konum Kodu) |
| `plus_code_compound`| String | Google Plus Code (Bölgesel) |
| `Maps_url` | String | Google Haritalar linki |

### ⭐ Puanlama ve Durum
| Kolon Adı | Veri Tipi | Açıklama |
| :--- | :--- | :--- |
| `rating` | Float | Kullanıcı puan ortalaması (1.0 - 5.0) |
| `user_ratings_total` | Int | Toplam yorum sayısı |
| `price_level` | Float | Fiyat seviyesi (Bilinmiyorsa boş) |
| `business_status` | String | İşletme durumu (OPERATIONAL, CLOSED_TEMPORARILY) |
| `photo_count` | Int | Mekana ait toplam fotoğraf sayısı |

### 📞 İletişim
| Kolon Adı | Veri Tipi | Açıklama |
| :--- | :--- | :--- |
| `phone` | String | Yerel telefon numarası |
| `international_phone`| String | Uluslararası formatta telefon (+90...) |
| `website` | URL | İşletmenin web sitesi veya sosyal medya linki |

### 🏷️ Özellikler ve Kategoriler
| Kolon Adı | Veri Tipi | Açıklama |
| :--- | :--- | :--- |
| `types` | String | Mekan etiketleri (cafe, food, point_of_interest...) |
| `is_cafe` | Boolean | Kafe mi? (True/False) |
| `is_restaurant` | Boolean | Restoran mı? (True/False) |
| `is_bar` | Boolean | Bar mı? (True/False) |
| `wheelchair_accessible`| Boolean | Tekerlekli sandalye erişimi var mı? |

### 🕒 Zaman Bilgileri
| Kolon Adı | Veri Tipi | Açıklama |
| :--- | :--- | :--- |
| `is_open_now` | Boolean | Şu an açık mı? |
| `opening_hours` | String | Haftalık çalışma saatleri (Metin formatında) |
| `opening_hours_json` | JSON | Çalışma saatlerinin yapısal veri hali |
| `utc_offset` | Int | Saat dilimi farkı (Dakika cinsinden) |

<p align="center">
<img width="977" height="727" alt="Ekran Resmi 2025-11-19 20 05 33" src="https://github.com/user-attachments/assets/fd0b76f9-a87b-4512-80d5-569bfa08ff58" />

</p>

---

## 🛠 6. Teknik Kurulum ve Kullanım

### Gereksinimler
* Python 3.8+
* Google Cloud API Key (Places API Enabled)

