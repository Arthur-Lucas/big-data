import json
import requests
import boto3

def get_yelp_api_key(secret_name="my-secret-key", region_name="eu-west-1"):
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response["SecretString"])
    return secret.get("api_key")

YELP_API_KEY = get_yelp_api_key()
BASE_URL = "https://api.yelp.com/v3/businesses"
HEADERS = {
    "Authorization": f"Bearer {YELP_API_KEY}",
    "Content-Type": "application/json"
}

SQS_QUEUE_URL = "https://sqs.eu-west-1.amazonaws.com/1234567890/YelpReviewsQueue"
DYNAMODB_TABLE_NAME = "YelpRestaurants"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

def get_restaurants_from_yelp(location="Paris", term="restaurant", limit=50):

    try:
        params = {"term": term, "location": location, "limit": limit}
        response = requests.get(f"{BASE_URL}/search", headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        restaurants = []
        for business in data.get("businesses", []):
            restaurants.append({
                "id": business["id"],
                "name": business["name"],
                "address": " ".join(business["location"].get("display_address", [])),
                "rating": business.get("rating"),
                "review_count": business.get("review_count"),
                "phone": business.get("display_phone"),
                "categories": [cat["title"] for cat in business.get("categories", [])],
                "url": f"https://www.yelp.com/biz/{business['id']}?osq=restaurant"
            })
        
        return restaurants

    except requests.exceptions.RequestException as e:
        print(f" Erreur API Yelp : {str(e)}")
        return []

def store_restaurant_to_dynamodb(restaurant):

    table.put_item(Item=restaurant)
    print(f" Restaurant stocké : {restaurant['name']}")

def send_to_sqs(restaurant):
    sqs = boto3.client('sqs')
    message_body = json.dumps({"id": restaurant["id"], "name": restaurant["name"], "url": restaurant["url"]})
    response = sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=message_body
    )
    print(f" Message envoyé à SQS : {restaurant['name']} ({restaurant['id']})")
    return response

def handler(event, context):
    restaurants = get_restaurants_from_yelp()
    
    if not restaurants:
        print(" Aucun restaurant trouvé sur Yelp.")
        return {"statusCode": 500, "body": " Aucun restaurant trouvé"}

    for restaurant in restaurants:
        store_restaurant_to_dynamodb(restaurant)
        send_to_sqs(restaurant)

    return {"statusCode": 200, "body": json.dumps(f" {len(restaurants)} restaurants stockés dans DynamoDB et envoyés à SQS")}
