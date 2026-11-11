"""Embedding model - HashingVectorizer"""
from typing import List
from sklearn.feature_extraction.text import HashingVectorizer
from langchain_core.embeddings import Embeddings

_FIXED_DIM = 256

class HashEmbeddings(Embeddings):
    def __init__(self):
        self._vectorizer = HashingVectorizer(
            n_features=_FIXED_DIM, alternate_sign=False, norm='l2')

    def __call__(self, input):
        return self.embed_documents(input)

    def name(self):
        return "hash_embeddings_256"

    def embed_documents(self, texts=None, input=None):
        if input is not None:
            texts = input
        if texts is None or (isinstance(texts, list) and len(texts) == 0):
            return []
        if isinstance(texts, str):
            texts = [texts]
        matrix = self._vectorizer.fit_transform(texts)
        return [row.toarray()[0].tolist() for row in matrix]

    def embed_query(self, text=None, input=None):
        if input is not None:
            text = input if isinstance(input, str) else input[0]
        if text is None:
            return []
        if isinstance(text, list):
            text = text[0]
        vec = self._vectorizer.transform([text])
        return vec.toarray()[0].tolist()

_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HashEmbeddings()
    return _embeddings