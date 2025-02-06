import json
import time
import boto3
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
restaurants_table = dynamodb.Table('restaurant-' + os.environ['ENV'])
avis_table = dynamodb.Table('avis-' + os.environ['ENV'])

# Configuration du WebDriver
options = webdriver.ChromeOptions()
options.binary_location = "C:/Program Files/Google/Chrome/Application/chrome.exe"
options.headless = True  # Mode headless pour exécution sans interface graphique
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")  # Évite la détection Selenium

restaurants = [
    "le-comptoir-de-la-gastronomie-paris",
    "le-fouquets-paris",
    "chez-léon-paris",
]

def handler(event, context):
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        all_reviews = [get_yelp_reviews(driver, restaurant) for restaurant in restaurants]
        return {
            "statusCode": 200,
            "body": json.dumps(all_reviews, indent=4, ensure_ascii=False)
        }
    finally:
        driver.quit()


def get_yelp_reviews(driver, restaurant_name):
    url = f"https://www.yelp.com/biz/{restaurant_name}"
    print(f"Scraping {url}...")

    try:
        driver.get(url)
        
        # Attente dynamique de l'affichage des avis
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "comment__09f24__D0cxf"))
        )

        reviews_elements = driver.find_elements(By.CLASS_NAME, "comment__09f24__D0cxf")
        
        if not reviews_elements:
            print(f"Aucun avis trouvé pour {restaurant_name}")
        
        reviews = [review.text for review in reviews_elements]
        persist_data({"restaurant": restaurant_name, "reviews": reviews})
        return {"restaurant": restaurant_name, "reviews": reviews}

    except Exception as e:
        return {"restaurant": restaurant_name, "error": str(e)}


def persist_data(json_data): 
    # Enregistrement du restaurant dans la table restaurants_table
    restaurants_table.put_item(
        Item={
            "idrestaurant": json_data["restaurant"]
        }
    )
    
    # Enregistrement des avis dans la table avis_table
    for i, review in enumerate(json_data["reviews"], start=1):
        avis_table.put_item(  # Correction ici : put_item() au lieu de put_items()
            Item={
                "idavis": f"{json_data['restaurant']}-{i}",  # ID unique avec index
                "idrestaurant": json_data["restaurant"],
                "commentaire": review
            }
        )
