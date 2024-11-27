import json
import os
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_fixed
from cachetools import TTLCache
from typing import Optional

# Data Models
class ScrapeRequest(BaseModel):
    pages: Optional[int] = 5
    proxy: Optional[str] = None

# Initialize FastAPI app
app = FastAPI()

# Taking default Cache timing for 1 hour with 100 items
cache = TTLCache(maxsize=100, ttl=3600)

# Authentication token(using static token for simplicity)
API_TOKEN = "secretToken"


def verify_token(token: str = Header(...)):
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")


def download_image(image_url: str, product_title: str):
    ''' Function to download the product image in images folder'''
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        image_path = f"images/{product_title.replace(' ', '_').replace('.','')}.jpg"
        with open(image_path, 'wb') as file:
            file.write(response.content)
        return image_path
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def scrape_page(url: str, proxy: Optional[str] = None):
    '''
    This function scapes product data from given url
    Also retries 3 times
    '''
    proxies = {"http": proxy, "https": proxy} if proxy else None
    response = requests.get(url, proxies=proxies)
    response.raise_for_status()
    return response.text

def create_images_folder():
    ''' this function creates images folder if already does not exists'''

    dir_path="images"
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print("Images directory created successfully!")
    else:
        print("Images directory already exists!")

# Scraping function
def scrape_products(pages: int, proxy: Optional[str] = None):
    products = []
    base_url = "https://dentalstall.com/shop/page/"
    create_images_folder()
    
    for page in range(1, pages + 1):
        try:
            url = f"{base_url}{page}/"
            print(f"Scraping page {page}: {url}")
            html = scrape_page(url, proxy)
            soup = BeautifulSoup(html, "html.parser")
            
            # Find all product elements
            product_items = soup.find_all("li", class_="product")
            
            for product in product_items:
                name_tag = product.find('h2', class_='woo-loop-product__title')
                product_title = name_tag.get_text(strip=True) if name_tag else None
                
                price_tag = product.find('span', class_='price')
                price = price_tag.get_text(strip=True).split('₹')[1] if price_tag else None
                
                
                image_url = product.find('img')["data-lazy-src"]
                
                # Check if the product exists in cache and if price has changed
                cached_price = cache.get(product_title)
                if cached_price != price:
                    image_path = download_image(image_url, product_title)
                    products.append({
                        "product_title": product_title,
                        "product_price": float(price.strip('₹').replace(',', '')),
                        "path_to_image": image_path,
                    })
                    cache[product_title] = price

        except Exception as e:
            print(f"Error scraping page {page}: {e}")
    
    return products

# FastAPI endpoint to start scraping
@app.post("/scrape")
def scrape(scrape_request: ScrapeRequest, token: str = Depends(verify_token)):
    pages = scrape_request.pages
    proxy = scrape_request.proxy
    
    products = scrape_products(pages, proxy)
    
    # Save the products data to JSON
    if products:
        with open("scraped_products.json", "w") as f:
            json.dump(products, f, indent=4)
    
    # Notify (print in the console)
    print(f"Scraped {len(products)} products.")
    
    return {"status": "success", "message": f"Scraped {len(products)} products."}
