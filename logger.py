# logger.py - Loglama yardımcısı
import logging
import os
from datetime import datetime

class Logger:
    """Uygulama çapında loglama işlevselliği sağlar"""
    
    def __init__(self, log_level=logging.INFO, log_to_file=True):
        """Logger'ı başlatır
        
        Args:
            log_level: Loglama seviyesi (logging.DEBUG, logging.INFO, vb.)
            log_to_file: Dosyaya log yazılsın mı?
        """
        # Log formatı
        log_format = '%(asctime)s [%(levelname)s] - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # Root logger'ı yapılandır
        self.logger = logging.getLogger('petlebi_scraper')
        self.logger.setLevel(log_level)
        
        # Mevcut handler'ları temizle
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # Konsol handler'ı ekle
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        self.logger.addHandler(console_handler)
        
        # Dosya handler'ı ekle (opsiyonel)
        if log_to_file:
            # Log dizinini oluştur
            log_dir = 'logs'
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Günlük log dosyası oluştur
            log_filename = f"{log_dir}/petlebi_scraper_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_filename)
            file_handler.setFormatter(logging.Formatter(log_format, date_format))
            self.logger.addHandler(file_handler)
    
    def debug(self, message):
        """Debug seviyesinde log"""
        self.logger.debug(message)
    
    def info(self, message):
        """Info seviyesinde log"""
        self.logger.info(message)
    
    def warning(self, message):
        """Warning seviyesinde log"""
        self.logger.warning(message)
    
    def error(self, message):
        """Error seviyesinde log"""
        self.logger.error(message)
    
    def critical(self, message):
        """Critical seviyesinde log"""
        self.logger.critical(message)
    
    def exception(self, message):
        """Exception stack trace ile hata logu"""
        self.logger.exception(message)