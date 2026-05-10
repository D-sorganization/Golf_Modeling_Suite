"""Comprehensive TDD test suite for RAG Knowledge Store.

This module provides test coverage for the KnowledgeStore and ConversationMemory
classes in the shared chat RAG package.

Test Categories:
    - Unit tests for Document and SearchResult dataclasses
    - KnowledgeStore CRUD operations
    - Search functionality and relevance scoring
    - Index persistence (save/load)
    - ConversationMemory tracking and summarization
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.shared.python.ai.rag.knowledge_store import (
    ConversationMemory,
    Document,
    KnowledgeStore,
    SearchResult,
    get_conversation_memory,
    get_knowledge_store,
)


class TestDocument:
    """Tests for the Document dataclass."""

    def test_document_creation(self) -> None:
        """Test basic document creation."""
        doc = Document(
            id="test_doc_1",
            content="This is test content.",
            metadata={"title": "Test Document", "source": "test"},
        )

        assert doc.id == "test_doc_1"
        assert doc.content == "This is test content."
        assert doc.metadata["title"] == "Test Document"
        assert doc.metadata["source"] == "test"
        assert doc.embedding is None
        assert isinstance(doc.created_at, str)

    def test_document_to_dict(self) -> None:
        """Test document serialization."""
        doc = Document(
            id="test_doc_2",
            content="Test content for serialization.",
            metadata={"key": "value"},
        )

        data = doc.to_dict()

        assert data["id"] == "test_doc_2"
        assert data["content"] == "Test content for serialization."
        assert data["metadata"]["key"] == "value"
        assert "created_at" in data

    def test_document_from_dict(self) -> None:
        """Test document deserialization."""
        data = {
            "id": "test_doc_3",
            "content": "Restored content.",
            "metadata": {"restored": True},
            "embedding": [0.1, 0.2, 0.3],
            "created_at": "2024-01-01T00:00:00",
        }

        doc = Document.from_dict(data)

        assert doc.id == "test_doc_3"
        assert doc.content == "Restored content."
        assert doc.metadata["restored"] is True
        assert doc.embedding == [0.1, 0.2, 0.3]
        assert doc.created_at == "2024-01-01T00:00:00"

    def test_document_default_metadata(self) -> None:
        """Test that default metadata is an empty dict."""
        doc = Document(id="test", content="content")

        assert doc.metadata == {}


class TestSearchResult:
    """Tests for the SearchResult dataclass."""

    def test_search_result_creation(self) -> None:
        """Test search result creation."""
        doc = Document(id="result_doc", content="Relevant content.")
        result = SearchResult(document=doc, score=0.95)

        assert result.document == doc
        assert result.score == 0.95


class TestKnowledgeStore:
    """Tests for the KnowledgeStore class."""

    @pytest.fixture
    def temp_index_dir(self) -> Path:
        """Create a temporary directory for test indexes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def knowledge_store(self, temp_index_dir: Path) -> KnowledgeStore:
        """Create a KnowledgeStore instance for testing."""
        return KnowledgeStore(app_context="test_app", index_dir=temp_index_dir)

    def test_initialization(self, knowledge_store: KnowledgeStore) -> None:
        """Test KnowledgeStore initialization."""
        assert knowledge_store.app_context == "test_app"
        assert knowledge_store.document_count == 0
        assert not knowledge_store._index_initialized

    def test_add_document(self, knowledge_store: KnowledgeStore) -> None:
        """Test adding a single document."""
        doc_id = knowledge_store.add_document(
            title="Test Title",
            content="Test content for the knowledge store.",
            metadata={"tag": "test"},
        )

        assert doc_id.startswith("test_app_test_title_")
        assert knowledge_store.document_count == 1

    def test_add_document_duplicate(self, knowledge_store: KnowledgeStore) -> None:
        """Test that duplicate documents are not added."""
        content = "Duplicate content test."

        doc_id_1 = knowledge_store.add_document("Duplicate", content)
        doc_id_2 = knowledge_store.add_document("Duplicate", content)

        assert doc_id_1 == doc_id_2
        assert knowledge_store.document_count == 1

    def test_add_documents_batch(self, knowledge_store: KnowledgeStore) -> None:
        """Test adding multiple documents at once."""
        documents = [
            ("Title 1", "Content 1", {"type": "doc"}),
            ("Title 2", "Content 2", None),
            ("Title 3", "Content 3", {"type": "article"}),
        ]

        doc_ids = knowledge_store.add_documents(documents)

        assert len(doc_ids) == 3
        assert knowledge_store.document_count == 3

    def test_remove_document(self, knowledge_store: KnowledgeStore) -> None:
        """Test removing a document."""
        doc_id = knowledge_store.add_document("To Remove", "Content to remove.")
        assert knowledge_store.document_count == 1

        result = knowledge_store.remove_document(doc_id)
        assert result is True
        assert knowledge_store.document_count == 0

    def test_remove_nonexistent_document(self, knowledge_store: KnowledgeStore) -> None:
        """Test removing a document that doesn't exist."""
        result = knowledge_store.remove_document("nonexistent")
        assert result is False

    def test_search_empty_store(self, knowledge_store: KnowledgeStore) -> None:
        """Test searching an empty store."""
        results = knowledge_store.search("query")
        assert results == []

    def test_search_no_matches(self, knowledge_store: KnowledgeStore) -> None:
        """Test search with no matching results."""
        knowledge_store.add_document("Test", "Content about physics engines")
        results = knowledge_store.search("completely unrelated query xyz")
        assert results == []

    def test_search_title_match(self, knowledge_store: KnowledgeStore) -> None:
        """Test search that matches document title."""
        knowledge_store.add_document(
            "Physics Engine Comparison",
            "Detailed comparison of MuJoCo, Drake, and Pinocchio.",
        )

        results = knowledge_store.search("physics engine", top_k=5)

        assert len(results) == 1
        assert results[0].score > 0
        assert "Physics Engine Comparison" in results[0].document.metadata["title"]

    def test_search_content_match(self, knowledge_store: KnowledgeStore) -> None:
        """Test search that matches document content."""
        knowledge_store.add_document(
            "Golf Biomechanics",
            "The golf swing involves complex coordination of "
            "shoulder rotation, hip torque, and wrist action.",
        )

        results = knowledge_store.search("shoulder rotation hip torque", top_k=5)

        assert len(results) == 1
        assert results[0].score > 0

    def test_search_relevance_ranking(self, knowledge_store: KnowledgeStore) -> None:
        """Test that search results are ranked by relevance."""
        # Document with title match should rank higher
        knowledge_store.add_document(
            "Energy Conservation",
            "Brief mention of energy.",
        )
        knowledge_store.add_document(
            "Other Topic",
            "Energy conservation is fundamental to physics simulations. "
            "Total mechanical energy must be conserved.",
        )

        results = knowledge_store.search("energy conservation", top_k=5)

        # Title match should rank first
        assert len(results) >= 1
        assert results[0].document.metadata["title"] == "Energy Conservation"

    def test_search_with_metadata_filter(self, knowledge_store: KnowledgeStore) -> None:
        """Test search with metadata filtering."""
        knowledge_store.add_document(
            "Doc 1",
            "Content about simulation.",
            metadata={"category": "simulation"},
        )
        knowledge_store.add_document(
            "Doc 2",
            "Content about validation.",
            metadata={"category": "validation"},
        )

        # Filter by category
        results = knowledge_store.search(
            "content",
            filter_metadata={"category": "simulation"},
        )

        assert len(results) == 1
        assert results[0].document.metadata["category"] == "simulation"

    def test_get_context_for_prompt(self, knowledge_store: KnowledgeStore) -> None:
        """Test getting formatted context for prompts."""
        knowledge_store.add_document(
            "Inverse Dynamics",
            "Inverse dynamics calculates joint torques from observed motion.",
        )

        context = knowledge_store.get_context_for_prompt("joint torques")

        assert "Inverse Dynamics" in context
        assert "joint torques" in context.lower()

    def test_get_context_empty_query(self, knowledge_store: KnowledgeStore) -> None:
        """Test context retrieval with no matches."""
        context = knowledge_store.get_context_for_prompt("xyz nonexistent")
        assert context == ""

    def test_build_index(self, knowledge_store: KnowledgeStore) -> None:
        """Test building an index from documents."""
        documents = [
            {"title": "Doc 1", "content": "First document content."},
            {"title": "Doc 2", "content": "Second document content."},
        ]

        knowledge_store.build_index(documents)

        assert knowledge_store.document_count == 2
        assert knowledge_store._index_initialized

    def test_save_and_load_index(self, temp_index_dir: Path) -> None:
        """Test index persistence."""
        store1 = KnowledgeStore(app_context="persist_test", index_dir=temp_index_dir)
        store1.add_document("Persistent Doc", "This content should persist.")
        store1._save_index()

        # Create new store instance and load
        store2 = KnowledgeStore(app_context="persist_test", index_dir=temp_index_dir)
        store2._load_index()

        assert store2.document_count == 1
        assert "Persistent Doc" in str(store2._documents.values())

    def test_clear_index(self, knowledge_store: KnowledgeStore) -> None:
        """Test clearing the index."""
        knowledge_store.add_document("Doc 1", "Content 1")
        knowledge_store.add_document("Doc 2", "Content 2")
        assert knowledge_store.document_count == 2

        knowledge_store.clear_index()

        assert knowledge_store.document_count == 0
        assert not knowledge_store._index_initialized


