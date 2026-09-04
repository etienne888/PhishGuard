import os
from .model_manager import NaiveBayesClassifier

def train_model():
    print("Training PhishGuard-AI Model...")
    
    # --- TRAINING DATA (You can add a lot more here! ---
    # 1. Real Scams (From your CIRT-CM and Cameroon research)
    phishing_texts = [
        "Cher client MTN, votre compte Mobile Money a été bloqué. Cliquez ici: http://mtn-secure.tk",
        "Orange Money: Transaction de 75000 FCFA en attente. Confirmez ici: http://orange-verify.ga",
        "URGENT: Votre compte Afriland a été compromis. Donnez votre mot de passe pour vérifier.",
        "Félicitations! Vous avez gagné 500,000 FCFA dans Momo Kash. Envoyez 5000 pour réclamer.",
        "Je suis un agent Orange. Donnez-moi votre code PIN pour sécuriser votre compte."
    ]
    labels = [1, 1, 1, 1, 1] # 1 = Phishing
    
    # 2. Legitimate Messages (From official MTN/Orange/Banks)
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
    model = NaiveBayesClassifier()
    model.train(all_texts, all_labels)
    
    # Save
    model_dir = os.path.join(os.path.dirname(__file__), 'trained')
    os.makedirs(model_dir, exist_ok=True)
    model.save(os.path.join(model_dir, 'classifier.joblib'))
    print("✅ Model trained and saved!")

if __name__ == "__main__":
    train_model()