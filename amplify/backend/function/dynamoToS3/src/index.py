import json
import boto3
import os

def handler(event, context):
    print('Received event:')
    print(event)
    
    # Paramètres S3 et DynamoDB
    BUCKET_NAME = os.environ.get('STORAGE_BIGDATA_BUCKETNAME')
    DATA_KEY = "QuickSight/reviews_export.json"
    MANIFEST_KEY = "QuickSight/export_reviews_manifest.manifest"
    TABLE_NAME = os.environ.get('STORAGE_AVIS_NAME')
    
    # Initialiser les clients S3 et DynamoDB
    s3 = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(TABLE_NAME)
    
    # Récupérer tous les avis de la table DynamoDB
    try:
        response = table.scan()
        reviews = response.get('Items', [])
    except Exception as e:
        print(f"Error retrieving reviews: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps("Error retrieving reviews")
        }
    
    # Sauvegarder les avis en JSON dans S3
    reviews_json = json.dumps(reviews)
    try:
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=DATA_KEY,
            Body=reviews_json,
            ContentType='application/json'
        )
    except Exception as e:
        print(f"Error uploading reviews JSON: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps("Error uploading reviews JSON")
        }
    
    # Contenu du manifeste
    manifest_content = {
        "fileLocations": [
            {
                "URIPrefixes": [
                    f"s3://{BUCKET_NAME}/{DATA_KEY}"
                ]
            }
        ],
        "globalUploadSettings": {
            "format": "JSON",
            "containsHeader": "false"
        }
    }
    
    # Convertir en JSON
    manifest_json = json.dumps(manifest_content)
    
    # Enregistrer le manifeste dans S3
    try:
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=MANIFEST_KEY,
            Body=manifest_json,
            ContentType='application/json'
        )
        
        response_message = f"Manifest successfully uploaded to s3://{BUCKET_NAME}/{MANIFEST_KEY}"
    except Exception as e:
        print(f"Error uploading manifest: {str(e)}")
        response_message = "Error uploading manifest"
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(response_message)
    }
