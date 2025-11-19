import requests
import time
import csv

API_KEY = "AIzaSyDOwMT8BDo-u9s-782xwSWWsUVIrIoyQLo"  # Google Places API key

# İstanbul koordinat sınırları
LAT_MIN = 40.80
LAT_MAX = 41.30
LON_MIN = 28.50
LON_MAX = 29.50

STEP = 0.01   # 0.01 = hızlı, 0.008 = daha detaylı, 0.005 = ultra detay
RADIUS = 1500  # 1500 metre yakınlık taraması

place_ids = set()

def nearby_search(lat, lon):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lon}",
        "radius": RADIUS,
        "type": "cafe",
        "key": API_KEY
    }

    results = []

    while True:
        resp = requests.get(url, params=params)
        data = resp.json()

        for place in data.get("results", []):
            pid = place.get("place_id")
            if pid:
                results.append(pid)

        next_page_token = data.get("next_page_token")
        if next_page_token:
            time.sleep(2)
            params["pagetoken"] = next_page_token
        else:
            break

    return results

# Grid üretimi
lat_values = []
lon_values = []

lat = LAT_MIN
while lat <= LAT_MAX:
    lat_values.append(round(lat, 4))
    lat += STEP

lon = LON_MIN
while lon <= LON_MAX:
    lon_values.append(round(lon, 4))
    lon += STEP

total_cells = len(lat_values) * len(lon_values)
print(f"Toplam taranacak hücre sayısı: {total_cells}")

cell_counter = 0

# Grid taraması
for lat in lat_values:
    for lon in lon_values:
        cell_counter += 1
        print(f"[{cell_counter}/{total_cells}] Hücre taranıyor → {lat}, {lon}")

        try:
            pids = nearby_search(lat, lon)
            for pid in pids:
                place_ids.add(pid)
        except Exception as e:
            print("Hata:", e)

        time.sleep(0.2)

# Sonuçları kaydetme
output_file = "place_ids_istanbul_FULL.csv"
with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["place_id"])
    for pid in place_ids:
        writer.writerow([pid])

print("\n=====================================")
print(f"Tarama tamamlandı!")
print(f"Toplam benzersiz place_id: {len(place_ids)}")
print(f"Kaydedilen dosya: {output_file}")
print("=====================================\n")
