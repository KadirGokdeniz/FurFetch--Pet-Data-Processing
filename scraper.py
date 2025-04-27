# scraper.py - Web kazıma işlemleri
from bs4 import BeautifulSoup
import requests
import json
from config import CONFIG
import time

class PetlebiScraper:
    def __init__(self, base_url=None, max_pages=None):
        self.base_url = base_url or CONFIG['scraping']['base_url']
        self.max_pages = max_pages or CONFIG['scraping']['max_pages']
        self.products = []
        
    def scrape_all_pages(self):
        """Tüm sayfaları tarar"""
        for page in range(1, self.max_pages + 1):
            try:
                if page == 1:
                    url = self.base_url
                else:
                    url = f"{self.base_url}?page={page}"
                
                print(f"Taranıyor: Sayfa {page}/{self.max_pages}")
                
                success = self.scrape_page(url)
                if not success:
                    print(f"Sayfa {page} taranamadı, devam ediliyor...")
                
                # Sunucuya aşırı yüklenmemek için bekleme
                time.sleep(1)
            except Exception as e:
                print(f"Sayfa {page} taranırken hata: {e}")
        
        return self.products
    
    def scrape_page(self, url):
        """Belirli bir sayfayı tarar"""
        try:
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Sayfa alınamadı. Durum kodu: {response.status_code}")
                return False
                
            html_text = response.text
            soup = BeautifulSoup(html_text, 'lxml')
            products = soup.find_all('div', class_='col-lg-4 col-md-4 col-sm-6 search-product-box')
            
            for product in products:
                product_data = self.extract_product_data(product)
                if product_data:
                    # Ürün detaylarını almak için yeni sayfa
                    try:
                        detailed_data = self.get_product_details(product_data['url'])
                        product_data.update(detailed_data)
                        self.products.append(product_data)
                    except Exception as e:
                        print(f"Ürün detayları alınamadı: {e}")
            
            return True
        except Exception as e:
            print(f"Sayfa tarama hatası: {e}")
            return False
    
    def extract_product_data(self, product_element):
        """Ürün elementinden temel bilgileri çıkarır"""
        try:
            more_info = product_element.find('div', class_='card-body pb-0 pt-2 pl-3 pr-3')
            product_url = more_info.a['href']
            product_dictionary = json.loads(more_info.a['data-gtm-product'])
            
            return {
                "url": product_url,
                "name": product_dictionary["name"],
                "price": product_dictionary["price"],
                "stock": product_dictionary["dimension2"],
                "category": product_dictionary["category"].split('>')[-1],
                "id": product_dictionary["id"],
                "brand": product_dictionary["brand"],
                "sku": ""
            }
        except Exception as e:
            print(f"Ürün verisi çıkarma hatası: {e}")
            return None
    
    def get_product_details(self, product_url):
        """Ürün detay sayfasından ek bilgiler alır"""
        try:
            response = requests.get(product_url)
            if response.status_code != 200:
                return {}
                
            html_text = response.text
            soup = BeautifulSoup(html_text, 'lxml')
            
            # Varsayılan değerler
            product_details = {
                "barcode": "",
                "description": "",
                "image": ""
            }
            
            # Barkod
            info = soup.find_all('div', class_='tab-pane active show read-more-box', id="hakkinda")
            for div in info:
                barcode_divs = div.find_all('div', class_='row mb-2')
                for barcode_div in barcode_divs:
                    barcode = barcode_div.find('div', class_='col-2 pd-d-t')
                    if barcode and barcode.string == "BARKOD":
                        barcode_value = barcode_div.find('div', class_='col-10 pd-d-v')
                        product_details["barcode"] = barcode_value.text.strip() if barcode_value else ""
                
                # Açıklama
                spans = div.find('span', id='productDescription')
                if spans:
                    description_list = []
                    for i, span in enumerate(spans):
                        if i == 1:  # İkinci öğe açıklama olarak belirtilmiş
                            description = span.text.strip().replace('\n', ' ')
                            product_details["description"] = description
            
            # Görsel
            info2 = soup.find('div', class_='col-md-6 col-sm-5')
            if info2 and info2.a and 'href' in info2.a.attrs:
                product_details["image"] = info2.a['href']
            
            return product_details
        except Exception as e:
            print(f"Ürün detayları alınamadı: {e}")
            return {}
    
    def save_to_json(self, filename):
        """Ürünleri JSON dosyasına kaydeder"""
        try:
            with open(filename, "w", encoding="utf-8") as json_file:
                json.dump(self.products, json_file, ensure_ascii=False, indent=2)
            print(f"{len(self.products)} ürün {filename} dosyasına kaydedildi")
            return True
        except Exception as e:
            print(f"JSON kaydetme hatası: {e}")
            return False
