import json
import time
import boto3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

CHROME_PATH = "/var/task/chrome/headless-chromium"
CHROMEDRIVER_PATH = "/var/task/chrome/chromedriver"

options = Options()
options.binary_location = CHROME_PATH
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

SQS_QUEUE_URL = "https://sqs.eu-west-1.amazonaws.com/1234567890/YelpReviewsQueue"
DYNAMODB_TABLE_NAME = "YelpRestaurants"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

def get_yelp_reviews(restaurant):
    """
    Scrape les avis d'un restaurant depuis Yelp.com
    """
    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
    try:
        driver.get(restaurant["url"])
        time.sleep(3)

        reviews_elements = driver.find_elements(By.CLASS_NAME, "comment__09f24__D0cxf")
        reviews = [review.text for review in reviews_elements]

        return {"id": restaurant["id"], "name": restaurant["name"], "reviews": reviews}
    except Exception as e:
        return {"id": restaurant["id"], "name": restaurant["name"], "error": str(e)}
    finally:
        driver.quit()

def receive_from_sqs():
    """
    Récupère un restaurant depuis la file SQS.
    """
    sqs = boto3.client('sqs')
    response = sqs.receive_message(
        QueueUrl=SQS_QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10
    )

    messages = response.get('Messages', [])
    if not messages:
        return None

    message = messages[0]
    restaurant = json.loads(message['Body'])
    receipt_handle = message['ReceiptHandle']

    return restaurant, receipt_handle

def delete_message(receipt_handle):
    """
    Supprime un message de la file SQS après traitement.
    """
    sqs = boto3.client('sqs')
    sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt_handle)

def store_reviews_to_dynamodb(data):
    """
    Stocke les avis scrapés dans DynamoDB.
    """
    table.update_item(
        Key={"id": data["id"]},
        UpdateExpression="SET reviews = :r",
        ExpressionAttributeValues={":r": data["reviews"]}
    )
    print(f"✅ Avis stockés pour {data['name']}")

def lambda_handler(event, context):
    restaurant_data = receive_from_sqs()
    if not restaurant_data:
        print("📭 Aucun message à traiter dans SQS.")
        return {"statusCode": 200, "body": "📭 Aucun message à traiter"}

    restaurant, receipt_handle = restaurant_data
    print(f"🔍 Scraping des avis pour : {restaurant['name']}")

    reviews = get_yelp_reviews
