import requests
import time
import csv
import json
from typing import Dict, Any, Optional

# ==================== CONFIGURATION ====================
API_KEY = "google api"
INPUT_FILE = "place_ids_istanbul_FULL.csv"
OUTPUT_FILE = "istanbul_cafes_ULTRA.csv"

# API rate limiting
REQUEST_DELAY = 0.15  # seconds between requests
BATCH_SAVE_SIZE = 100  # save every N records

# ==================== HELPER FUNCTIONS ====================

def get_place_details(place_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch comprehensive place details from Google Places API
    """
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    
    # Request ALL possible fields
    fields = [
        "place_id", "name", "formatted_address", "geometry",
        "rating", "user_ratings_total", "price_level",
        "types", "website", "formatted_phone_number",
        "international_phone_number", "opening_hours",
        "photos", "reviews", "url", "plus_code",
        "business_status", "vicinity", "adr_address",
        "utc_offset", "wheelchair_accessible_entrance"
    ]
    
    params = {
        "place_id": place_id,
        "fields": ",".join(fields),
        "key": API_KEY,
        "language": "tr"  # Turkish for better local data
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") == "OK":
            return data.get("result")
        else:
            print(f"⚠️  API Error for {place_id}: {data.get('status')}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed for {place_id}: {str(e)}")
        return None


def extract_district(address: str) -> str:
    """
    Extract district name from address
    """
    if not address:
        return ""
    
    # Common Istanbul district keywords
    districts = [
        "Kadıköy", "Beşiktaş", "Şişli", "Beyoğlu", "Fatih",
        "Üsküdar", "Bakırköy", "Sarıyer", "Ataşehir", "Maltepe",
        "Kartal", "Pendik", "Tuzla", "Beylikdüzü", "Avcılar",
        "Küçükçekmece", "Başakşehir", "Eyüpsultan", "Gaziosmanpaşa",
        "Sultangazi", "Esenler", "Güngören", "Bahçelievler",
        "Zeytinburnu", "Bayrampaşa", "Kağıthane", "Sultanbeyli"
    ]
    
    for district in districts:
        if district in address:
            return district
    
    return ""


def parse_opening_hours(hours_data: Optional[Dict]) -> Dict[str, str]:
    """
    Parse opening hours into structured format
    """
    result = {
        "is_open_now": "",
        "weekday_text": "",
        "periods_json": ""
    }
    
    if not hours_data:
        return result
    
    result["is_open_now"] = str(hours_data.get("open_now", ""))
    
    weekday_text = hours_data.get("weekday_text", [])
    if weekday_text:
        result["weekday_text"] = " | ".join(weekday_text)
    
    periods = hours_data.get("periods", [])
    if periods:
        result["periods_json"] = json.dumps(periods, ensure_ascii=False)
    
    return result


def extract_photo_references(photos_data: Optional[list]) -> str:
    """
    Extract photo references (max 5)
    """
    if not photos_data:
        return ""
    
    refs = [p.get("photo_reference", "") for p in photos_data[:5]]
    return " | ".join([r for r in refs if r])


def flatten_place_data(place: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten nested place data into CSV-friendly format
    """
    # Basic info
    row = {
        "place_id": place.get("place_id", ""),
        "name": place.get("name", ""),
        "rating": place.get("rating", ""),
        "user_ratings_total": place.get("user_ratings_total", ""),
        "price_level": place.get("price_level", ""),
        "business_status": place.get("business_status", ""),
    }
    
    # Location
    geometry = place.get("geometry", {})
    location = geometry.get("location", {})
    row["latitude"] = location.get("lat", "")
    row["longitude"] = location.get("lng", "")
    
    # Address
    row["formatted_address"] = place.get("formatted_address", "")
    row["vicinity"] = place.get("vicinity", "")
    row["district"] = extract_district(row["formatted_address"])
    
    # Contact
    row["phone"] = place.get("formatted_phone_number", "")
    row["international_phone"] = place.get("international_phone_number", "")
    row["website"] = place.get("website", "")
    row["google_maps_url"] = place.get("url", "")
    
    # Plus Code
    plus_code = place.get("plus_code", {})
    row["plus_code_global"] = plus_code.get("global_code", "")
    row["plus_code_compound"] = plus_code.get("compound_code", "")
    
    # Types
    types = place.get("types", [])
    row["types"] = ", ".join(types) if types else ""
    row["is_cafe"] = "cafe" in types
    row["is_restaurant"] = "restaurant" in types
    row["is_bar"] = "bar" in types
    
    # Opening Hours
    hours_data = place.get("opening_hours", {})
    hours_parsed = parse_opening_hours(hours_data)
    row["is_open_now"] = hours_parsed["is_open_now"]
    row["opening_hours"] = hours_parsed["weekday_text"]
    row["opening_hours_json"] = hours_parsed["periods_json"]
    
    # Photos
    row["photo_references"] = extract_photo_references(place.get("photos"))
    row["photo_count"] = len(place.get("photos", []))
    
    # Accessibility
    row["wheelchair_accessible"] = place.get("wheelchair_accessible_entrance", "")
    
    # UTC Offset
    row["utc_offset"] = place.get("utc_offset", "")
    
    return row


# ==================== MAIN SCRAPING LOGIC ====================

def main():
    print("=" * 60)
    print("🚀 ISTANBUL CAFES - ULTRA DATASET SCRAPER")
    print("=" * 60)
    
    # Read place_ids from CSV
    print(f"\n📂 Reading place IDs from: {INPUT_FILE}")
    place_ids = []
    
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            place_ids = [row["place_id"] for row in reader if row.get("place_id")]
    except FileNotFoundError:
        print(f"❌ ERROR: {INPUT_FILE} not found!")
        return
    except Exception as e:
        print(f"❌ ERROR reading file: {str(e)}")
        return
    
    total = len(place_ids)
    print(f"✅ Loaded {total} place IDs")
    
    if total == 0:
        print("❌ No place IDs found. Exiting.")
        return
    
    # Prepare output CSV
    fieldnames = [
        "place_id", "name", "rating", "user_ratings_total", "price_level",
        "business_status", "latitude", "longitude", "formatted_address",
        "vicinity", "district", "phone", "international_phone", "website",
        "google_maps_url", "plus_code_global", "plus_code_compound",
        "types", "is_cafe", "is_restaurant", "is_bar", "is_open_now",
        "opening_hours", "opening_hours_json", "photo_references",
        "photo_count", "wheelchair_accessible", "utc_offset"
    ]
    
    # Initialize CSV with headers
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
    
    print(f"\n📝 Output file initialized: {OUTPUT_FILE}")
    print(f"⏱️  Starting scraping with {REQUEST_DELAY}s delay...")
    print("=" * 60)
    
    # Scrape each place
    scraped_data = []
    success_count = 0
    fail_count = 0
    
    for idx, place_id in enumerate(place_ids, 1):
        print(f"\n[{idx}/{total}] Processing: {place_id}")
        
        # Fetch details
        place_data = get_place_details(place_id)
        
        if place_data:
            row = flatten_place_data(place_data)
            scraped_data.append(row)
            success_count += 1
            print(f"  ✅ {row.get('name', 'Unknown')} - {row.get('district', 'No district')}")
        else:
            fail_count += 1
            print(f"  ❌ Failed to fetch details")
        
        # Batch save
        if len(scraped_data) >= BATCH_SAVE_SIZE:
            with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerows(scraped_data)
            print(f"\n💾 Saved batch of {len(scraped_data)} records")
            scraped_data = []
        
        # Rate limiting
        time.sleep(REQUEST_DELAY)
    
    # Save remaining data
    if scraped_data:
        with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerows(scraped_data)
        print(f"\n💾 Saved final batch of {len(scraped_data)} records")
    
    # Final report
    print("\n" + "=" * 60)
    print("🎉 SCRAPING COMPLETED!")
    print("=" * 60)
    print(f"✅ Successfully scraped: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"📊 Success rate: {(success_count/total*100):.1f}%")
    print(f"📁 Output file: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
