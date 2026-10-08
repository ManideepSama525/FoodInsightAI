# RAG Design

## Phase 3 implementation

The RAG system now contains explicit components:

- `DocumentProcessor`
- `RecursiveChunker`
- `EmbeddingProvider`
- `QdrantVectorStore`
- `Retriever`
- `LexicalReranker`
- `ContextBuilder`
- `RAGIngestionService`
- `RAGPipeline`

### Ingestion

```text
uploaded document
      ↓
DocumentProcessor
      ↓
ParsedPage[]
      ↓
RecursiveChunker
      ↓
TextChunk[]
      ↓
EmbeddingProvider
      ↓
Qdrant
```

The same chunks are persisted in PostgreSQL for application-level provenance.

### Retrieval

```text
query
 ↓
embedding
 ↓
Qdrant top-K
 ↓
lexical/vector reranking
 ↓
ContextBuilder
 ↓
evidence + citation records
```

### OCR

Native PDF text extraction is attempted first. Pages with insufficient extracted text call an injectable OCR provider. Phase 3 includes a safe `NullOCRProvider`; a production OCR adapter can be connected without changing the document processor.

### Embeddings

The default Phase 3 development provider is a deterministic local embedding implementation. This keeps the project runnable without model downloads/API credentials. It is explicitly **not** a semantic-quality benchmark. A pretrained embedding provider should be configured for actual retrieval evaluation.

### Security boundary

Retrieved documents are evidence, not instructions. The eventual LLM prompt must place retrieved text in a clearly delimited evidence section and explicitly prohibit retrieved content from overriding system/application instructions.

### Provenance

Every chunk carries:
- document ID
- chunk ID
- chunk index
- page number
- source metadata

This allows response citations to point back to the originating document/page.
