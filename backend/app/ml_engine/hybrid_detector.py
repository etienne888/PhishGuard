import os

from .model_manager import NaiveBayesClassifier
from .heuristic_scorer import HeuristicScorer

class HybridDetector:
    def __init__(self):
        self.ml_model = NaiveBayesClassifier()
        self.heuristic = HeuristicScorer()
        model_path = os.path.join(os.path.dirname(__file__), 'trained', 'classifier.joblib')

        try:
            self.ml_model = self.ml_model.load(model_path)
            print("ML model loaded successfully.")
        except FileNotFoundError:
            print("ML model not trained yet; analysis is unavailable.")
    def analyze(self, text, sender_domain=None):
        # 1. Get Heuristic Score (0-100)
        heuristic_score = self.heuristic.score(text, sender_domain)
        
        # 2. Get ML Score (0.0 to 1.0) -> 0-100
        ml_prob = self.ml_model.predict_proba(text)
        ml_score = ml_prob * 100
        
        # 3. Combine (60% ML, 40% Heuristics)
        final_score = (heuristic_score * 0.4) + (ml_score * 0.6)
        
        # 4. Determine Risk Level
        if final_score > 80:
            verdict = 'Critical'
        elif final_score > 60:
            verdict = 'High'
        elif final_score > 40:
            verdict = 'Medium'
        else:
            verdict = 'Low'
            
        return {
            'score': round(final_score, 2),
            'verdict': verdict,
            'ml_score': round(ml_score, 2),
            'heuristic_score': round(heuristic_score, 2),
            'indicators': self._get_indicators(text, sender_domain)
        }

    def _get_indicators(self, text, sender_domain):
        # (You can expand this with your existing heuristic logic)
        return []