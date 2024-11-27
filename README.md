# web_scraper
This project just scrapes the product details from https://dentalstall.com/shop/
This project is a solution of the assignment given by Atlys.

## How to run this project:
1. Setup a virtual environment in local ( follow this to setup https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/)
2. Clone this repo
3. Run `pip install -r requirements.txt`
4. Run `uvicorn scraper:app --reload` to run the project

## Use this project
#### Use Postman 
#### Url: `http://127.0.0.1:8000/scrape`
#### Method: POST
#### Add `token` with value `secretToken` in headers
#### In body:
```
{
    "pages": 4,
    "proxy": "proxy server if available otherwise remove this field"
}
```
#### Response:
```
{
    "status": "success",
    "message": "Scraped 51 products."
}
```

### It will create a scraped_products.json where product_title, product_price and path_to_image 
### It will create a `images` folder where it will keep all the downloaded images of products.
