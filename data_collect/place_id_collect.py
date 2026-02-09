import requests
import time
import csv

API_KEY = "google api"  
SEARCH_QUERIES = [
    "cafe in Istanbul",
    "coffee shop in Istanbul",
    "kafe İstanbul",
    "kahveci İstanbul"
]

BASE_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

place_ids = set()

for query in SEARCH_QUERIES:
    print(f"Sorgu: {query}")
    params = {
        "query": query,
        "key": API_KEY,
        "region": "tr"
    }
    next_page_token = None

    while True:
        if next_page_token:
            params["pagetoken"] = next_page_token
            time.sleep(2)  

        resp = requests.get(BASE_URL, params=params)
        data = resp.json()

        for result in data.get("results", []):
            pid = result.get("place_id")
            if pid:
                place_ids.add(pid)

        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break

print(f"Toplam benzersiz place_id sayısı: {len(place_ids)}")

# CSV'ye kaydet
with open("place_ids_istanbul_cafes.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["place_id"])
    for pid in place_ids:
        w.writerow([pid])

print("✅ place_ids_istanbul_cafes.csv oluşturuldu.")
