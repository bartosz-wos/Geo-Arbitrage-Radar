import json
import time
import random
import re
from bs4 import BeautifulSoup
import requests
from playwright.sync_api import sync_playwright

LIMIT_OFERT = 20 

def fetch_offers():
    offers = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        main_url = "https://www.olx.pl/nieruchomosci/mieszkania/sprzedaz/warszawa/?search%5Border%5D=created_at%3Adesc"
        
        try:
            page.goto(main_url, timeout=60000)
            
            try:
                page.wait_for_selector('button#onetrust-accept-btn-handler', timeout=3000)
                page.click('button#onetrust-accept-btn-handler')
                time.sleep(1)
            except:
                pass
                
            for _ in range(4):
                page.mouse.wheel(0, 1500)
                time.sleep(1.5)
            
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if 'oferta' in href and 'otodom.pl' not in href and 'konto' not in href:
                    if href.startswith('/'):
                        href = "https://www.olx.pl" + href
                    clean_link = href.split('?')[0]
                    if clean_link not in links:
                        links.append(clean_link)
             
            for i, link in enumerate(links[:LIMIT_OFERT]):
                try:
                    page.goto(link, timeout=30000)
                    page.wait_for_timeout(1500) 
                    
                    sub_html = page.content()
                    sub_soup = BeautifulSoup(sub_html, 'html.parser')
                    full_text = sub_soup.get_text(separator=' | ', strip=True)
                    
                    title_elem = sub_soup.find('h1')
                    title = title_elem.get_text(strip=True) if title_elem else "OLX Offer"
                    
                    prices = re.findall(r'([\d\s\xa0]+)\s*zł', full_text, re.IGNORECASE)
                    valid_prices = []
                    for p_str in prices:
                        clean_p = p_str.replace(' ', '').replace('\xa0', '')
                        if clean_p.isdigit():
                            valid_prices.append(float(clean_p))
                    price_total = max(valid_prices) if valid_prices else 0
                    
                    sqm_match = re.search(r'Powierzchnia[^>]*?([\d\.,]+)\s*m', sub_html, re.IGNORECASE) or re.search(r'([\d\.,]+)\s*m', full_text, re.IGNORECASE)
                    sqm = float(sqm_match.group(1).replace(',', '.')) if sqm_match else 0
                    
                    location = "Warszawa"
                    loc_match = re.search(r'Warszawa,\s*([A-Za-zżźćńółęąśŻŹĆĄŚĘŁÓŃ\-]+)', full_text)
                    if loc_match:
                        district = loc_match.group(1).strip()
                        location = f"Warszawa, {district}"
                        
                        street_match = re.search(r'(?i)(?:ul\.|ulica|ulicy)\s+([^.,\n]{2,35}?\d+[a-zA-Z]?)', full_text)
                        if street_match:
                            street_name = street_match.group(1).strip()
                            if len(street_name) < 40:
                                location = f"Warszawa, {district}, ul. {street_name}"
                    
                    if 250000 < price_total < 4000000 and 15 < sqm < 150:
                        offers.append({
                            'title': title,
                            'address': location,
                            'price_total': price_total,
                            'sqm': sqm,
                            'url': link 
                        })
                            
                except Exception as sub_e:
                    print(f"   Error {sub_e}.")
                
                time.sleep(1.5) 

        except Exception as e:
            print(f"Error {e}")
        finally:
            browser.close()
            
    return offers

def geocode(address):
    url = 'https://nominatim.openstreetmap.org/search'
    search_query = address if "Warszawa" in address else f"{address}, Warszawa"
    params = {'q': search_query, 'format': 'json', 'limit': 1}
    headers = {'User-Agent': 'GeoArbitrageRadar/Deep11'}
    
    try:
        resp = requests.get(url, params=params, headers=headers)
        data = resp.json()
        if data and len(data) > 0:
            lon = float(data[0]['lon']) 
            lat = float(data[0]['lat'])
            
            if "ul." in address:
                lon += random.uniform(-0.001, 0.001)
                lat += random.uniform(-0.001, 0.001)
            else:
                lon += random.uniform(-0.015, 0.015)
                lat += random.uniform(-0.010, 0.010)
                
            return [lon, lat]
    except:
        pass
    return None

def process_data(listings):
    if not listings:
        return []
    processed = []
    for idx, it in enumerate(listings):
        coords = geocode(it['address'])
        time.sleep(1.1)
        if coords:
            processed.append({
                'title': it['title'],
                'address': it['address'],
                'position': coords,
                'price': round(it['price_total'] / it['sqm']),
                'url': it['url'] 
            })
    return processed

if __name__ == '__main__':
    final_data = process_data(fetch_offers())
    
    if final_data:
        with open('data/data.json', 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        print(f'\nFound {len(final_data)} offers')
    else:
        print('Nothing found')
