# Petlebi Web Scraping Project
This project is designed to scrape animal product information from the Petlebi website using web scraping techniques.

## Files
- **petlebi_scrapy.py**: This Python file contains the main code used to scrape product information from the Petlebi website.
- **import_products.py**: This Python file establishes a connection with a MySQL database and creates a new database and table to import data from JSON format.
- **petlebi_create.sql**: This SQL file contains the necessary commands to create the required database and table for the project.

## Usage
1. Run the `petlebi_scrapy.py` file to scrape product information from the Petlebi website and save it to the `petlebi_products.json` file.
2. Execute the `import_products.py` file to:
   - Create a new table in the MySQL database using the SQL commands from the `petlebi_create.sql` file.
   - Import data from the JSON file into this table.

## Additional Information
- The project can scrape product information from a total of **221 different pages**.
- If you wish to add information for a new product, execute the SQL commands from the `petlebi_create.sql` file.
