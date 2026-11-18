"""
Retrieval for the music recommender (the "R" in RAG).

Markdown files in data/knowledge/ are split into chunks (one per `##` section)
and indexed with BM25, a keyword-ranking formula. It is pure Python, so there
are no extra dependencies and no embedding service to run.
"""

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import List

DEFAULT_KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge"

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is",
    "it", "of", "on", "or", "the", "to", "with", "i", "me", "my", "want", "some",
}


@dataclass
class Chunk:
    source: str   # file name, e.g. "moods.md"
    heading: str  # the "##" section title
    text: str

    @property
    def citation(self) -> str:
        return f"{self.source} > {self.heading}"


def tokenize(text: str) -> List[str]:
    """Lowercase words, light plural stripping, stopwords removed."""
    words = re.findall(r"[a-z0-9&]+", text.lower())
    return [w[:-1] if len(w) > 3 and w.endswith("s") else w
            for w in words if w not in STOPWORDS]


def load_chunks(knowledge_dir: Path = DEFAULT_KNOWLEDGE_DIR) -> List[Chunk]:
    """Split every .md file in the folder into one Chunk per `##` section."""
    chunks: List[Chunk] = []
    for path in sorted(Path(knowledge_dir).glob("*.md")):
        heading, lines = None, []

        def flush():
            body = " ".join(lines).strip()
            if heading and body:
                chunks.append(Chunk(path.name, heading, body))

        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                flush()
                heading, lines = line[3:].strip(), []
            elif heading is not None:
                lines.append(line.strip())
        flush()
    return chunks


class Retriever:
    """BM25 search over a list of chunks."""

    def __init__(self, chunks: List[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks, self.k1, self.b = chunks, k1, b
        # The heading counts as part of the chunk so "Studying" finds its section.
        self._tokens = [tokenize(f"{c.heading} {c.heading} {c.text}") for c in chunks]
        self._tf = [Counter(t) for t in self._tokens]
        self._avg_len = sum(len(t) for t in self._tokens) / max(1, len(chunks))
        doc_freq = Counter(term for tokens in self._tokens for term in set(tokens))
        n = len(chunks)
        self._idf = {t: math.log(1 + (n - df + 0.5) / (df + 0.5)) for t, df in doc_freq.items()}

    @classmethod
    def from_directory(cls, knowledge_dir: Path = DEFAULT_KNOWLEDGE_DIR) -> "Retriever":
        return cls(load_chunks(knowledge_dir))

    def search(self, query: str, top_k: int = 3) -> List[Chunk]:
        """Return up to top_k chunks that match the query; none if nothing matches."""
        terms = tokenize(query)
        scored = []
        for i, tf in enumerate(self._tf):
            length = len(self._tokens[i])
            score = 0.0
            for term in terms:
                if term not in tf:
                    continue
                norm = tf[term] + self.k1 * (1 - self.b + self.b * length / self._avg_len)
                score += self._idf[term] * tf[term] * (self.k1 + 1) / norm
            if score > 0:
                scored.append((score, i))
        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        return [self.chunks[i] for _, i in scored[:top_k]]
