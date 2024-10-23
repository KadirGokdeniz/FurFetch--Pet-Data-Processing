# Petlebi Web Scraping Project
Welcome to the **Petlebi Web Scraping Project**! This project allows you to gather animal product information from the Petlebi website using effective web scraping techniques.

## Table of Contents
- [Project Files](#project-files)
- [How to Use](#how-to-use)
- [Additional Information](#additional-information)

## Project Files
Here are the key files included in this project:
- **`petlebi_scrapy.py`**: The main Python script that scrapes product information from the Petlebi website.
- **`import_products.py`**: A Python script that connects to a MySQL database, creating a new database and table for importing data from JSON format.
- **`petlebi_create.sql`**: SQL commands needed to set up the required database and table structure for this project.

## How to Use
Follow these simple steps to get started:

1. **Scrape Product Information**:
   - Run the `petlebi_scrapy.py` file. This will scrape product information from the Petlebi website and save it to `petlebi_products.json`.

2. **Import Data into MySQL**:
   - Execute the `import_products.py` file to:
     - Create a new table in your MySQL database using the commands from `petlebi_create.sql`.
     - Import the scraped data from the `petlebi_products.json` file into the newly created table.

## Additional Information
- This project is capable of scraping product information from **221 different pages**.
- To add information for a new product, simply run the SQL commands from the `petlebi_create.sql` file.

Feel free to explore the code, and happy scraping!
