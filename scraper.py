import json
import requests
import random
import time

def fetch_listings():
    return [
        {'address': 'Prosta 51, Warszawa', 'price_total': 950000, 'sqm': 50},
        {'address': 'Towarowa 22, Warszawa', 'price_total': 1200000, 'sqm': 60},
        {'address': 'Grzybowska 62, Warszawa', 'price_total': 1500000, 'sqm': 65},
        {'address': 'Giełdowa 4, Warszawa', 'price_total': 650000, 'sqm': 55},
        {'address': 'Kolejowa 47, Warszawa', 'price_total': 1100000, 'sqm': 50},
        {'address': 'Złota 44, Warszawa', 'price_total': 4500000, 'sqm': 100},
        {'address': 'Emilii Plater 14, Warszawa', 'price_total': 2000000, 'sqm': 60},
        {'address': 'Hoża 50, Warszawa', 'price_total': 1800000, 'sqm': 55},
        {'address': 'Koszykowa 30, Warszawa', 'price_total': 800000, 'sqm': 60},
        {'address': 'Jana Kazimierza 50, Warszawa', 'price_total': 800000, 'sqm': 50},
        {'address': 'Ordona 5, Warszawa', 'price_total': 900000, 'sqm': 55},
        {'address': 'Sowińskiego 25, Warszawa', 'price_total': 750000, 'sqm': 50},
    ]

def geocode_address(address):
    url = 'https://nominatim.openstreetmap.org/search'
    params = {'q': address, 'format': 'json', 'limit': 1}
    headers = {'User-Agent': 'GeoArbitrageRadar/1.0'}
    try:
        resp = requests.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        if data: return [float(data[0]['lon']), float(data[0]['lat'])]
    except Exception as e:
        print(f'Error: {e}')

    return None

def process_data(listings):
    processed = []

    for it in listings:
        coords = geocode_address(it['address'])
        time.sleep(1)
        if coords:
            processed.append({
                'address': it['address'],
                'position': coords,
                'price': round(it['price_total'] / it['sqm'])
            })

    return processed

if __name__ == '__main__':
    final_data = process_data(fetch_listings())

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
