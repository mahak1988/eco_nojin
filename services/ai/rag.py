"""RAG — retrieval over the project's Persian knowledge base (free, no API).

BM25 (pure Python, no dependencies) over `docs/fa/*.md`, chunked by
headings. Retrieval is deterministic and works offline.
"""
import math
import re
from pathlib import Path
from typing import Dict, List, Tuple

_DOC_DIR = Path("docs/fa")
_STOP = set("به از و یا در با که این آن را برای از بر تا هم نیز فقط هر خود ما شما".split())


def _tokenize(text: str) -> List[str]:
    return [t for t in re.findall(r"[\w\u0600-\u06FF]{2,}", text.lower()) if t not in _STOP]


class BM25Index:
    def __init__(self) -> None:
        self.docs: List[Dict] = []
        self._df: Dict[str, int] = {}
        self._avgdl = 1.0
        self._built = False

    def build(self, doc_dir: Path = _DOC_DIR) -> int:
        """Index every .md file in doc_dir, chunked by '## ' headings."""
        self.docs = []
        if not doc_dir.exists():
            return 0
        for md in sorted(doc_dir.glob("*.md")):
            text = md.read_text(encoding="utf-8", errors="ignore")
            chunks = re.split(r"(?m)^## ", text)
            for chunk in chunks:
                if len(chunk.strip()) < 40:
                    continue
                title = chunk.split("\n", 1)[0].strip()[:90]
                self.docs.append({"file": md.name, "title": title, "text": chunk[:1400]})
        self._df = {}
        doc_freq: Dict[str, int] = {}
        total_len = 0
        for d in self.docs:
            toks = set(_tokenize(d["text"]))
            for t in toks:
                doc_freq[t] = doc_freq.get(t, 0) + 1
            total_len += len(_tokenize(d["text"]))
        self._df = doc_freq
        self._avgdl = max(1.0, total_len / max(1, len(self.docs)))
        self._built = True
        return len(self.docs)

    def search(self, query: str, k: int = 3) -> List[Dict]:
        if not self._built:
            self.build()
        q_toks = _tokenize(query)
        if not q_toks or not self.docs:
            return []
        n = len(self.docs)
        scored: List[Tuple[float, int]] = []
        for i, d in enumerate(self.docs):
            toks = _tokenize(d["text"])
            dl = len(toks)
            score = 0.0
            for t in q_toks:
                if t not in self._df:
                    continue
                tf = toks.count(t)
                df = self._df[t]
                idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
                score += idf * (tf * 1.5) / (tf + 1.5 * (0.25 + 0.75 * dl / self._avgdl))
            scored.append((score, i))
        scored.sort(reverse=True)
        return [{"file": self.docs[i]["file"], "title": self.docs[i]["title"], "text": self.docs[i]["text"][:400], "score": round(s, 3)} for s, i in scored[:k]]


index = BM25Index()
