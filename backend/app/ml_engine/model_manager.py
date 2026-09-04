import math
import joblib
from collections import Counter
from .preprocessing.text_processor import TextProcessor

class NaiveBayesClassifier:
    """A simple pure-python Naive Bayes classifier for phishing detection"""
    
    def __init__(self):
        self.processor = TextProcessor()
        self.class_priors = {}
        self.word_probs = {0: {}, 1: {}} # 0 = Legit, 1 = Phish
        self.vocab = set()

    def train(self, texts, labels):
        """Train the model on text data"""
        if len(texts) != len(labels) or not texts:
            raise ValueError("texts and labels must have the same non-zero length")
        if set(labels) != {0, 1}:
            raise ValueError("labels must contain both 0 (legitimate) and 1 (phishing)")

        # 1. Process texts
        processed_texts = [self.processor.clean_text(t) for t in texts]
        
        # 2. Count words per class
        class_counts = Counter(labels)
        total_docs = len(labels)
        self.class_priors = {cls: count/total_docs for cls, count in class_counts.items()}
        
        # 3. Count word frequencies per class
        word_freq = {0: Counter(), 1: Counter()}
        self.vocab = set()
        self.word_probs = {0: {}, 1: {}}
        for text, label in zip(processed_texts, labels):
            words = text.split()
            self.vocab.update(words)
            word_freq[label].update(words)
        
        # 4. Calculate probabilities with Laplace smoothing
        for cls in [0, 1]:
            total_words = sum(word_freq[cls].values())
            for word in self.vocab:
                self.word_probs[cls][word] = (word_freq[cls][word] + 1) / (total_words + len(self.vocab))

    def predict_proba(self, text):
        """Return probability that text is phishing (1.0 to 0.0)"""
        if set(self.class_priors) != {0, 1}:
            raise RuntimeError("The classifier must be trained before prediction")

        processed = self.processor.clean_text(text)
        words = processed.split()
        
        log_probs = {}
        for cls in [0, 1]:
            log_prob = math.log(self.class_priors[cls])
            for word in words:
                if word in self.word_probs[cls]:
                    log_prob += math.log(self.word_probs[cls][word])
            log_probs[cls] = log_prob
        
        # Normalize log probabilities with log-sum-exp to avoid overflow.
        maximum = max(log_probs.values())
        normalizer = maximum + math.log(
            sum(math.exp(value - maximum) for value in log_probs.values())
        )
        return math.exp(log_probs[1] - normalizer)

    def save(self, path):
        joblib.dump(self, path)

    def load(self, path):
        return joblib.load(path)