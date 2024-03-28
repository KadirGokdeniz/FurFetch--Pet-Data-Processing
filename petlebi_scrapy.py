from bs4 import BeautifulSoup
import requests
import json

existing_data = []
page_number = 1

def find_products(link):
    global existing_data
    global page_number
    print(page_number)
    html_text = requests.get(link).text
    soup = BeautifulSoup(html_text, 'lxml')
    products = soup.find_all('div', class_='col-lg-4 col-md-4 col-sm-6 search-product-box')
    for product in products:
        more_info = product.find('div', class_='card-body pb-0 pt-2 pl-3 pr-3')
        product_url = more_info.a['href']
        product_dictionary = json.loads(more_info.a['data-gtm-product'])
        product_name = product_dictionary["name"]
        product_price = product_dictionary["price"]
        product_stock = product_dictionary["dimension2"]
        product_category = product_dictionary["category"].split('>')[-1]
        product_id = product_dictionary["id"]
        product_brand = product_dictionary["brand"]
        sku = " "

        # New page for additional informations
        html_text_additional = requests.get(product_url).text
        soup_new = BeautifulSoup(html_text_additional, 'lxml')
        info = soup_new.find_all('div', class_='tab-pane active show read-more-box', id="hakkinda")

        for div in info:
            barcode_divs = div.find_all('div', class_='row mb-2')
            for barcode_div in barcode_divs:
                barcode = barcode_div.find('div', class_='col-2 pd-d-t')
                if barcode and barcode.string == "BARKOD":
                    barcode = barcode_div.find('div', class_='col-10 pd-d-v')
                    barcode = barcode.text.strip()
                    product_barcode = barcode
            spans = div.find('span', id='productDescription')
            for i, span in enumerate(spans):
                if i == 1:
                    product_description = span.text.strip()
                    product_description = product_description.replace('\n', ' ')
        info2 = soup_new.find('div', class_='col-md-6 col-sm-5')
        product_image = info2.a['href']

        data = {
            "url": product_url,
            "name": product_name,
            "barcode": product_barcode,
            "price": product_price,
            "stock": product_stock,
            "image": product_image,
            "description": product_description,
            "sku": sku,
            "category": product_category,
            "id": product_id,
            "brand": product_brand
        }
        existing_data.append(data)
    page_number += 1
    next_link = link + '?page=' + str(page_number)

    if page_number<222:
        find_products(next_link)
    else:
        print("finished")

find_products('https://www.petlebi.com/alisveris/ara')

with open("petlebi_products.json", "w") as json_file:
    json.dump(existing_data, json_file)
