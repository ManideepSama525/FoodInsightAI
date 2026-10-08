from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("mime_type", sa.String(100)),
        sa.Column("source", sa.String(500)),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_documents_filename", "documents", ["filename"])
    op.create_index("ix_documents_document_type", "documents", ["document_type"])
    op.create_index("ix_documents_status", "documents", ["status"])

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer()),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index("ix_document_chunks_page_number", "document_chunks", ["page_number"])

    op.create_table(
        "queries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("mode", sa.String(50), nullable=False),
        sa.Column("processing_time_ms", sa.Integer()),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_queries_mode", "queries", ["mode"])

    op.create_table(
        "responses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("query_id", sa.String(36), sa.ForeignKey("queries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_responses_query_id", "responses", ["query_id"])

    op.create_table(
        "citations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("response_id", sa.String(36), sa.ForeignKey("responses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="SET NULL")),
        sa.Column("chunk_id", sa.String(36)),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("source", sa.String(1000), nullable=False),
        sa.Column("page", sa.Integer()),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_citations_response_id", "citations", ["response_id"])
    op.create_index("ix_citations_document_id", "citations", ["document_id"])
    op.create_index("ix_citations_chunk_id", "citations", ["chunk_id"])

def downgrade():
    op.drop_table("citations")
    op.drop_table("responses")
    op.drop_table("queries")
    op.drop_table("document_chunks")
    op.drop_table("documents")
