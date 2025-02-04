import json
import os
import boto3
import stanza
import re
import torch
from collections import Counter
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from decimal import Decimal


dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
restaurants_table = dynamodb.Table('restaurant-'+os.environ['ENV'])
avis_table = dynamodb.Table('avis-'+os.environ['ENV'])


model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)


stanza.download('en') 
nlp = stanza.Pipeline('en', processors='tokenize,mwt,pos,lemma')

def analyser_sentiment(avis):
    sentiments = []
    for commentaire in avis:
        inputs = tokenizer(commentaire, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = model(**inputs)
        prediction = torch.argmax(outputs.logits, dim=1).item() + 1
        sentiments.append("Négatif" if prediction in [1, 2] else "Neutre" if prediction == 3 else "Positif")
    return sentiments

def get_most_used_words(avis):
    text = ' '.join(avis)
    text = re.sub(r'[^a-zA-Zéèàùâêîôûç]+', ' ', text.lower())
    doc = nlp(text)
    words = [word.lemma for sentence in doc.sentences for word in sentence.words if word.upos in ['NOUN', 'ADJ', 'VERB']]
    return [word for word, _ in Counter(words).most_common(10)]

def handler(event, context):
    for restaurant_data in event:
        try:
            restaurant_name = restaurant_data["restaurant"]
            reviews = restaurant_data["reviews"]
            
            if not reviews:
                continue
            
            sentiments = analyser_sentiment(reviews)
            note_moyenne = sum(5 if s == "Positif" else 3 if s == "Neutre" else 1 for s in sentiments) / len(sentiments)
            sentiment_global = "Positif" if sentiments.count("Positif") > sentiments.count("Négatif") else "Négatif" if sentiments.count("Négatif") > sentiments.count("Positif") else "Neutre"
            most_used_words = get_most_used_words(reviews)


            restaurants_table.put_item(
                Item={
                    "idrestaurant": restaurant_name,
                    "note_moyenne": Decimal(str(round(note_moyenne, 1))),  # Conversion en Decimal
                    "sentiment_global": sentiment_global,
                    "mots_frequents": most_used_words
                }
            )

            for i, (review, sentiment) in enumerate(zip(reviews, sentiments)):
                mots_avis = get_most_used_words([review])
                avis_table.put_item(
                    Item={
                        "idavis": f"{restaurant_name}-{i}",
                        "idrestaurant": restaurant_name,
                        "avis": review,
                        "sentiment": sentiment,
                        "mots_frequents": mots_avis
                    }
                )

            print(f"Donnees inserees pour {restaurant_name}")
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps(f"Donnees inserees pour {restaurant_name}")
            }
        except Exception as e:
            print(f"Erreur avec {restaurant_data.get('restaurant', 'inconnu')}: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps("Erreur cote serveur")
            }
