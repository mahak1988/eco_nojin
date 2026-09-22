"""
Generative AI for Local Knowledge Integration
==============================================

Provides:
- RAG (Retrieval-Augmented Generation) for farmer knowledge
- LLM-based calibration assistance
- Multilingual chat interface (14 languages)
- Knowledge graph construction from unstructured data
- Prompt engineering for scientific queries
- Voice/USSD integration for feature phones
"""

from __future__ import annotations

import logging
import warnings
import json
import hashlib
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, AsyncGenerator

import numpy as np

from engine.hydroma.models.base import ScientificModel
from engine.hydroma.models.expansion.registry import ModelDomain, ModelFidelity, ModelStatus, register_model

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeEntry:
    """Single entry in the knowledge base."""
    entry_id: str
    content: str
    language: str
    source: str  # farmer_interview, extension_officer, literature, sensor_log
    location: Optional[Dict[str, float]] = None  # lat, lon, admin_level
    crop: Optional[str] = None
    season: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "content": self.content,
            "language": self.language,
            "source": self.source,
            "location": self.location,
            "crop": self.crop,
            "season": self.season,
            "topics": self.topics,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


@dataclass
class RAGQuery:
    """Query for RAG system."""
    query: str
    language: str = "en"
    location: Optional[Dict[str, float]] = None
    crop: Optional[str] = None
    top_k: int = 5
    similarity_threshold: float = 0.7
    filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGResponse:
    """Response from RAG system."""
    answer: str
    sources: List[KnowledgeEntry]
    confidence: float
    language: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    def embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for texts."""
        pass
    
    @abstractmethod
    def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for a single query."""
        pass


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local embedding provider using sentence-transformers."""
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Loaded embedding model: {model_name}, dim={self.dimension}")
        except ImportError:
            logger.warning("sentence-transformers not available, using mock")
            self.model = None
            self.dimension = 384
    
    def embed(self, texts: List[str]) -> np.ndarray:
        if self.model is None:
            return np.random.randn(len(texts), self.dimension).astype(np.float32)
        return self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    
    def embed_query(self, query: str) -> np.ndarray:
        return self.embed([query])[0]


class VectorStore(ABC):
    """Abstract vector store for similarity search."""
    
    @abstractmethod
    def add(self, embeddings: np.ndarray, metadata: List[Dict]) -> List[str]:
        """Add vectors to store."""
        pass
    
    @abstractmethod
    def search(self, query_embedding: np.ndarray, k: int, filters: Optional[Dict] = None) -> List[Tuple[str, float, Dict]]:
        """Search for similar vectors."""
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]) -> bool:
        """Delete vectors."""
        pass


class FAISSVectorStore(VectorStore):
    """FAISS-based vector store."""
    
    def __init__(self, dimension: int, index_path: Optional[Path] = None):
        try:
            import faiss
            self.faiss = faiss
            self.dimension = dimension
            self.index_path = index_path or Path("data/vector_store/faiss.index")
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use IVF index for scalability
            self.index = faiss.IndexFlatIP(dimension)
            self.metadata: Dict[int, Dict] = {}
            self._next_id = 0
            
            if self.index_path.exists():
                self.load()
                
            logger.info(f"Initialized FAISS index: dim={dimension}")
        except ImportError:
            logger.warning("FAISS not available, using mock")
            self.index = None
            self.metadata = {}
            self._next_id = 0
    
    def add(self, embeddings: np.ndarray, metadata: List[Dict]) -> List[str]:
        if self.index is None:
            return [f"mock_{i}" for i in range(len(embeddings))]
        
        ids = []
        for i, (emb, meta) in enumerate(zip(embeddings, metadata)):
            idx = self._next_id
            self.index.add(emb.reshape(1, -1))
            self.metadata[idx] = {**meta, "internal_id": idx}
            ids.append(str(idx))
            self._next_id += 1
        
        return ids
    
    def search(self, query_embedding: np.ndarray, k: int, filters: Optional[Dict] = None) -> List[Tuple[str, float, Dict]]:
        if self.index is None:
            return []
        
        k = min(k, self.index.ntotal)
        if k == 0:
            return []
        
        scores, indices = self.index.search(query_embedding.reshape(1, -1), k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            meta = self.metadata.get(idx, {})
            
            # Apply filters
            if filters:
                match = True
                for key, value in filters.items():
                    if meta.get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            results.append((str(idx), float(score), meta))
        
        return results
    
    def delete(self, ids: List[str]) -> bool:
        # FAISS doesn't support efficient deletion, rebuild needed
        logger.warning("FAISS deletion not implemented efficiently")
        return False
    
    def save(self) -> None:
        if self.index is not None:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            self.faiss.write_index(self.index, str(self.index_path))
            # Save metadata separately
            meta_path = self.index_path.with_suffix(".meta.json")
            meta_path.write_text(json.dumps(self.metadata))
    
    def load(self) -> None:
        if self.index is not None and self.index_path.exists():
            self.index = self.faiss.read_index(str(self.index_path))
            meta_path = self.index_path.with_suffix(".meta.json")
            if meta_path.exists():
                self.metadata = json.loads(meta_path.read_text())
                self._next_id = max(self.metadata.keys()) + 1 if self.metadata else 0


class KnowledgeGraph:
    """
    Knowledge graph for structured farmer knowledge.
    
    Nodes: Concepts (crops, practices, pests, soil_types, etc.)
    Edges: Relations (causes, treats, improves, requires, etc.)
    """
    
    def __init__(self, graph_path: Optional[Path] = None):
        try:
            import networkx as nx
            self.nx = nx
            self.graph = nx.MultiDiGraph()
            self.graph_path = graph_path or Path("data/knowledge_graph/graph.gpickle")
            self.graph_path.parent.mkdir(parents=True, exist_ok=True)
            
            if self.graph_path.exists():
                self.load()
                
            logger.info(f"Initialized knowledge graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        except ImportError:
            logger.warning("networkx not available")
            self.graph = None
    
    def add_entity(self, entity_id: str, entity_type: str, attributes: Dict[str, Any]) -> None:
        """Add entity to knowledge graph."""
        if self.graph is None:
            return
        self.graph.add_node(entity_id, type=entity_type, **attributes)
    
    def add_relation(self, source: str, target: str, relation: str, attributes: Dict[str, Any] = None) -> None:
        """Add relation between entities."""
        if self.graph is None:
            return
        self.graph.add_edge(source, target, relation=relation, **(attributes or {}))
    
    def query(self, entity_id: str, relation: Optional[str] = None, depth: int = 2) -> List[Dict]:
        """Query knowledge graph."""
        if self.graph is None or entity_id not in self.graph:
            return []
        
        results = []
        for target in self.nx.single_source_shortest_path_length(self.graph, entity_id, cutoff=depth):
            if target == entity_id:
                continue
            edge_data = self.graph.get_edge_data(entity_id, target)
            if relation and relation not in [d.get("relation") for d in edge_data.values()]:
                continue
            results.append({
                "entity": target,
                "data": self.graph.nodes[target],
                "relations": [d.get("relation") for d in edge_data.values()],
            })
        return results
    
    def extract_subgraph(self, entity_ids: List[str], depth: int = 2) -> Any:
        """Extract subgraph around entities."""
        if self.graph is None:
            return None
        
        nodes = set()
        for eid in entity_ids:
            if eid in self.graph:
                nodes.update(self.nx.single_source_shortest_path_length(self.graph, eid, cutoff=depth).keys())
        
        return self.graph.subgraph(nodes).copy()
    
    def save(self) -> None:
        if self.graph is not None:
            self.graph_path.parent.mkdir(parents=True, exist_ok=True)
            self.nx.write_gpickle(self.graph, self.graph_path)
    
    def load(self) -> None:
        if self.graph is not None and self.graph_path.exists():
            self.graph = self.nx.read_gpickle(self.graph_path)


class RAGEngine:
    """
    Retrieval-Augmented Generation engine for farmer knowledge.
    
    Pipeline:
    1. Query embedding
    2. Vector search (with filters)
    3. Knowledge graph enrichment
    4. Prompt construction
    5. LLM generation
    6. Response validation
    """
    
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        knowledge_graph: Optional[KnowledgeGraph] = None,
        llm_client: Optional[Any] = None,
        system_prompt: Optional[str] = None,
    ):
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.knowledge_graph = knowledge_graph
        self.llm_client = llm_client
        self.system_prompt = system_prompt or self._default_system_prompt()
        
        # Language-specific prompts
        self.prompts = self._load_prompts()
    
    def _default_system_prompt(self) -> str:
        return """You are an expert agricultural advisor for smallholder farmers. 
        Provide practical, actionable advice based on local knowledge and scientific principles.
        Always cite your sources. Be honest about uncertainty.
        Respond in the farmer's language."""
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load language-specific prompts."""
        return {
            "en": "Based on the following local knowledge and scientific data, answer the farmer's question.",
            "fa": "بر اساس دانش محلی و داده‌های علمی زیر، به سوال کشاورز پاسخ دهید.",
            "ar": "بناءً على المعرفة المحلية والبيانات العلمية التالية، أجب على سؤال المزارع.",
            "es": "Basado en el conocimiento local y los datos científicos siguientes, responde a la pregunta del agricultor.",
            "fr": "Sur la base des connaissances locales et des données scientifiques suivantes, répondez à la question de l'agriculteur.",
            "zh": "基于以下当地知识和科学数据，回答农民的问题。",
            "hi": "निम्नलिखित स्थानीय ज्ञान और वैज्ञानिक डेटा के आधार पर, किसान के प्रश्न का उत्तर दें।",
            "pt": "Com base no conhecimento local e nos dados científicos a seguir, responda à pergunta do agricultor.",
            "ru": "На основе следующих локальных знаний и научных данных ответьте на вопрос фермера.",
            "sw": "Kulingana na elimu ya kijiji na data ya kisayansi ifuatayo, jibu swali la mkulima.",
            "am": "የሚከተለውን የቦታ እውቀት እና የሳይንስ ውሂብ በመመለከት የገበሬውን ጥያቄ ይመልሱ።",
            "bn": "নিচের স্থানীয় জ্ঞান এবং বৈজ্ঞানিক তথ্যের ভিত্তিতে, কৃষকের প্রশ্নের উত্তর দিন।",
            "id": "Berdasarkan pengetahuan lokal dan data ilmiah berikut, jawab pertanyaan petani.",
            "vi": "Dựa trên kiến thức địa phương và dữ liệu khoa học dưới đây, hãy trả lời câu hỏi của nông dân.",
        }
    
    def add_knowledge(self, entries: List[KnowledgeEntry]) -> List[str]:
        """Add knowledge entries to vector store and knowledge graph."""
        # Generate embeddings
        texts = [e.content for e in entries]
        embeddings = self.embedding_provider.embed(texts)
        
        # Prepare metadata
        metadata = [e.to_dict() for e in entries]
        
        # Add to vector store
        ids = self.vector_store.add(embeddings, metadata)
        
        # Add to knowledge graph
        if self.knowledge_graph:
            for entry in entries:
                self.knowledge_graph.add_entity(
                    entry.entry_id,
                    "knowledge_entry",
                    {"content": entry.content, "language": entry.language, "source": entry.source}
                )
                if entry.crop:
                    self.knowledge_graph.add_relation(entry.entry_id, entry.crop, "mentions_crop")
                if entry.location:
                    loc_key = f"loc_{entry.location.get('lat', 0):.2f}_{entry.location.get('lon', 0):.2f}"
                    self.knowledge_graph.add_entity(loc_key, "location", entry.location)
                    self.knowledge_graph.add_relation(entry.entry_id, loc_key, "located_at")
        
        # Save vector store
        if hasattr(self.vector_store, 'save'):
            self.vector_store.save()
        
        return ids
    
    def query(self, rag_query: RAGQuery) -> RAGResponse:
        """Execute RAG query."""
        # Embed query
        query_embedding = self.embedding_provider.embed_query(rag_query.query)
        
        # Vector search
        filters = rag_query.filters.copy()
        if rag_query.location:
            # Add location-based filter (approximate)
            pass
        if rag_query.crop:
            filters["crop"] = rag_query.crop
        
        results = self.vector_store.search(
            query_embedding,
            k=rag_query.top_k,
            filters=filters if filters else None,
        )
        
        # Filter by similarity threshold
        results = [(id, score, meta) for id, score, meta in results if score >= rag_query.similarity_threshold]
        
        # Enrich with knowledge graph
        kg_context = []
        if self.knowledge_graph:
            for id, score, meta in results:
                kg_results = self.knowledge_graph.query(id, depth=1)
                kg_context.extend(kg_context)
        
        # Construct prompt
        context_texts = [meta.get("content", "") for _, _, meta in results]
        context = "\n\n".join([f"Source {i+1}: {text}" for i, text in enumerate(context_texts)])
        
        prompt = self._construct_prompt(rag_query, context, kg_context)
        
        # Generate response
        answer = self._generate(prompt, rag_query.language)
        
        # Validate response
        confidence = self._validate_response(answer, results)
        
        # Create source entries
        sources = [
            KnowledgeEntry(
                entry_id=id,
                content=meta.get("content", ""),
                language=meta.get("language", "en"),
                source=meta.get("source", "unknown"),
                confidence=score,
            )
            for id, score, meta in results
        ]
        
        return RAGResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            language=rag_query.language,
            metadata={"num_sources": len(sources), "kg_nodes": len(kg_context)},
        )
    
    def _construct_prompt(self, query: RAGQuery, context: str, kg_context: List) -> str:
        """Construct LLM prompt with context."""
        lang_prompt = self.prompts.get(query.language, self.prompts["en"])
        
        prompt = f"""{self.system_prompt}

