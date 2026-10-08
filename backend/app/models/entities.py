from datetime import datetime
import uuid
from sqlalchemy import Boolean,String, Text, DateTime, ForeignKey, Integer, JSON, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

class Document(TimestampMixin, Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(255), index=True)
    storage_path: Mapped[str] = mapped_column(String(1000))
    document_type: Mapped[str] = mapped_column(String(50), index=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="uploaded", index=True)
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

class DocumentChunk(TimestampMixin, Base):
    __tablename__ = "document_chunks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    document: Mapped["Document"] = relationship(back_populates="chunks")

class QueryLog(TimestampMixin, Base):
    __tablename__ = "queries"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_text: Mapped[str] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(50), default="assistant", index=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

class ResponseLog(TimestampMixin, Base):
    __tablename__ = "responses"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id: Mapped[str] = mapped_column(ForeignKey("queries.id", ondelete="CASCADE"), index=True)
    answer: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

class Citation(Base):
    __tablename__ = "citations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    response_id: Mapped[str] = mapped_column(ForeignKey("responses.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[str | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    chunk_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(1000))
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class Nutrient(TimestampMixin, Base):
    __tablename__ = "nutrients"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    unit: Mapped[str] = mapped_column(String(30))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

class Food(TimestampMixin, Base):
    __tablename__ = "foods"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), index=True)
    serving_size_g: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(500))
    is_synthetic: Mapped[bool] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

class FoodNutrient(Base):
    __tablename__ = "food_nutrients"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    food_id: Mapped[str] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"), index=True)
    nutrient_id: Mapped[str] = mapped_column(ForeignKey("nutrients.id", ondelete="CASCADE"), index=True)
    amount_per_100g: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(500))

class RecipeRecord(TimestampMixin, Base):
    __tablename__ = "recipe_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), index=True)
    servings: Mapped[int] = mapped_column(Integer)
    instructions: Mapped[list] = mapped_column(JSON, default=list)
    dietary_tags: Mapped[list] = mapped_column(JSON, default=list)
    allergens: Mapped[list] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

class RecipeIngredientRecord(Base):
    __tablename__ = "recipe_ingredients"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipe_records.id", ondelete="CASCADE"), index=True)
    food_id: Mapped[str | None] = mapped_column(ForeignKey("foods.id", ondelete="SET NULL"), nullable=True, index=True)
    ingredient_name: Mapped[str] = mapped_column(String(255))
    quantity_g: Mapped[float] = mapped_column(Float)

class SafetyEvidenceRecord(TimestampMixin, Base):
    __tablename__ = "safety_evidence"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject: Mapped[str] = mapped_column(String(500), index=True)
    topic: Mapped[str] = mapped_column(String(255), index=True)
    statement: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(1000))
    source_type: Mapped[str] = mapped_column(String(100))
    confidence: Mapped[float] = mapped_column(Float)
    jurisdiction: Mapped[str | None] = mapped_column(String(100), nullable=True)
    effective_date: Mapped[str | None] = mapped_column(String(50), nullable=True)

class TraceEventRecord(Base):
    __tablename__ = "trace_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id: Mapped[str] = mapped_column(String(255), index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    actor: Mapped[str] = mapped_column(String(255))
    timestamp: Mapped[str] = mapped_column(String(50), index=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

class FeedbackRecordEntity(TimestampMixin, Base):
    __tablename__ = "feedback"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id: Mapped[str] = mapped_column(String(255), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)

class KnowledgeEntityRecord(Base):
    __tablename__ = "knowledge_entities"
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(100), index=True)
    canonical_name: Mapped[str] = mapped_column(String(500), index=True)
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    source_ids: Mapped[list] = mapped_column(JSON, default=list)

class KnowledgeRelationRecord(Base):
    __tablename__ = "knowledge_relations"
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    subject_id: Mapped[str] = mapped_column(String(255), index=True)
    predicate: Mapped[str] = mapped_column(String(100), index=True)
    object_id: Mapped[str] = mapped_column(String(255), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    source_ids: Mapped[list] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

class EvaluationRunRecord(TimestampMixin, Base):
    __tablename__ = "evaluation_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    total_cases: Mapped[int] = mapped_column(Integer)
    passed_cases: Mapped[int] = mapped_column(Integer)
    pass_rate: Mapped[float] = mapped_column(Float)
    metrics_json: Mapped[list] = mapped_column(JSON, default=list)
    results_json: Mapped[list] = mapped_column(JSON, default=list)


class JobRecord(Base):
    __tablename__ = "job_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    subject_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="Queued")
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
