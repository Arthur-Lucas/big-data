import json
import boto3
import os
import io
import matplotlib.pyplot as plt
from collections import Counter

# Initialisation des clients AWS
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Récupération des noms des tables et du bucket S3 depuis les variables d'environnement
table_restaurant = dynamodb.Table(os.environ["STORAGE_RESTAURANT_NAME"])
table_avis = dynamodb.Table(os.environ["STORAGE_AVIS_NAME"])
S3_BUCKET = os.environ["STORAGE_BIGDATA_BUCKETNAME"]

def generate_graphics(idrestaurant, avis_list, mots_frequents):
    """ Génère les graphiques et les envoie à S3 """
    
    # 📊 Histogramme des sentiments
    sentiments = [avis['sentiment'] for avis in avis_list]
    sentiment_counts = Counter(sentiments)

    fig, ax = plt.subplots()
    ax.bar(sentiment_counts.keys(), sentiment_counts.values(), color=['green', 'gray', 'red'])
    ax.set_xlabel("Sentiments")
    ax.set_ylabel("Nombre d'avis")
    ax.set_title(f"Répartition des sentiments pour {idrestaurant}")
    
    # Sauvegarde dans un buffer et envoi vers S3
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    s3_key_histogram = f"{idrestaurant}/histogram.png"
    s3.upload_fileobj(buf, S3_BUCKET, s3_key_histogram, ExtraArgs={'ContentType': 'image/png'})
    plt.close(fig)

    # 🥧 Camembert des mots fréquents
    fig, ax = plt.subplots()
    mots_counts = Counter(mots_frequents)
    mots, freqs = zip(*mots_counts.most_common(5)) if mots_counts else ([], [])  # Top 5 mots
    if mots and freqs:
        ax.pie(freqs, labels=mots, autopct='%1.1f%%', startangle=90)
        ax.set_title(f"Mots les plus fréquents - {idrestaurant}")
    else:
        ax.text(0.5, 0.5, "Aucun mot fréquent", ha='center', va='center')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    s3_key_piechart = f"{idrestaurant}/piechart.png"
    s3.upload_fileobj(buf, S3_BUCKET, s3_key_piechart, ExtraArgs={'ContentType': 'image/png'})
    plt.close(fig)

    # URLs des images
    s3_url_histogram = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key_histogram}"
    s3_url_piechart = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key_piechart}"
    
    return s3_url_histogram, s3_url_piechart

def handler(event, context):
    try:
        # Extraction des query params

        params = event.get('queryStringParameters', {})
        idrestaurant = params.get('idrestaurant')
        # idrestaurant = "le-fouquets-paris"

        if not idrestaurant:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing idrestaurant in query parameters'})
            }

        # Accès à la table restaurant
        response = table_restaurant.get_item(Key={'idrestaurant': idrestaurant})
        restaurant = response.get('Item')

        if not restaurant:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Restaurant not found'})
            }

        # Accès à la table avis pour récupérer les avis liés au restaurant
        response = table_avis.query(
            IndexName="idrestaurant",
            KeyConditionExpression="idrestaurant = :id",
            ExpressionAttributeValues={":id": idrestaurant}
        )
        avis_list = response.get('Items', [])

        if not avis_list:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'No reviews found'})
            }

        mots_frequents = restaurant.get('mot_les_plus_frequents', [])

        # Génération et envoi des graphiques à S3
        s3_url_histogram, s3_url_piechart = generate_graphics(idrestaurant, avis_list, mots_frequents)

        pre_signe_url_historigram = s3.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': f"{idrestaurant}/histogram.png"}, ExpiresIn=3600)
        pre_signe_url_piechart = s3.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': f"{idrestaurant}/piechart.png"}, ExpiresIn=3600)

        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'idrestaurant': idrestaurant,
                'histogram_url': pre_signe_url_historigram,
                'piechart_url': pre_signe_url_piechart
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
