
# main.py - Ana program
import argparse
import json
from config import CONFIG
from logger import Logger
from scraper import PetlebiScraper
from database import DatabaseManager
import sys
import traceback

def parse_arguments():
    """Komut satırı argümanlarını işler"""
    parser = argparse.ArgumentParser(description="Petlebi Veri Kazıma ve Veritabanı Aracı")
    
    parser.add_argument("--scrape", action="store_true", help="Web sitesinden veri çekmek için bu seçeneği kullanın")
    parser.add_argument("--import", dest="import_data", action="store_true", help="JSON verilerini veritabanına aktarmak için kullanın")
    parser.add_argument("--pages", type=int, default=CONFIG['scraping']['max_pages'], help="Taranacak sayfa sayısı")
    parser.add_argument("--output", type=str, default="petlebi_products.json", help="JSON çıktı dosyası")
    parser.add_argument("--input", type=str, default="petlebi_products.json", help="İçe aktarılacak JSON dosyası")
    parser.add_argument("--sql", type=str, default="petlebi_create.sql", help="Çalıştırılacak SQL dosyası")
    parser.add_argument("--db-name", type=str, default=CONFIG['database']['db_name'], help="Veritabanı adı")
    parser.add_argument("--host", type=str, default=CONFIG['database']['host'], help="Veritabanı sunucusu")
    parser.add_argument("--port", type=str, default=CONFIG['database']['port'], help="Veritabanı portu")
    parser.add_argument("--user", type=str, default=CONFIG['database']['user'], help="Veritabanı kullanıcısı")
    parser.add_argument("--password", type=str, default=None, help="Veritabanı şifresi")
    parser.add_argument("--debug", action="store_true", help="Debug modu")
    
    return parser.parse_args()

def scrape_data(args, logger):
    """Web sitesinden veri çeker"""
    logger.info(f"Veri çekme işlemi başlatılıyor: {args.pages} sayfa")
    
    scraper = PetlebiScraper(base_url=CONFIG['scraping']['base_url'], max_pages=args.pages)
    products = scraper.scrape_all_pages()
    
    if products:
        scraper.save_to_json(args.output)
        logger.info(f"{len(products)} ürün {args.output} dosyasına kaydedildi")
        return True
    else:
        logger.error("Veri çekme işlemi başarısız oldu")
        return False

def import_to_database(args, logger):
    """JSON verilerini veritabanına aktarır"""
    logger.info("Veritabanı işlemleri başlatılıyor")
    
    # Veritabanı yöneticisini başlat
    db = DatabaseManager()
    
    # Kullanıcı şifresi
    password = args.password if args.password else input("MySQL şifresi: ")
    
    # Veritabanına bağlan
    if not db.connect(host=args.host, port=args.port, user=args.user, password=password):
        logger.error("Veritabanı bağlantısı kurulamadı.")
        return False
    
    # Veritabanını oluştur
    if not db.create_database(args.db_name):
        logger.error(f"Veritabanı oluşturulamadı: {args.db_name}")
        return False
    
    # SQL dosyasını çalıştır
    if not db.run_sql_file(args.sql):
        logger.error(f"SQL dosyası çalıştırılamadı: {args.sql}")
        return False
    
    # JSON'dan veri aktar
    logger.info(f"{args.input} dosyasından veriler içe aktarılıyor...")
    if not db.import_products_from_json(args.input):
        logger.error("Ürünler veritabanına aktarılamadı")
        db.commit_and_close()
        return False
    
    # Bağlantıyı kapat
    db.commit_and_close()
    logger.info("Veritabanı işlemleri tamamlandı")
    return True

def main():
    # Argümanları işle
    args = parse_arguments()
    
    # Logger'ı başlat
    logger = Logger(log_level=logging.DEBUG if args.debug else logging.INFO)
    
    try:
        if not args.scrape and not args.import_data:
            logger.info("Bir işlem belirtmediniz. --scrape veya --import seçeneğini kullanın.")
            print("\nKullanım örnekleri:")
            print("  python main.py --scrape --pages 10 --output products.json")
            print("  python main.py --import --input products.json --db-name petlebidb")
            return
        
        # Veri çekme
        if args.scrape:
            if not scrape_data(args, logger):
                logger.error("Veri çekme işlemi başarısız oldu")
                return
        
        # Veritabanına aktarma
        if args.import_data:
            if not import_to_database(args, logger):
                logger.error("Veritabanı işlemleri başarısız oldu")
                return
        
        logger.info("İşlem başarıyla tamamlandı!")
        
    except KeyboardInterrupt:
        logger.warning("İşlem kullanıcı tarafından iptal edildi.")
    except Exception as e:
        logger.critical(f"Beklenmeyen hata: {e}")
        if args.debug:
            logger.debug(traceback.format_exc())

if __name__ == "__main__":
    main()

# Ayrıca asenkron versiyonunun nasıl kullanılacağını gösterelim
# async_main.py - Asenkron sürüm için ana program
import asyncio
import argparse
import logging
from config import CONFIG
from logger import Logger
from async_scraper import AsyncPetlebiScraper
from database import DatabaseManager

async def main_async():
    # Argümanları işle
    parser = argparse.ArgumentParser(description="Petlebi Asenkron Veri Kazıma Aracı")
    parser.add_argument("--pages", type=int, default=10, help="Taranacak sayfa sayısı")
    parser.add_argument("--output", type=str, default="petlebi_products_async.json", help="JSON çıktı dosyası")
    parser.add_argument("--concurrency", type=int, default=5, help="Eşzamanlı istek sayısı")
    parser.add_argument("--debug", action="store_true", help="Debug modu")
    args = parser.parse_args()
    
    # Logger'ı başlat
    logger = Logger(log_level=logging.DEBUG if args.debug else logging.INFO)
    logger.info(f"Asenkron veri çekme işlemi başlatılıyor: {args.pages} sayfa, {args.concurrency} eşzamanlı istek")
    
    try:
        # Asenkron scraper'ı oluştur ve çalıştır
        scraper = AsyncPetlebiScraper(
            base_url=CONFIG['scraping']['base_url'],
            max_pages=args.pages,
            concurrency_limit=args.concurrency
        )
        
        await scraper.run_and_save(args.output)
        logger.info(f"Asenkron veri çekme işlemi tamamlandı, çıktı: {args.output}")
        
    except KeyboardInterrupt:
        logger.warning("İşlem kullanıcı tarafından iptal edildi.")
    except Exception as e:
        logger.critical(f"Beklenmeyen hata: {e}")
        if args.debug:
            import traceback
            logger.debug(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main_async())