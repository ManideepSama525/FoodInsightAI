# API Contract — Phase 1

Base path: `/api/v1`

## Health
`GET /health`

Returns:
```json
{"status":"ok"}
```

## Chat
`POST /chat`

Request:
```json
{
  "message": "What are the nutritional benefits of spinach?",
  "document_ids": [],
  "image_id": null,
  "mode": "assistant"
}
```

Response contract:
```json
{
  "answer": "...",
  "sources": [],
  "retrieved_chunks": [],
  "confidence": null,
  "warnings": [],
  "processing_time_ms": 0
}
```

## Upload
`POST /upload` with multipart form field `file`.

Phase 1 validates presence only. MIME allowlisting, size limits, content sniffing, malware-safe processing, persistence, parsing and indexing are implemented in later phases.
