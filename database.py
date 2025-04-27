# database.py - Veritabanı işlemleri
import mysql.connector
import json
from config import CONFIG

class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None
        
    def connect(self, host=None, port=None, user=None, password=None):
        """Veritabanı bağlantısı oluşturur"""
        host = host or input("localhost name: ")
        port = port or input("port name: ")
        user = user or input("User name: ")
        password = password or input("MySQL password: ")
        
        try:
            self.connection = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password
            )
            self.cursor = self.connection.cursor()
            return True
        except mysql.connector.Error as err:
            print(f"Veritabanı bağlantı hatası: {err}")
            return False
            
    def create_database(self, db_name):
        """Veritabanı oluşturur"""
        try:
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name};")
            self.connection.database = db_name
            return True
        except mysql.connector.Error as err:
            print(f"Veritabanı oluşturma hatası: {err}")
            return False
            
    def run_sql_file(self, filename):
        """SQL dosyasını çalıştırır"""
        try:
            with open(filename, 'r') as sql_file:
                sql_queries = sql_file.read()
                sql_commands = sql_queries.split(';')
                for command in sql_commands:
                    if command.strip() != '':
                        self.cursor.execute(command)
            return True
        except Exception as e:
            print(f"SQL dosyası çalıştırma hatası: {e}")
            return False
            
    def import_products(self, products_data):
        """Ürünleri veritabanına ekler"""
        try:
            for product in products_data:
                add_product_query = """
                INSERT INTO petlebi (product_url, name, barcode, price, stock, image, description, sku, category, brand)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                product_values = (
                    product['url'],
                    product['name'],
                    product.get('barcode', ''),
                    product['price'],
                    product['stock'],
                    product.get('image', ''),
                    product.get('description', ''),
                    product.get('sku', ''),
                    product.get('category', ''),
                    product.get('brand', '')
                )
                self.cursor.execute(add_product_query, product_values)
            return True
        except Exception as e:
            print(f"Ürün ekleme hatası: {e}")
            return False
    
    def import_products_from_json(self, filename):
        """JSON dosyasından ürünleri içe aktarır"""
        try:
            with open(filename, 'r') as json_file:
                products_data = json.load(json_file)
                return self.import_products(products_data)
        except Exception as e:
            print(f"JSON okuma hatası: {e}")
            return False
            
    def commit_and_close(self):
        """Değişiklikleri kaydeder ve bağlantıyı kapatır"""
        if self.connection:
            self.connection.commit()
            self.connection.close()
            print("Veritabanı bağlantısı kapatıldı")