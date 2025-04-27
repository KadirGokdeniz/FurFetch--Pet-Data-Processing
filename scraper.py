# scraper.py - İyileştirilmiş web kazıma sınıfı
from bs4 import BeautifulSoup
import requests
import json
import time
from config import CONFIG
from logger import Logger
from error_handler import ErrorHandler

class PetlebiScraper:
    """Petlebi web sitesinden ürün verilerini çeken sınıf"""
    
    def __init__(self, base_url=None, max_pages=None):
        """Scraper'ı başlat
        
        Args:
            base_url: Taranacak web sitesinin temel URL'si
            max_pages: Taranacak maksimum sayfa sayısı
        """
        self.base_url = base_url or CONFIG['scraping']['base_url']
        self.max_pages = max_pages or CONFIG['scraping']['max_pages']
        self.products = []
        self.logger = Logger()
        self.error_handler = ErrorHandler(self.logger)
        self.session = self._create_session()
    
    def _create_session(self):
        """Oturum oluştur ve başlıkları ayarla"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.petlebi.com/'
        })
        return session
    
    def scrape_all_pages(self):
        """Tüm sayfaları sırayla tara"""
        self.logger.info(f"Veri kazıma başlatılıyor: {self.max_pages} sayfa")
        
        start_time = time.time()
        
        for page in range(1, self.max_pages + 1):
            try:
                if page == 1:
                    url = self.base_url
                else:
                    url = f"{self.base_url}?page={page}"
                
                self.logger.info(f"Sayfa {page}/{self.max_pages} taranıyor: {url}")
                success = self.scrape_page(url)
                
                if not success:
                    self.logger.warning(f"Sayfa {page} taranamadı, devam ediliyor...")
                
                # Sunucuya aşırı yüklenmemek için bekleme
                if page % 5 == 0:  # Her 5 sayfada bir
                    time.sleep(2)
                else:
                    time.sleep(0.5)
                    
            except KeyboardInterrupt:
                self.logger.warning("Kullanıcı işlemi durdurdu")
                break
            except Exception as e:
                self.logger.exception(f"Sayfa {page} taranırken beklenmeyen hata: {e}")
                # Ciddi hatadan sonra kısa bir mola ver
                time.sleep(5)
        
        end_time = time.time()
        self.logger.info(f"Veri kazıma tamamlandı. {len(self.products)} ürün toplandı.")
        self.logger.info(f"Toplam süre: {end_time - start_time:.2f} saniye")
        
        return self.products
    
    def scrape_page(self, url):
        """Belirli bir sayfayı tara ve ürün listesini al"""
        try:
            # Sayfayı indir
            response = self.session.get(url, timeout=(10, 30))  # (bağlantı zaman aşımı, okuma zaman aşımı)
            
            if response.status_code != 200:
                error_type = self.error_handler.handle_request_error(url, response)
                return False
            
            # Sayfayı ayrıştır
            soup = BeautifulSoup(response.text, 'lxml')
            products = soup.find_all('div', class_='col-lg-4 col-md-4 col-sm-6 search-product-box')
            
            if not products:
                self.logger.warning(f"Sayfada ürün bulunamadı: {url}")
                return False
            
            self.logger.info(f"{len(products)} ürün bulundu")
            
            # Her ürünü işle
            successful_count = 0
            for product in products:
                try:
                    # Temel ürün verilerini çıkar
                    product_data = self.extract_product_data(product)
                    
                    if product_data:
                        # Ürün detaylarını al
                        detailed_data = self.get_product_details(product_data['url'])
                        product_data.update(detailed_data)
                        
                        # Temiz veriyi doğrula
                        if self.validate_product(product_data):
                            self.products.append(product_data)
                            successful_count += 1
                        else:
                            self.logger.warning(f"Ürün doğrulanamadı: {product_data.get('name', 'bilinmiyor')}")
                
                except Exception as e:
                    self.logger.error(f"Ürün işlenirken hata: {e}")
            
            self.logger.info(f"{successful_count} ürün başarıyla işlendi")
            return successful_count > 0
            
        except requests.exceptions.RequestException as e:
            self.error_handler.handle_request_error(url, e)
            return False
        except Exception as e:
            self.logger.exception(f"Sayfa taranırken beklenmeyen hata: {e}")
            return False
    
    def extract_product_data(self, product_element):
        """Ürün elementinden temel bilgileri çıkarır"""
        try:
            # Kart içeriğini bul
            more_info = product_element.find('div', class_='card-body pb-0 pt-2 pl-3 pr-3')
            if not more_info or not more_info.a:
                return None
            
            # URL'i al
            product_url = more_info.a['href']
            
            # GTM ürün verisini ayrıştır
            try:
                product_dictionary = json.loads(more_info.a['data-gtm-product'])
            except json.JSONDecodeError:
                self.logger.error(f"GTM ürün verisi ayrıştırılamadı: {more_info.a['data-gtm-product']}")
                return None
            
            # Temel ürün bilgilerini oluştur
            product_data = {
                "url": product_url,
                "name": product_dictionary.get("name", "İsimsiz Ürün"),
                "price": product_dictionary.get("price", 0.0),
                "stock": product_dictionary.get("dimension2", "Bilinmiyor"),
                "category": product_dictionary.get("category", "").split('>')[-1].strip(),
                "id": product_dictionary.get("id", ""),
                "brand": product_dictionary.get("brand", ""),
                "sku": ""  # Varsayılan boş değer
            }
            
            return product_data
            
        except Exception as e:
            self.logger.error(f"Ürün verisi çıkarma hatası: {e}")
            return None
    
    def get_product_details(self, product_url):
        """Ürün detay sayfasından ek bilgiler çıkarır"""
        product_details = {
            "barcode": "",
            "description": "",
            "image": ""
        }
        
        try:
            # Detay sayfasını indir
            response = self.session.get(product_url, timeout=(10, 30))
            
            if response.status_code != 200:
                error_type = self.error_handler.handle_request_error(product_url, response)
                return product_details
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Barkod ve açıklama
            info = soup.find_all('div', class_='tab-pane active show read-more-box', id="hakkinda")
            for div in info:
                # Barkod bilgisi
                barcode_divs = div.find_all('div', class_='row mb-2')
                for barcode_div in barcode_divs:
                    barcode_label = barcode_div.find('div', class_='col-2 pd-d-t')
                    if barcode_label and barcode_label.string == "BARKOD":
                        barcode_value = barcode_div.find('div', class_='col-10 pd-d-v')
                        if barcode_value:
                            product_details["barcode"] = barcode_value.text.strip()
                
                # Ürün açıklaması
                spans = div.find('span', id='productDescription')
                if spans:
                    for i, span in enumerate(spans):
                        if i == 1:  # İkinci öğe açıklama olarak belirtilmiş
                            product_details["description"] = span.text.strip().replace('\n', ' ')
            
            # Resim URL'si
            info2 = soup.find('div', class_='col-md-6 col-sm-5')
            if info2 and info2.a and 'href' in info2.a.attrs:
                product_details["image"] = info2.a['href']
            
            # Ürün detayları dönüş
            return product_details
            
        except requests.exceptions.RequestException as e:
            self.error_handler.handle_request_error(product_url, e)
            return product_details
        except Exception as e:
            self.logger.error(f"Ürün detayları alınamadı: {product_url}, {e}")
            return product_details
    
    def validate_product(self, product):
        """Ürün verisinin geçerli olup olmadığını kontrol eder"""
        # Zorunlu alanları kontrol et
        required_fields = ['url', 'name', 'price']
        for field in required_fields:
            if not product.get(field):
                return False
        
        # Fiyat sayısal mı kontrol et
        try:
            float(product['price'])
        except (ValueError, TypeError):
            return False
            
        return True
    
    def save_to_json(self, filename):
        """Ürünleri JSON dosyasına kaydeder"""
        try:
            with open(filename, "w", encoding="utf-8") as json_file:
                json.dump(self.products, json_file, ensure_ascii=False, indent=2)
            
            self.logger.info(f"{len(self.products)} ürün {filename} dosyasına kaydedildi")
            return True
        except Exception as e:
            self.logger.exception(f"JSON kaydetme hatası: {e}")
            return False
            
    def get_statistics(self):
        """Toplanan veri hakkında istatistikler sağlar"""
        if not self.products:
            return {"total": 0}
            
        categories = {}
        brands = {}
        stock_status = {"In Stock": 0, "Out of Stock": 0, "Other": 0}
        price_ranges = {"0-50": 0, "51-100": 0, "101-200": 0, "201+": 0}
        
        for product in self.products:
            # Kategori sayısı
            category = product.get('category', 'Unknown')
            categories[category] = categories.get(category, 0) + 1
            
            # Marka sayısı
            brand = product.get('brand', 'Unknown')
            brands[brand] = brands.get(brand, 0) + 1
            
            # Stok durumu
            stock = product.get('stock', '').lower()
            if 'in stock' in stock or 'stokta' in stock:
                stock_status["In Stock"] += 1
            elif 'out of stock' in stock or 'stokta yok' in stock or 'tükendi' in stock:
                stock_status["Out of Stock"] += 1
            else:
                stock_status["Other"] += 1
            
            # Fiyat aralıkları
            try:
                price = float(product.get('price', 0))
                if price <= 50:
                    price_ranges["0-50"] += 1
                elif price <= 100:
                    price_ranges["51-100"] += 1
                elif price <= 200:
                    price_ranges["101-200"] += 1
                else:
                    price_ranges["201+"] += 1
            except (ValueError, TypeError):
                pass
        
        return {
            "total": len(self.products),
            "categories": categories,
            "brands": brands,
            "stock_status": stock_status,
            "price_ranges": price_ranges,
            "with_barcode": sum(1 for p in self.products if p.get('barcode')),
            "with_image": sum(1 for p in self.products if p.get('image')),
            "with_description": sum(1 for p in self.products if p.get('description'))
        }

# error_handler.py - Hata yönetim yardımcısı sınıfı
class ErrorHandler:
    """Uygulama çapında hata yakalama ve işleme için yardımcı sınıf"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def handle_request_error(self, url, error):
        """HTTP isteklerinde oluşan hataları işler"""
        if hasattr(error, 'status_code'):
            status_code = error.status_code
            if status_code == 404:
                self.logger.warning(f"Sayfa bulunamadı (404): {url}")
                return "not_found"
            elif status_code == 403:
                self.logger.warning(f"Erişim engellendi (403): {url}")
                return "forbidden"
            elif status_code == 429:
                self.logger.warning(f"Çok fazla istek gönderildi (429): {url}")
                return "rate_limited"
            elif status_code >= 500:
                self.logger.error(f"Sunucu hatası ({status_code}): {url}")
                return "server_error"
            else:
                self.logger.error(f"HTTP hatası ({status_code}): {url}")
                return "http_error"
        else:
            self.logger.exception(f"Bağlantı hatası: {url}, {str(error)}")
            return "connection_error"
    
    def handle_parse_error(self, url, error):
        """HTML/JSON ayrıştırma hatalarını işler"""
        self.logger.error(f"Ayrıştırma hatası: {url}, {str(error)}")
        return "parse_error"