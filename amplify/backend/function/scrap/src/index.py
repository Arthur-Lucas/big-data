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
restaurants_table = dynamodb.Table(os.environ["STORAGE_RESTAURANT_NAME"])
avis_table = dynamodb.Table(os.environ["STORAGE_AVIS_NAME"])

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

data = [
    {
        "restaurant": "le-fouquets-paris",
        "reviews": [
            "We had a splendid dinner here. It is expensive but the food was absolutely perfect. The service was attentive. The ambiance is wonderful. If you have time for a long luxurious meal, this is a spot to check out. I had some to die for chicken with morrel mushrooms in a super tasty sauce. The onion soup was wonderful. The sorbet--- sooo good. We were here feasting for hours.",
            "Chicken supreme was amazing! Loved the ambiance. Service was excellent. Definitely go here!",
            "I ended up coming here with other family and friends, after our friend was told by the hotel to hit up this place.\nWhen I arrived, it was pretty empty during 3/4pm, which isn't unusual. Staff was nice, friendly. This is in one of the most touristy locations in all of Paris, so you're warned. Off the bat, I knew this would be an overly pricey place to come with out of town guests or maybe for a special occassion.\n\nThe food was mediocre- steak, escargot, def you can get better off the beaten path, especially for that price.\n\nAmbience- quiet, too quiet for me, formal, well decorated.\n\nStaff- polite and accomodating and we had 2 young toddlers with us.\nprice- high, but appropriate. your on the most famous avenue in paris. what do you expect?\n\nI'm not certain I'd return on my own will, maybe if I was with a group that really wanted to come here for the history or maybe if the President invited me, lol.",
            "1/1/2024\nI made a reservation on January 2nd through Yelp, I highly recommend to make a reservation.\nI always come to Fouquet when am in Paris. The service is fantastic and the French ambiance is a great experience.\nIt's pricy,,,$182 for lunch.\nThe French onion soup was delicious and the croquet monsieur was so good.\nThey bring olives and fresh bread to the table.\nEmma our waiter was so nice.\nIt was my bday so they did bring a cutie tiny cake and chocolate for me.\nLoved the experience.\nIt's a must try.\nMy $41 dollar salad was a bit under dressed. We dined on 01/01/24.",
            "Ambiance is great for people watching if you sit near the window. Alex our waiter is bilingual and has a pleasant personality that is helpful. The escargot was delicious, and the Cesar salad was plentiful. Actually could not finish it because it was so filling. Inside look on the walls, there are photos of a lot of the famous people that have dined here. Everyone enjoyed their lunch and we all would go back when in town. Enjoy!",
            "This is more of a spot to go for ambiance than the food itself. White tablecloth, expansive corner spot in Champs-Elysses, I've been told it's an institution of sorts. I found the food very average and the prices very high for the quality of the food, especially when there are so many restaurants in Paris. I ordered the beef tartare (spicy) and it was okay. Nothing super impressive in my opinion. I would even venture to say I've had better tartare in the city.",
            "My lovely bride and I did not plan on having lunch at Le Fouquet, but we were walking along the Avenue des Champs-Élysées on a Sunday afternoon when the rain started coming down and, of course, our umbrellas were nice and dry at our hotel. My bride odered the croque monsieur, which was accompanied by a mesclun salad and frites. I ordered the beef tartare, as well as the frites and mesclun. Best beef tartare and croque monsieur. The food and the service are outstanding. Our server, Pierre, was very helpful in his recommendations. For dessert, we highly recommend the café gourmand. This place rocks.",
            "Excelente food and outstanding service!! We decided to come here and enjoy our last meal in Paris. It didn't disappoint! Everything was delicious and our server gave us outstanding service! The ambience was so relaxing and enjoying the views of Champs Elysee.",
            "Given the location, you know there's going to be a lot of tourists. You also know that inexpensive is not going to happen, either. Given that they mention Pierre Gagnaire being involved with the menu, you assume it will be very good for that price. I believe it was.\nFor mains, I went with the lamb cutlets and the wife had the sea bream. They were both done perfectly. You can see they care about the details, down to the butter. We ate on the patio, so can't comment on what is supposed to be a very nice interior. Our server was very good and attentive. We were kind of down and out of the way, which in our case, was perfect. By the time we left, everything was full, but it was more private for a while.",
            "We were walking by on the Champs d'Elysee and saw the signs for Paris and New York restaurant. We came in for a glass of wine. What an adorable restaurant. Great service and the waiter was very kind to take pictures of us. The olives that came with the drinks were phenomenal. I had the Hermitage red wine which was fabulous."
        ]
    },
    {
        "restaurant": "chez-léon-paris",
        "reviews": [
            "Wonderful and charming little restaurant with fantastic drinks and food. Service was first class as well. Highly recommend and will definitely return.\nExcellent place to unwind from the world and enjoy great food/drinks in a comfortable and warm atmosphere!!!!",
            "God so amazing. Such simple fare but still delicious. I got a blood pudding sausage to die for and my friend got half a roasted chicken. With fries, Perrier and wine at under 40€ it was perfect. Decor is simple and so is the food."
        ]
    },
    {
        "restaurant": "le-comptoir-de-la-gastronomie-paris",
        "reviews": [
            "Given the location, you know there's going to be a lot of tourists. You also know that inexpensive is not going to happen, either. Given that they mention Pierre Gagnaire being involved with the menu, you assume it will be very good for that price. I believe it was.\nFor mains, I went with the lamb cutlets and the wife had the sea bream. They were both done perfectly. You can see they care about the details, down to the butter. We ate on the patio, so can't comment on what is supposed to be a very nice interior. Our server was very good and attentive. We were kind of down and out of the way, which in our case, was perfect. By the time we left, everything was full, but it was more private for a while.",
            "God so amazing. Such simple fare but still delicious. I got a blood pudding sausage to die for and my friend got half a roasted chicken. With fries, Perrier and wine at under 40€ it was perfect. Decor is simple and so is the food."
        ]
    }
]

def handler(event, context):
    # service = Service(ChromeDriverManager().install())
    # driver = webdriver.Chrome(service=service, options=options)
        print(dynamodb.meta.client.list_tables())
        print("ENV:", os.environ.get('ENV'))
        print("Table restaurant:", restaurants_table.table_name)
        print("Table avis:", avis_table.table_name)

        # all_reviews = [get_yelp_reviews(driver, restaurant) for restaurant in restaurants]
        for dat in data:
            persist_data(dat)

        return {
            "statusCode": 200,
            "body": {"test": "hey"}
        }




def persist_data(json_data): 
    try:
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
        print("data persist " + avis_table)
    except Exception as e:
        return {"error": str(e)}
