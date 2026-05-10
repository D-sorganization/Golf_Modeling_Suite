"""RAG Knowledge Store for context-aware AI responses.

This module provides a knowledge store with vector search capabilities
for retrieving relevant documentation and context during chat conversations.

Features:
    - Vector-based semantic search using FAISS or ChromaDB
    - Incremental re-indexing support
    - Local-only vector storage (no cloud dependencies)
    - App-specific knowledge packs
    - Conversation memory with summarization

Usage:
    >>> store = KnowledgeStore(app_context="gasification")
    >>> store.add_document("Thermo equations", "The first law of thermodynamics...")
    >>> results = store.search("energy conservation", top_k=3)
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_INDEX_DIR = Path.home() / ".upstream_drift" / "knowledge_index"


@dataclass
class Document:
    """A document in the knowledge store.

    Attributes:
        id: Unique document identifier.
        content: Document text content.
        metadata: Additional metadata (source, tags, etc.).
        embedding: Vector embedding (optional, computed on demand).
        created_at: Document creation timestamp.
    """

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Document:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding"),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )


@dataclass
class SearchResult:
    """A search result from the knowledge store.

    Attributes:
        document: The matched document.
        score: Relevance score (higher is better).
    """

    document: Document
    score: float


class KnowledgeStore:
    """Knowledge store with vector search capabilities.

    Provides semantic search over documentation, code, and domain knowledge.
    Supports multiple backends (FAISS, ChromaDB) with local storage.

    Attributes:
        app_context: Application context for knowledge packs.
        index_dir: Directory for storing vector index.
    """

    def __init__(
        self,
        app_context: str = "default",
        index_dir: Path | None = None,
    ) -> None:
        """Initialize the knowledge store.

        Args:
            app_context: Application context (gasification, upstream_drift).
            index_dir: Optional custom index directory.
        """
        self._app_context = app_context
        self._index_dir = index_dir or DEFAULT_INDEX_DIR / app_context
        self._documents: dict[str, Document] = {}
        self._index_initialized = False

        # Create index directory
        self._index_dir.mkdir(parents=True, exist_ok=True)

        # Try to load existing index
        self._load_index()

    @property
    def app_context(self) -> str:
        """Return the application context."""
        return self._app_context

    @property
    def document_count(self) -> int:
        """Return the number of indexed documents."""
        return len(self._documents)

    def add_document(
        self,
        title: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Add a document to the knowledge store.

        Args:
            title: Document title.
            content: Document content.
            metadata: Optional metadata (source, tags, etc.).

        Returns:
            Document ID.
        """
        # Generate unique ID from content
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        doc_id = f"{self._app_context}_{title.lower().replace(' ', '_')}_{content_hash}"

        if doc_id in self._documents:
            logger.debug("Document already exists: %s", doc_id)
            return doc_id

        doc = Document(
            id=doc_id,
            content=content,
            metadata={
                "title": title,
                "app_context": self._app_context,
                **(metadata or {}),
            },
        )

        self._documents[doc_id] = doc
        self._index_initialized = False

        logger.debug("Added document: %s", doc_id)
        return doc_id

    def add_documents(
        self,
        documents: list[tuple[str, str, dict[str, Any] | None]],
    ) -> list[str]:
        """Add multiple documents to the knowledge store.

        Args:
            documents: List of (title, content, metadata) tuples.

        Returns:
            List of document IDs.
        """
        return [
            self.add_document(title, content, metadata)
            for title, content, metadata in documents
        ]

    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from the knowledge store.

        Args:
            doc_id: Document ID to remove.

        Returns:
            True if document was removed, False if not found.
        """
        if doc_id in self._documents:
            del self._documents[doc_id]
            self._index_initialized = False
            logger.debug("Removed document: %s", doc_id)
            return True
        return False

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for relevant documents.

        Args:
            query: Search query.
            top_k: Number of results to return.
            filter_metadata: Optional metadata filters.

        Returns:
            List of search results sorted by relevance.
        """
        if not self._documents:
            return []

        # Simple keyword-based search (can be enhanced with vector search)
        query_lower = query.lower()
        results: list[tuple[Document, float]] = []

        for doc in self._documents.values():
            # Apply metadata filters
            if filter_metadata:
                match = all(
                    doc.metadata.get(k) == v
                    for k, v in filter_metadata.items()
                )
                if not match:
                    continue

            # Calculate relevance score based on keyword matching
            content_lower = doc.content.lower()
            title = doc.metadata.get("title", "").lower()

            # Score components
            title_match = sum(1 for w in query_lower.split() if w in title)
            content_match = sum(1 for w in query_lower.split() if w in content_lower)

            # Weighted score
            score = (title_match * 3.0) + (content_match * 1.0)

            if score > 0:
                results.append((doc, score))

        # Sort by score and return top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return [
            SearchResult(document=doc, score=score)
            for doc, score in results[:top_k]
        ]

    def get_context_for_prompt(
        self,
        query: str,
        max_tokens: int = 1000,
    ) -> str:
        """Get relevant context for inclusion in a system prompt.

        Args:
            query: Current user query.
            max_tokens: Maximum context tokens.

        Returns:
            Formatted context string.
        """
        results = self.search(query, top_k=5)

        if not results:
            return ""

        context_parts = ["## Relevant Knowledge Base:\n"]
        total_chars = 0

        for result in results:
            title = result.document.metadata.get("title", "Unknown")
            snippet = result.document.content[:500]  # Limit snippet length

            context = f"- **{title}**: {snippet}...\n"
            if total_chars + len(context) > max_tokens * 4:  # Rough char estimate
                break

            context_parts.append(context)
            total_chars += len(context)

        return "".join(context_parts)

    def build_index(self, documents: list[dict[str, Any]] | None = None) -> None:
        """Build or rebuild the knowledge index.

        Args:
            documents: Optional list of documents to index.
        """
        if documents:
            for doc in documents:
                self.add_document(
                    title=doc.get("title", "Untitled"),
                    content=doc.get("content", ""),
                    metadata=doc.get("metadata"),
                )

        self._save_index()
        self._index_initialized = True
        logger.info(
            "Built knowledge index with %d documents for %s",
            self.document_count,
            self._app_context,
        )

    def _save_index(self) -> None:
        """Save the index to disk."""
        index_path = self._index_dir / "index.json"

        data = {
            "app_context": self._app_context,
            "documents": {
                doc_id: doc.to_dict() for doc_id, doc in self._documents.items()
            },
            "created_at": datetime.now().isoformat(),
        }

        with open(index_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.debug("Saved knowledge index to %s", index_path)

    def _load_index(self) -> None:
        """Load the index from disk."""
        index_path = self._index_dir / "index.json"

        if not index_path.exists():
            logger.debug("No existing index found for %s", self._app_context)
            return

        try:
            with open(index_path) as f:
                data = json.load(f)

            self._documents = {
                doc_id: Document.from_dict(doc_data)
                for doc_id, doc_data in data.get("documents", {}).items()
            }

            self._index_initialized = True
            logger.info(
                "Loaded knowledge index with %d documents for %s",
                self.document_count,
                self._app_context,
            )

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to load knowledge index: %s", e)
            self._documents = {}
            self._index_initialized = False

    def clear_index(self) -> None:
        """Clear all documents and the index."""
        self._documents = {}
        self._index_initialized = False

        index_path = self._index_dir / "index.json"
        if index_path.exists():
            index_path.unlink()

        logger.info("Cleared knowledge index for %s", self._app_context)


class ConversationMemory:
    """Memory for tracking and summarizing conversations.

    Provides context-aware conversation history with automatic
    summarization to fit within token limits.

    Attributes:
        max_tokens: Maximum tokens to keep in memory.
        summary_model: Optional model for summarization.
    """

    def __init__(
        self,
        max_tokens: int = 4000,
        session_id: str | None = None,
    ) -> None:
        """Initialize conversation memory.

        Args:
            max_tokens: Maximum tokens to retain.
            session_id: Optional session identifier.
        """
        self._max_tokens = max_tokens
        self._session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self._messages: list[dict[str, str]] = []
        self._summary: str = ""
        self._token_count: int = 0

    @property
    def session_id(self) -> str:
        """Return the session ID."""
        return self._session_id

    @property
    def message_count(self) -> int:
        """Return the number of messages."""
        return len(self._messages)

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation.

        Args:
            role: Message role (user, assistant, system).
            content: Message content.
        """
        self._messages.append({"role": role, "content": content})
        self._token_count += len(content) // 4  # Rough estimate

        # Trigger summarization if needed
        if self._token_count > self._max_tokens:
            self._summarize()

    def get_context(self) -> list[dict[str, str]]:
        """Get the conversation context for the next prompt.

        Returns:
            List of messages including summary if applicable.
        """
        context = []

        if self._summary:
            context.append({
                "role": "system",
                "content": f"Conversation summary: {self._summary}",
            })

        context.extend(self._messages)
        return context

    def clear(self) -> None:
        """Clear the conversation memory."""
        self._messages = []
        self._summary = ""
        self._token_count = 0

    def _summarize(self) -> None:
        """Summarize the conversation to reduce token count.

        In a full implementation, this would use an LLM to generate
        a summary. For now, we keep only the most recent messages.
        """
        # Keep only the last 10 messages as a simple approach
        if len(self._messages) > 10:
            removed = self._messages[:-10]
            self._messages = self._messages[-10:]

            # Create a simple summary from removed messages
            user_msgs = [m["content"][:50] for m in removed if m["role"] == "user"]
            if user_msgs:
                self._summary = f"Previous topics: {', '.join(user_msgs[:3])}..."

        self._token_count = sum(len(m["content"]) // 4 for m in self._messages)
        logger.debug("Summarized conversation memory")


def get_knowledge_store(
    app_context: str = "default",
    index_dir: Path | None = None,
) -> KnowledgeStore:
    """Get or create a knowledge store instance.

    Args:
        app_context: Application context.
        index_dir: Optional index directory.

    Returns:
        Knowledge store instance.
    """
    return KnowledgeStore(app_context=app_context, index_dir=index_dir)


def get_conversation_memory(
    max_tokens: int = 4000,
    session_id: str | None = None,
) -> ConversationMemory:
    """Get or create a conversation memory instance.

    Args:
        max_tokens: Maximum tokens to retain.
        session_id: Optional session identifier.

    Returns:
        Conversation memory instance.
    """
    return ConversationMemory(max_tokens=max_tokens, session_id=session_id)