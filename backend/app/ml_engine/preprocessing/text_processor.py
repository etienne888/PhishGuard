import re
import unicodedata

class TextProcessor:
    def clean_text(self, text):
        # Lowercase
        text = text.lower()
        
        # Remove accents (French words like "bloqué" become "bloque")
        text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
        
        # Remove URLs (replace with placeholder)
        text = re.sub(r'http\S+', ' urlplaceholder ', text)
        
        # Remove special characters
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        
        return text.strip()

    def extract_features(self, text):
        """Generate specific features for the model"""
        features = {
            'length': len(text),
            'word_count': len(text.split()),
            'exclamation_count': text.count('!'),
            'urgency_words': sum(1 for w in ['urgent', 'immediat', 'bloque', 'suspendu'] if w in text),
            'momo_words': sum(1 for w in ['mtn', 'orange', 'momo', 'argent'] if w in text),
            'link_count': text.count('http')
        }
        return features