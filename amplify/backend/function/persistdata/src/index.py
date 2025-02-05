import json
import os
import boto3
import stanza
import re
import torch
from collections import defaultdict, Counter
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

def fetch_data():
    
    restaurants = {item["idrestaurant"]: item for item in restaurants_table.scan()["Items"]}
    print(restaurants)
    avis = avis_table.scan()["Items"]

    grouped_reviews = defaultdict(list)
    for review in avis:
        grouped_reviews[review["idrestaurant"]].append(review["avis"])

    return restaurants, grouped_reviews

def process_data():
    
    restaurants, grouped_reviews = fetch_data()

    for restaurant_id, reviews in grouped_reviews.items():
        try:
            sentiments = analyser_sentiment(reviews)
            note_moyenne = sum(5 if s == "Positif" else 3 if s == "Neutre" else 1 for s in sentiments) / len(sentiments)
            sentiment_global = "Positif" if sentiments.count("Positif") > sentiments.count("Négatif") else "Négatif" if sentiments.count("Négatif") > sentiments.count("Positif") else "Neutre"
            most_used_words = get_most_used_words(reviews)
            adresse = restaurants.get(restaurant_id, {}).get("adresse", "Inconnue")

            
            restaurants_table.put_item(
                Item={
                    "idrestaurant": restaurant_id,
                    "adresse": adresse,
                    "note_moyenne": Decimal(str(round(note_moyenne, 1))),
                    "sentiment_global": sentiment_global,
                    "mots_frequents": most_used_words
                }
            )

            
            for review in avis_table.scan()["Items"]:
                if review["idrestaurant"] == restaurant_id:
                    mots_avis = get_most_used_words([review["avis"]])
                    avis_table.put_item(
                        Item={
                            "idavis": review["idavis"],
                            "idrestaurant": review["idrestaurant"],
                            "avis": review["avis"],
                            "sentiment": analyser_sentiment([review["avis"]])[0],
                            "mots_frequents": mots_avis
                        }
                    )

            print(f"Données mises à jour pour {restaurant_id}")

        except Exception as e:
            print(f"Erreur avec {restaurant_id}: {str(e)}")

def handler(event, context):
    process_data()
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps("Donnees mises a jour avec succes")
    }