{lang_prompt}

Context:
{context}

Knowledge Graph Context:
{json.dumps(kg_context, ensure_ascii=False, indent=2) if kg_context else "None"}

Farmer's Question ({query.language}):
{query.query}

Answer in {query.language}:"""
        
        return prompt
    
    def _generate(self, prompt: str, language: str) -> str:
        """Generate response using LLM."""
        if self.llm_client is None:
            return f"[Mock response for {language}] Based on the provided context, here is my advice..."
        
        # Use LLM client (OpenAI, Ollama, etc.)
        try:
            if hasattr(self.llm_client, 'chat'):
                # OpenAI-compatible
                response = self.llm_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=500,
                )
                return response.choices[0].message.content
            elif hasattr(self.llm_client, 'generate'):
                # Ollama or similar
                return self.llm_client.generate(prompt)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"Error generating response: {e}"
        
        return "[LLM unavailable]"
    
    def _validate_response(self, answer: str, sources: List) -> float:
        """Validate response quality."""
        # Simple heuristics
        confidence = 1.0
        
        if len(answer) < 50:
            confidence *= 0.5
        if len(sources) == 0:
            confidence *= 0.3
        if "I don't know" in answer or "unknown" in answer.lower():
            confidence *= 0.4
        
        return max(0.1, confidence)
    
    async def stream_query(self, rag_query: RAGQuery) -> AsyncGenerator[str, None]:
        """Stream query response for real-time UX."""
        # For streaming, we'd use LLM streaming API
        response = self.query(rag_query)
        
        # Simulate streaming
        words = response.answer.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.05)


class CalibrationAssistant:
    """
    LLM-assisted model calibration.
    
    Features:
    - Parameter suggestion based on literature
    - Sensitivity analysis interpretation
    - Calibration workflow guidance
    - Uncertainty communication
    """
    
    def __init__(self, rag_engine: RAGEngine, model_registry: Any = None):
        self.rag_engine = rag_engine
        self.model_registry = model_registry
    
    def suggest_parameters(
        self,
        model_name: str,
        location: Dict[str, float],
        crop: str,
        available_data: List[str],
    ) -> Dict[str, Any]:
        """Suggest calibration parameters for a model at a location."""
        # Query RAG for relevant literature
        query = RAGQuery(
            query=f"Calibration parameters for {model_name} for {crop} in region with lat={location.get('lat')}, lon={location.get('lon')}",
            language="en",
            location=location,
            crop=crop,
            top_k=10,
        )
        
        response = self.rag_engine.query(query)
        
        # Extract parameter suggestions from response
        return {
            "model": model_name,
            "location": location,
            "crop": crop,
            "literature_suggestions": response.answer,
            "sources": [s.to_dict() for s in response.sources],
            "confidence": response.confidence,
            "available_data": available_data,
        }
    
    def interpret_sensitivity(self, sensitivity_indices: Dict[str, np.ndarray]) -> str:
        """Interpret Sobol sensitivity indices for farmer."""
        if not sensitivity_indices:
            return "No sensitivity data available."
        
        S1 = sensitivity_indices.get("S1", [])
        ST = sensitivity_indices.get("ST", [])
        
        # Find most important parameters
        param_names = [f"param_{i}" for i in range(len(S1))]
        ranked = sorted(zip(param_names, S1, ST), key=lambda x: x[2], reverse=True)
        
        interpretation = "Parameter importance ranking (total effect):\n"
        for i, (name, s1, st) in enumerate(ranked[:5]):
            interpretation += f"{i+1}. {name}: First-order={s1:.3f}, Total={st:.3f}\n"
        
        return interpretation
    
    def guide_calibration_workflow(
        self,
        model_name: str,
        current_params: Dict[str, float],
        observations: Dict[str, float],
    ) -> Dict[str, Any]:
        """Guide calibration workflow step by step."""
        return {
            "step": 1,
            "action": "Define objective function",
            "description": "Choose between NSE, KGE, RMSE, or multi-objective",
            "suggested_objective": "KGE (balances correlation, bias, variability)",
            "current_parameters": current_params,
            "observations": observations,
            "next_steps": [
                "Run sensitivity analysis",
                "Identify calibratable parameters",
                "Set parameter bounds",
                "Run calibration algorithm (SCE-UA, DREAM, Bayesian)",
                "Validate with independent data",
            ],
        }


class VoiceInterface:
    """
    Voice interface for feature phone access.
    
    Supports:
    - USSD menu navigation
    - IVR (Interactive Voice Response)
    - SMS-based queries
    - Text-to-speech for responses
    """
    
    def __init__(self, rag_engine: RAGEngine, tts_client: Optional[Any] = None):
        self.rag_engine = rag_engine
        self.tts_client = tts_client
        self.sessions: Dict[str, Dict] = {}
    
    def handle_ussd(self, session_id: str, user_input: str, language: str = "en") -> str:
        """Handle USSD menu interaction."""
        if session_id not in self.sessions:
            self.sessions[session_id] = {"state": "main_menu", "language": language}
        
        session = self.sessions[session_id]
        
        if session["state"] == "main_menu":
            if user_input == "1":
                session["state"] = "ask_question"
                return "Please ask your farming question (voice or text):"
            elif user_input == "2":
                session["state"] = "weather"
                return "Enter your location (lat,lon) for weather:"
            elif user_input == "3":
                session["state"] = "market_prices"
                return "Enter crop name for market prices:"
            else:
                return self._main_menu(language)
        
        elif session["state"] == "ask_question":
            # Process as RAG query
            rag_query = RAGQuery(query=user_input, language=language)
            response = self.rag_engine.query(rag_query)
            session["state"] = "main_menu"
            return f"{response.answer}\n\n1. Ask another\n2. Weather\n3. Market prices\n0. Exit"
        
        return self._main_menu(language)
    
    def _main_menu(self, language: str) -> str:
        menus = {
            "en": "Welcome to Eco Nojin Advisory\n1. Ask farming question\n2. Weather forecast\n3. Market prices\n0. Exit",
            "fa": "به مشاوره اکو نوجین خوش آمدید\n۱. پرسش کشاورزی\n۲. پیش‌بینی آب و هوا\n۳. قیمت بازار\n۰. خروج",
        }
        return menus.get(language, menus["en"])
    
    async def text_to_speech(self, text: str, language: str) -> bytes:
        """Convert text to speech."""
        if self.tts_client:
            return await self.tts_client.synthesize(text, language)
        return b""


class FarmerKnowledgeIngestion:
    """
    Pipeline for ingesting farmer knowledge from various sources.
    
    Sources:
    - Field interviews (audio -> text -> structured)
    - Extension officer reports
    - SMS/USSD logs
    - Community forums
    - Satellite/drone annotations
    """
    
    def __init__(self, rag_engine: RAGEngine):
        self.rag_engine = rag_engine
    
    def ingest_interview(
        self,
        audio_path: Path,
        transcript: str,
        metadata: Dict[str, Any],
        language: str,
    ) -> KnowledgeEntry:
        """Ingest farmer interview."""
        entry = KnowledgeEntry(
            entry_id=hashlib.sha256(f"{audio_path}_{datetime.now(UTC).isoformat()}".encode()).hexdigest()[:16],
            content=transcript,
            language=language,
            source="farmer_interview",
            location=metadata.get("location"),
            crop=metadata.get("crop"),
            season=metadata.get("season"),
            topics=metadata.get("topics", []),
            confidence=0.9,
            metadata=metadata,
        )
        
        self.rag_engine.add_knowledge([entry])
        return entry
    
    def ingest_sms_log(self, sms_logs: List[Dict]) -> List[KnowledgeEntry]:
        """Ingest SMS/USSD interaction logs."""
        entries = []
        for log in sms_logs:
            entry = KnowledgeEntry(
                entry_id=hashlib.sha256(f"{log.get('phone')}_{log.get('timestamp')}".encode()).hexdigest()[:16],
                content=f"Q: {log.get('question')}\nA: {log.get('answer')}",
                language=log.get("language", "en"),
                source="ussd_sms",
                location=log.get("location"),
                crop=log.get("crop"),
                topics=log.get("topics", []),
                confidence=0.7,
                metadata=log,
            )
            entries.append(entry)
        
        self.rag_engine.add_knowledge(entries)
        return entries
    
    def ingest_extension_report(self, report: Dict) -> KnowledgeEntry:
        """Ingest extension officer report."""
        entry = KnowledgeEntry(
            entry_id=hashlib.sha256(f"ext_{report.get('officer_id')}_{report.get('date')}".encode()).hexdigest()[:16],
            content=report.get("content", ""),
            language=report.get("language", "en"),
            source="extension_officer",
            location=report.get("location"),
            crop=report.get("crop"),
            season=report.get("season"),
            topics=report.get("topics", []),
            confidence=0.95,
            metadata=report,
        )
        
        self.rag_engine.add_knowledge([entry])
        return entry


# Register generative AI components
register_model(
    model_class=RAGEngine,
    name="Farmer Knowledge RAG Engine",
    version="1.0.0",
    domain=ModelDomain.SOCIOECONOMIC,
    fidelity=ModelFidelity.DATA_DRIVEN,
    status=ModelStatus.EXPERIMENTAL,
    description="RAG engine for multilingual farmer knowledge retrieval and advisory",
    references=[
        "Lewis et al. (2020) Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
    ],
    doi="10.18653/v1/2020.acl-main.449",
    authors=["P. Lewis", "E. Perez", "A. Piktus", "et al."],
    tags=["rag", "llm", "farmer_knowledge", "multilingual", "advisory"],
)

register_model(
    model_class=CalibrationAssistant,
    name="Model Calibration Assistant",
    version="1.0.0",
    domain=ModelDomain.SOCIOECONOMIC,
    fidelity=ModelFidelity.DATA_DRIVEN,
    status=ModelStatus.EXPERIMENTAL,
    description="LLM-assisted model calibration guidance",
    references=[],
    tags=["calibration", "llm", "assistant", "sensitivity"],
)

register_model(
    model_class=VoiceInterface,
    name="Voice/USSD Advisory Interface",
    version="1.0.0",
    domain=ModelDomain.SOCIOECONOMIC,
    fidelity=ModelFidelity.DATA_DRIVEN,
    status=ModelStatus.EXPERIMENTAL,
    description="Voice and USSD interface for feature phone access",
    references=[],
    tags=["voice", "ussd", "ivrs", "feature_phone", "inclusive"],
)