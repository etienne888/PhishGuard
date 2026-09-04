import sys
import os

# Add current directory to Python path to avoid importing app/__init__.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import directly from the ML engine
from app.ml_engine.model_manager import NaiveBayesClassifier

# Path to the model
base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, 'app', 'ml_engine', 'trained', 'classifier.joblib')

# Load the model
model = NaiveBayesClassifier()
model = model.load(model_path)

# Test with Scam
scam_text = "Cher client MTN, votre compte est bloqué. Cliquez ici: http://mtn-secure.tk"
scam_score = round(model.predict_proba(scam_text) * 100, 2)
print(f"🚨 Risk Score for SCAM: {scam_score}%")

# Test with Legit
legit_text = "MTN: Votre transaction de 5000 FCFA a été effectuée. Solde: 25000. *126#"
legit_score = round(model.predict_proba(legit_text) * 100, 2)
print(f"✅ Risk Score for LEGIT: {legit_score}%")