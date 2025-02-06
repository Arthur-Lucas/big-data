import json
import boto3
import os
import io
import matplotlib.pyplot as plt
from collections import Counter
from wordcloud import WordCloud

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

table_restaurant = dynamodb.Table(os.environ["STORAGE_RESTAURANT_NAME"])
table_avis = dynamodb.Table(os.environ["STORAGE_AVIS_NAME"])
S3_BUCKET = os.environ["STORAGE_BIGDATA_BUCKETNAME"]

def generate_graphics(idrestaurant, avis_list, mots_frequents):
    try:
        sentiments = [avis['sentiment'] for avis in avis_list]
        sentiment_counts = Counter(sentiments)

        fig, ax = plt.subplots()
        ax.bar(sentiment_counts.keys(), sentiment_counts.values(), color=['green', 'gray', 'red'])
        ax.set_xlabel("Sentiments")
        ax.set_ylabel("Nombre d'avis")
        ax.set_title(f"Répartition des sentiments pour {idrestaurant}")
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        s3_key_histogram = f"{idrestaurant}/histogram.png"
        s3.upload_fileobj(buf, S3_BUCKET, s3_key_histogram, ExtraArgs={'ContentType': 'image/png'})
        plt.close(fig)

        if mots_frequents:
            mots_counts = Counter(mots_frequents)
            wordcloud = WordCloud(width=800, height=400, background_color="white").generate_from_frequencies(mots_counts)
            
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.imshow(wordcloud, interpolation="bilinear")
            ax.axis("off")
            ax.set_title(f"Nuage de mots - {idrestaurant}")

            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            s3_key_wordcloud = f"{idrestaurant}/wordcloud.png"
            s3.upload_fileobj(buf, S3_BUCKET, s3_key_wordcloud, ExtraArgs={'ContentType': 'image/png'})
            plt.close(fig)
        else:
            s3_key_wordcloud = None

        s3_url_histogram = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key_histogram}"
        s3_url_wordcloud = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key_wordcloud}" if s3_key_wordcloud else None
        
        return s3_url_histogram, s3_url_wordcloud
    except Exception as e:
        print(f"Error: {str(e)}")
        return None, None

def handler(event, context):
    try:
        
        try:
            params = event.get('queryStringParameters', {})
            idrestaurant = params.get('idrestaurant')
        except Exception as e:
            print(f"Error: {str(e)}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid query parameters or missing idrestaurant'})
            }

        if not idrestaurant:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing idrestaurant in query parameters'})
            }

        response = table_restaurant.get_item(Key={'idrestaurant': idrestaurant})
        restaurant = response.get('Item')

        if not restaurant:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Restaurant not found'})
            }

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

        mots_frequents = restaurant.get('mots_frequents', [])

        generate_graphics(idrestaurant, avis_list, mots_frequents)

        pre_signe_url_historigram = s3.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': f"{idrestaurant}/histogram.png"}, ExpiresIn=3600)
        pre_signe_url_worldcloudurl = s3.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': f"{idrestaurant}/wordcloud.png"}, ExpiresIn=3600)

        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'idrestaurant': idrestaurant,
                'histogram_url': pre_signe_url_historigram,
                'worldcloud_url': pre_signe_url_worldcloudurl
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
