# Arthur LUCAS - Matis DENE - Pierre CAILLET

# Big Data

## 📌 Lien vers l'API

🔗 **URL de l'API** : [Big Data API](https://a9ncqj4vg9.execute-api.eu-west-1.amazonaws.com/arthur)

---

## 📚 Endpoints

### 🔍 Récupérer la liste de tous les restaurants

**GET** `/getRestaurants`

📌 **Description** :
Renvoie la liste de tous les restaurants enregistrés dans la base de données.

📥 **Paramètres** : Aucun

📤 **Réponse** (Exemple) :

```json
[
  {
    "idrestaurant": "NomDuRestaurant",
    "adresse": "123 Rue de Paris",
    "sentiment_global": "positif",
    "mots_frequents": ["délicieux", "rapide", "service"]
  },
  ...
]
```

---

### 📊 Récupérer les détails d’un restaurant

**GET** `/getRestaurant`

📌 **Description** :
Renvoie les détails d’un restaurant en fonction de son `idrestaurant`.

📥 **Query Parameters** :

- `idrestaurant` (**string**) : L'identifiant du restaurant à récupérer.

📤 **Réponse** (Exemple) :

```json
{
  "idrestaurant": "NomDuRestaurant",
  "histogram_url": "https://urlPresigne.png",
  "piechart_url": "https://urlPresigne.png"
}
```
