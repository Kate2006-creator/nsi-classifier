import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from database import load_model

class SemanticClassifier:
    
    def __init__(self):
        self.model = load_model()
        self.etalon_names = []
        self.etalon_embeddings = None  
        self.etalon_clusters = []
        self.threshold = 0.3  # Порог уверенности
    
    def load_etalons(self, db):
        #Загружает эталоны из БД
        from models import Etalon
        
        etalons = db.query(Etalon).all()
        
        self.etalon_names = []
        self.etalon_embeddings = []  
        self.etalon_clusters = []
        
        for etalon in etalons:
            if etalon.embedding is not None:
                self.etalon_names.append(etalon.etalon_name)
                self.etalon_embeddings.append(np.array(etalon.embedding))
                self.etalon_clusters.append(etalon.cluster_id)

        if self.etalon_embeddings:
            self.etalon_embeddings = np.array(self.etalon_embeddings)
        else:
            self.etalon_embeddings = None  # Если нет эмбеддингов, ставим None
        
        print(f"Загружено {len(self.etalon_names)} эталонов")
        return len(self.etalon_names) > 0
    
    def classify(self, query):
        #Классифицирует запрос, возвращая лучший эталон
        if not query or query.strip() == "":
            return None, None, 0.0
        
        # Проверяем, загружены ли эмбеддинги
        if self.etalon_embeddings is None or len(self.etalon_embeddings) == 0:
            return None, None, 0.0
        
        if self.etalon_embeddings.size == 0:  # Проверка размера массива
            return None, None, 0.0
        
        # Получаем эмбеддинг запроса
        query_embedding = self.model.encode([query])[0].reshape(1, -1)
        
        # Считаем сходство со всеми эталонами
        similarities = cosine_similarity(query_embedding, self.etalon_embeddings)[0]
        
        # Находим лучший результат
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]
        
        # Если уверенность ниже порога - возвращаем None
        if best_score < self.threshold:
            return None, None, best_score
        
        return self.etalon_names[best_idx], self.etalon_clusters[best_idx], best_score
    
    def get_suggestions(self, query, limit=5):
        if not query or query.strip() == "":
            return []
        
        if self.etalon_embeddings is None or len(self.etalon_embeddings) == 0:
            return []
        
        if self.etalon_embeddings.size == 0:
            return []
        
        query_embedding = self.model.encode([query])[0].reshape(1, -1)
        similarities = cosine_similarity(query_embedding, self.etalon_embeddings)[0]
        
        # Получаем индексы 
        top_indices = np.argsort(similarities)[-limit:][::-1]
        
        suggestions = []
        for idx in top_indices:
            if similarities[idx] > self.threshold:
                suggestions.append({
                    'etalon_name': self.etalon_names[idx],
                    'cluster': self.etalon_clusters[idx],
                    'score': float(similarities[idx])
                })
        
        return suggestions

classifier = SemanticClassifier()