import sys
import os

# Add the current directory to the path so we can import directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import directly from the ML engine folder
from app.ml_engine.model_manager import NaiveBayesClassifier
from app.ml_engine.preprocessing.text_processor import TextProcessor

# --- Training Data (from your PDF) ---
phishing_texts = [
    "Cher client MTN, votre compte Mobile Money a été bloqué. Cliquez ici: http://mtn-secure.tk",
    "Orange Money: Transaction de 75000 FCFA en attente. Confirmez ici: http://orange-verify.ga",
    "URGENT: Votre compte Afriland a été compromis. Donnez votre mot de passe pour vérifier.",
    "Félicitations! Vous avez gagné 500,000 FCFA dans Momo Kash. Envoyez 5000 pour réclamer.",
    "Je suis un agent Orange. Donnez-moi votre code PIN pour sécuriser votre compte."
]
labels = [1, 1, 1, 1, 1] # 1 = Phishing

legit_texts = [
    "MTN: Votre transaction de 5000 FCFA a été effectuée. Solde: 25000. *126#",
    "Orange Money: Votre compte a été crédité de 10000 FCFA. *124#",
    "Votre commande a été expédiée. Vous pouvez la suivre via votre compte.",
    "Bonjour, la réunion est prévue à 14h demain.",
    "Votre relevé de compte mensuel est disponible."
]
labels += [0, 0, 0, 0, 0] # 0 = Legit

# Combine
all_texts = phishing_texts + legit_texts
all_labels = labels

# Train
print("Training PhishGuard-AI Model...")
model = NaiveBayesClassifier()
model.train(all_texts, all_labels)

# Save next to the ML package so the API can load it from any working directory.
model_dir = os.path.join(os.path.dirname(__file__), 'app', 'ml_engine', 'trained')
os.makedirs(model_dir, exist_ok=True)
model.save(os.path.join(model_dir, 'classifier.joblib'))
print("✅ Model trained and saved successfully!")