import json
import mysql.connector

def run_sql_file(cursor, filename):
    with open(filename, 'r') as sql_file:
        sql_queries = sql_file.read()
        sql_commands = sql_queries.split(';')

        for command in sql_commands:
            if command.strip() != '':
                cursor.execute(command)

def import_products_from_json(cursor, filename):
    with open(filename, 'r') as json_file:
        products_data = json.load(json_file)

        for product in products_data:
            add_product_query = """
            INSERT INTO petlebi (product_url, name, barcode, price, stock, image, description, sku, category, brand)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            product_values = (
                product['url'],
                product['name'],
                product['barcode'],
                product['price'],
                product['stock'],
                product['image'],
                product['description'],
                product['sku'],
                product['category'],
                product['brand']
            )
            cursor.execute(add_product_query, product_values)

connection = mysql.connector.connect(
    host=input("localhost name: "),
    port=input("port name:"),
    user=input("User name: "),
    password=input("MySQL password:")
)

create_database_query = "CREATE DATABASE IF NOT EXISTS mydatabase;"
cursor = connection.cursor()
cursor.execute(create_database_query)

connection.database = "mydatabase"

run_sql_file(cursor, 'petlebi_create.sql')

import_products_from_json(cursor, 'petlebi_products.json')

connection.commit()

connection.close()





