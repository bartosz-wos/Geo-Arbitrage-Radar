import json
import requests
import random
import time

def fetch_listings():
    return [
            {'address': 'Prosta 51, Warszawa', 'price_total': 950000, 'sqm': 50},
            {'address': 'Towarowa 22, Warszawa', 'price_total': 1200000, 'sqm': 60},
            {'address': 'Karolkowa 30, Warszawa', 'price_total': 850000, 'sqm': 45},
            {'address': 'Grzybowska 62, Warszawa', 'price_total': 1500000, 'sqm': 65},
            {'address': 'Giełdowa 4, Warszawa', 'price_total': 650000, 'sqm': 55},
    ]

def geocode_address(address):
    url = 'https://nominatim.openstreetmap.org/search'
    params = {'q': address, 'format': 'json', 'limit': 1}
    headers = {'User-Agent': 'GeoArbitrageRadar/1.0'}
    
    resp = requests.get(url, params=params, headers=headers)
    data = resp.json()

    if data:
        return [float(data[0]['lon']), float(data[0]['lat'])]
    return None

def process_data(listings):
    processed = []
    prices_per_sqm = []

    for it in listings:
        price_sqm = round(it['price_total'] / it['sqm'])
        prices_per_sqm.append(price_sqm)
        
        coords = geocode_address(it['address'])
        time.sleep(1)

        if coords:
            processed.append({
                'address': it['address'],
                'position': coords,
                'price': price_sqm,
                'isArbitrage': False
            })

    avg = sum(prices_per_sqm) / len(prices_per_sqm)

    for p in processed:
        diff = 1.0 - (p['price'] / avg)
        if diff > 0.25:
            p['isArbitrage'] = True

    return processed

if __name__ == '__main__':
    raw_data = fetch_listings()
    final_data = process_data(raw_data)

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