class TestConversationMemory:
    """Tests for the ConversationMemory class."""

    def test_initialization(self) -> None:
        """Test ConversationMemory initialization."""
        memory = ConversationMemory(max_tokens=1000)

        assert memory._max_tokens == 1000
        assert memory.message_count == 0
        assert memory.session_id is not None

    def test_custom_session_id(self) -> None:
        """Test custom session ID."""
        custom_id = "custom_session_123"
        memory = ConversationMemory(session_id=custom_id)

        assert memory.session_id == custom_id

    def test_add_message(self) -> None:
        """Test adding messages to memory."""
        memory = ConversationMemory()

        memory.add_message("user", "Hello, how are you?")
        memory.add_message("assistant", "I'm doing well, thank you!")

        assert memory.message_count == 2

    def test_get_context(self) -> None:
        """Test getting conversation context."""
        memory = ConversationMemory()
        memory.add_message("user", "Test question")
        memory.add_message("assistant", "Test answer")

        context = memory.get_context()

        assert len(context) == 2
        assert context[0]["role"] == "user"
        assert context[0]["content"] == "Test question"

    def test_get_context_with_summary(self) -> None:
        """Test context includes summary when present."""
        memory = ConversationMemory(max_tokens=100)

        # Add enough messages to trigger summarization
        for i in range(20):
            memory.add_message("user", f"User message {i}" * 10)
            memory.add_message("assistant", f"Assistant response {i}" * 10)

        context = memory.get_context()

        # Should have system message with summary plus recent messages
        assert len(context) > 0
        assert context[0]["role"] == "system"
        assert "Previous topics" in context[0]["content"]

    def test_clear_memory(self) -> None:
        """Test clearing conversation memory."""
        memory = ConversationMemory()
        memory.add_message("user", "Test message")
        assert memory.message_count == 1

        memory.clear()

        assert memory.message_count == 0
        assert memory._summary == ""

    def test_token_count_estimation(self) -> None:
        """Test that token count is estimated."""
        memory = ConversationMemory(max_tokens=100)

        # Add a message and check token count increased
        initial_count = memory._token_count
        memory.add_message("user", "This is a test message with some length.")

        assert memory._token_count > initial_count


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_get_knowledge_store(self, temp_index_dir: Path) -> None:
        """Test get_knowledge_store factory function."""
        store = get_knowledge_store(
            app_context="factory_test",
            index_dir=temp_index_dir,
        )

        assert isinstance(store, KnowledgeStore)
        assert store.app_context == "factory_test"

    def test_get_conversation_memory(self) -> None:
        """Test get_conversation_memory factory function."""
        memory = get_conversation_memory(max_tokens=500, session_id="test_session")

        assert isinstance(memory, ConversationMemory)
        assert memory._max_tokens == 500
        assert memory.session_id == "test_session"