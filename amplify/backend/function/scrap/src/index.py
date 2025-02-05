import boto3
import os

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
restaurants_table = dynamodb.Table(os.environ["STORAGE_RESTAURANT_NAME"])
avis_table = dynamodb.Table(os.environ["STORAGE_AVIS_NAME"])

restaurants = [
    "le-comptoir-de-la-gastronomie-paris",
    "le-fouquets-paris",
    "chez-léon-paris",
]

def handler(event, context):
        for data in event:
            persist_data(data)

        return {
            "statusCode": 200,
            "body": {"state": "done"}
        }




def persist_data(json_data): 
    try:
        restaurants_table.put_item(
            Item={
                "idrestaurant": json_data["restaurant"],
                "adresse": json_data["adresse"]
            }
        )
        # Enregistrement des avis dans la table avis_table
        for i, review in enumerate(json_data["reviews"], start=1):
            avis_table.put_item(  
                Item={
                    "idavis": f"{json_data['restaurant']}-{i}", 
                    "idrestaurant": json_data["restaurant"],
                    "avis": review
                }
            )
        print("data persist " + avis_table)
    except Exception as e:
        return {"error": str(e)}
