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
    
    def handle_database_error(self, operation, error):
        """Veritabanı hatalarını işler"""
        error_code = getattr(error, 'errno', 'unknown')
        error_msg = str(error)
        
        # MySQL hata kodlarına göre özel mesajlar
        if error_code == 1045:  # Access denied
            self.logger.critical(f"Veritabanına erişim reddedildi: {error_msg}")
            return "access_denied"
        elif error_code == 1049:  # Unknown database
            self.logger.error(f"Veritabanı bulunamadı: {error_msg}")
            return "unknown_database"
        elif error_code == 1146:  # Table doesn't exist
            self.logger.error(f"Tablo bulunamadı: {error_msg}")
            return "table_not_found"
        elif error_code == 1062:  # Duplicate entry
            self.logger.warning(f"Tekrarlanan kayıt: {error_msg}")
            return "duplicate_entry"
        else:
            self.logger.error(f"Veritabanı hatası ({operation}): {error_msg}")
            return "database_error"
    
    def handle_file_error(self, filename, operation, error):
        """Dosya işleme hatalarını yönetir"""
        if isinstance(error, FileNotFoundError):
            self.logger.error(f"Dosya bulunamadı: {filename}")
            return "file_not_found"
        elif isinstance(error, PermissionError):
            self.logger.error(f"Dosya erişim izni yok: {filename}")
            return "permission_denied"
        elif isinstance(error, IsADirectoryError):
            self.logger.error(f"Dosya değil dizin: {filename}")
            return "is_directory"
        else:
            self.logger.error(f"Dosya işleme hatası ({operation}): {filename}, {str(error)}")
            return "file_operation_error"
            
    def should_retry(self, error_type):
        """Hata türüne göre yeniden deneme gerekip gerekmediğini belirler"""
        # Yeniden denenebilecek hatalar
        retriable_errors = [
            "connection_error",
            "server_error",
            "rate_limited"
        ]
        return error_type in retriable_errors