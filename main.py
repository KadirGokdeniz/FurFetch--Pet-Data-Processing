# main.py - Ana program
from config import CONFIG
from database import Database
from scraper import PetlebiScraper

def main():
    # 1. Web scraping
    print("Veri kazıma işlemi başlatılıyor...")
    scraper = PetlebiScraper()
    products = scraper.scrape_all_pages()
    scraper.save_to_json("petlebi_products.json")
    
    # 2. Veritabanı işlemleri
    print("\nVeritabanı işlemleri başlatılıyor...")
    db = Database()
    
    # Veritabanı bağlantısı
    if not db.connect(
        CONFIG["database"]["host"], 
        CONFIG["database"]["port"],
        CONFIG["database"]["user"],
        CONFIG["database"]["password"]
    ):
        print("Program sonlandırılıyor.")
        return
    
    # Veritabanı oluşturma
    if not db.create_database(CONFIG["database"]["db_name"]):
        print("Program sonlandırılıyor.")
        return
    
    # Tablo oluşturma
    if not db.run_sql_file('petlebi_create.sql'):
        print("Program sonlandırılıyor.")
        return
    
    # Ürünleri içe aktarma
    print(f"{len(products)} ürün veritabanına aktarılıyor...")
    if db.import_products(products):
        print("Ürünler başarıyla veritabanına eklendi.")
    
    # Bağlantıyı kapat
    db.commit_and_close()
    print("İşlem tamamlandı!")

if __name__ == "__main__":
    main()