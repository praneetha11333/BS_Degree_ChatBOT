import numpy as np
import time
from dataclasses import dataclass


@dataclass
class CacheEntry:
    query: str
    answer: str
    embedding: list
    timestamp: float


class SemanticCache:
    def __init__(self, threshold: float = 0.92, ttl: float = 3600, max_size: int = 1000):
        self.threshold = threshold
        self.ttl = ttl
        self.max_size = max_size
        self.cache: list[CacheEntry] = []

    def _cosine(self, a, b) -> float:
        a, b = np.array(a), np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def get(self, embedding: list) -> str | None:
        now = time.time()
        best_sim, best_entry = 0.0, None
        for entry in self.cache:
            if (now - entry.timestamp) > self.ttl:
                continue
            sim = self._cosine(embedding, entry.embedding)
            if sim > best_sim:
                best_sim, best_entry = sim, entry
        if best_entry and best_sim >= self.threshold:
            return best_entry.answer
        return None

    def set(self, query: str, answer: str, embedding: list) -> None:
        if len(self.cache) >= self.max_size:
            self.cache.pop(0)
        self.cache.append(CacheEntry(query, answer, embedding, time.time()))
