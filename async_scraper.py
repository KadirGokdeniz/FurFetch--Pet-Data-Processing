# async_scraper.py - Asenkron veri kazıma
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import time
from config import CONFIG

class AsyncPetlebiScraper:
    def __init__(self, base_url=None, max_pages=None, concurrency_limit=5):
        self.base_url = base_url or CONFIG['scraping']['base_url']
        self.max_pages = max_pages or CONFIG['scraping']['max_pages']
        self.concurrency_limit = concurrency_limit  # Aynı anda çalışacak istek sayısını sınırla
        self.products = []
        self.semaphore = None  # Asenkron işlemleri kontrol etmek için semaphore
        
    async def fetch(self, session, url):
        """URL'den veri almak için asenkron istek yapar"""
        try:
            async with self.semaphore:  # İstek limitini kontrol et
                print(f"İstek gönderiliyor: {url}")
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        print(f"Hata: {url} için {response.status} kodu alındı")
                        return None
        except Exception as e:
            print(f"İstek hatası {url}: {e}")
            return None
    
    async def parse_product_list(self, html, page_num):
        """Ürün listesi HTML'ini işler ve detay URL'lerini çıkarır"""
        if not html:
            return []
            
        soup = BeautifulSoup(html, 'lxml')
        products = soup.find_all('div', class_='col-lg-4 col-md-4 col-sm-6 search-product-box')
        product_urls = []
        
        print(f"Sayfa {page_num}: {len(products)} ürün bulundu")
        
        for product in products:
            try:
                more_info = product.find('div', class_='card-body pb-0 pt-2 pl-3 pr-3')
                if more_info and more_info.a:
                    product_url = more_info.a['href']
                    product_dictionary = json.loads(more_info.a['data-gtm-product'])
                    
                    # Temel ürün bilgilerini kaydet
                    product_data = {
                        "url": product_url,
                        "name": product_dictionary["name"],
                        "price": product_dictionary["price"],
                        "stock": product_dictionary["dimension2"],
                        "category": product_dictionary["category"].split('>')[-1],
                        "id": product_dictionary["id"],
                        "brand": product_dictionary["brand"],
                        "sku": ""
                    }
                    
                    # Detay URL'sini ürün verisiyle birlikte tut
                    product_urls.append((product_url, product_data))
            except Exception as e:
                print(f"Ürün veri çıkarma hatası: {e}")
        
        return product_urls
    
    async def parse_product_detail(self, html, basic_product_data):
        """Ürün detay sayfasından ek bilgileri çıkarır"""
        if not html:
            return basic_product_data
            
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Barkod ve açıklama
            barcode = ""
            description = ""
            
            info = soup.find_all('div', class_='tab-pane active show read-more-box', id="hakkinda")
            for div in info:
                barcode_divs = div.find_all('div', class_='row mb-2')
                for barcode_div in barcode_divs:
                    barcode_label = barcode_div.find('div', class_='col-2 pd-d-t')
                    if barcode_label and barcode_label.string == "BARKOD":
                        barcode_value = barcode_div.find('div', class_='col-10 pd-d-v')
                        barcode = barcode_value.text.strip() if barcode_value else ""
                
                spans = div.find('span', id='productDescription')
                if spans:
                    for i, span in enumerate(spans):
                        if i == 1:
                            description = span.text.strip().replace('\n', ' ')
            
            # Resim URL'si
            image = ""
            info2 = soup.find('div', class_='col-md-6 col-sm-5')
            if info2 and info2.a and 'href' in info2.a.attrs:
                image = info2.a['href']
            
            # Temel ürün bilgilerine ek detayları ekle
            basic_product_data.update({
                "barcode": barcode,
                "description": description,
                "image": image
            })
            
            return basic_product_data
        except Exception as e:
            print(f"Ürün detay işleme hatası: {e}")
            return basic_product_data
            
    async def process_page(self, session, page_num):
        """Sayfayı işler ve ürün detaylarını alır"""
        if page_num == 1:
            url = self.base_url
        else:
            url = f"{self.base_url}?page={page_num}"
            
        # Sayfadaki ürün listesini al
        page_html = await self.fetch(session, url)
        if not page_html:
            return
            
        # Sayfa içindeki ürünlerin detay URL'lerini çıkar
        product_urls = await self.parse_product_list(page_html, page_num)
        
        # Her ürün için detay sayfasını işle
        product_detail_tasks = []
        for product_url, product_data in product_urls:
            task = asyncio.create_task(self.process_product(session, product_url, product_data))
            product_detail_tasks.append(task)
            
        # Tüm ürün detaylarının tamamlanmasını bekle
        await asyncio.gather(*product_detail_tasks)
    
    async def process_product(self, session, url, basic_product_data):
        """Ürün detay bilgilerini alır ve kaydeder"""
        try:
            # Ürün detay sayfasını al
            detail_html = await self.fetch(session, url)
            
            # Detay bilgilerini çıkar ve ürün verilerine ekle
            complete_product = await self.parse_product_detail(detail_html, basic_product_data)
            
            # Ürünü listeye ekle
            self.products.append(complete_product)
            print(f"Ürün eklendi: {complete_product['name']}")
        except Exception as e:
            print(f"Ürün işleme hatası {url}: {e}")
    
    async def scrape_all(self):
        """Tüm sayfaları asenkron olarak tarar"""
        start_time = time.time()
        self.semaphore = asyncio.Semaphore(self.concurrency_limit)
        
        async with aiohttp.ClientSession() as session:
            # Tüm sayfaları işlemek için görevler oluştur
            page_tasks = []
            for page in range(1, self.max_pages + 1):
                task = asyncio.create_task(self.process_page(session, page))
                page_tasks.append(task)
                
                # Her 10 sayfa için bir bekletme (opsiyonel)
                if page % 10 == 0:
                    print(f"İlk {page} sayfa için görevler oluşturuldu. Bekleniyor...")
                    await asyncio.gather(*page_tasks)
                    page_tasks = []  # Görev listesini temizle
                    await asyncio.sleep(1)  # Rate limiting
            
            # Kalan görevleri tamamla
            if page_tasks:
                await asyncio.gather(*page_tasks)
        
        end_time = time.time()
        print(f"Toplam süre: {end_time - start_time:.2f} saniye")
        print(f"Toplanan ürün sayısı: {len(self.products)}")
        return self.products
    
    async def run_and_save(self, filename):
        """Scraper'ı çalıştırır ve sonuçları kaydeder"""
        products = await self.scrape_all()
        try:
            with open(filename, "w", encoding="utf-8") as json_file:
                json.dump(products, json_file, ensure_ascii=False, indent=2)
            print(f"{len(products)} ürün {filename} dosyasına kaydedildi")
            return True
        except Exception as e:
            print(f"JSON kaydetme hatası: {e}")
            return False

# Kullanım örneği
async def main():
    scraper = AsyncPetlebiScraper(max_pages=10)  # Test için 10 sayfa
    await scraper.run_and_save("petlebi_products_async.json")

if __name__ == "__main__":
    asyncio.run(main())