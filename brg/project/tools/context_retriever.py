from __future__ import annotations

import warnings
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Tuple

# Try to import sentence-transformers, but make it optional
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    SentenceTransformer = None

# Try to import numpy for semantic search
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None


class ContextRetriever:
    """
    Retrieve relevant context snippets using keyword or semantic search.
    
    Supports both simple keyword matching and semantic search with embeddings.
    Falls back gracefully to keyword search if embeddings are not available.
    """
    
    def __init__(
        self,
        snippets: List[dict[str, str]],
        use_embeddings: bool = True,
        embeddings_model: str = "all-MiniLM-L6-v2",
        cache_dir: Optional[Path] = None,
    ) -> None:
        """
        Initialize the context retriever.
        
        Args:
            snippets: List of snippet dictionaries with 'content' key
            use_embeddings: Whether to use semantic search (requires sentence-transformers)
            embeddings_model: Model name for sentence-transformers
            cache_dir: Directory to cache embeddings and model
        """
        self.snippets = snippets
        self.use_embeddings = use_embeddings and EMBEDDINGS_AVAILABLE
        self.embeddings_model_name = embeddings_model
        self.cache_dir = cache_dir
        
        # Initialize embeddings if requested and available
        self._model = None
        self._embeddings = None
        
        if self.use_embeddings and not EMBEDDINGS_AVAILABLE:
            warnings.warn(
                "sentence-transformers not available. Falling back to keyword search. "
                "Install with: pip install sentence-transformers"
            )
            self.use_embeddings = False
        
        if self.use_embeddings:
            self._initialize_embeddings()

    @lru_cache(maxsize=1)
    def _load_model(self) -> SentenceTransformer:
        """Load the sentence transformer model (cached)."""
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers not available")
        
        cache_folder = str(self.cache_dir) if self.cache_dir else None
        return SentenceTransformer(self.embeddings_model_name, cache_folder=cache_folder)
    
    def _initialize_embeddings(self) -> None:
        """Precompute embeddings for all snippets."""
        if not self.snippets:
            return
        
        try:
            self._model = self._load_model()
            # Extract content from snippets
            contents = [snippet.get("content", "") for snippet in self.snippets]
            # Compute embeddings for all snippets
            self._embeddings = self._model.encode(contents, convert_to_tensor=False)
        except Exception as e:
            warnings.warn(f"Failed to initialize embeddings: {e}. Falling back to keyword search.")
            self.use_embeddings = False
            self._model = None
            self._embeddings = None

    def _retrieve_keyword(self, query: str, limit: int = 3) -> List[str]:
        """
        Retrieve snippets using simple keyword matching.
        
        Scores snippets based on number of overlapping tokens between query and content.
        
        Args:
            query: Search query
            limit: Maximum number of results
        
        Returns:
            List of snippet contents, ordered by relevance
        """
        scored: List[Tuple[int, str]] = []
        lowered = query.lower()
        
        for snippet in self.snippets:
            content = snippet.get("content", "")
            tokens = set(content.lower().split())
            score = sum(1 for token in lowered.split() if token in tokens)
            scored.append((score, content))
        
        scored.sort(key=lambda s: s[0], reverse=True)
        return [content for _, content in scored[:limit] if content]
    
    def _retrieve_semantic(self, query: str, limit: int = 3) -> List[str]:
        """
        Retrieve snippets using semantic similarity with embeddings.
        
        Uses cosine similarity between query embedding and snippet embeddings.
        
        Args:
            query: Search query
            limit: Maximum number of results
        
        Returns:
            List of snippet contents, ordered by semantic similarity
        """
        if self._model is None or self._embeddings is None or not NUMPY_AVAILABLE:
            # Fall back to keyword search
            return self._retrieve_keyword(query, limit)
        
        try:
            # Encode the query
            query_embedding = self._model.encode([query], convert_to_tensor=False)[0]
            
            # Compute cosine similarities
            similarities = np.dot(self._embeddings, query_embedding) / (
                np.linalg.norm(self._embeddings, axis=1) * np.linalg.norm(query_embedding)
            )
            
            # Get top-k indices
            top_indices = np.argsort(similarities)[::-1][:limit]
            
            # Return corresponding snippets
            results = []
            for idx in top_indices:
                content = self.snippets[idx].get("content", "")
                if content:
                    results.append(content)
            
            return results
        except Exception as e:
            warnings.warn(f"Semantic search failed: {e}. Falling back to keyword search.")
            return self._retrieve_keyword(query, limit)

    def retrieve(self, spec: str, limit: int = 3) -> List[str]:
        """
        Retrieve relevant snippets for the given specification.
        
        Uses semantic search if available, otherwise falls back to keyword search.
        
        Args:
            spec: Specification or query text
            limit: Maximum number of results to return
        
        Returns:
            List of relevant snippet contents
        """
        if self.use_embeddings:
            return self._retrieve_semantic(spec, limit)
        else:
            return self._retrieve_keyword(spec, limit)
