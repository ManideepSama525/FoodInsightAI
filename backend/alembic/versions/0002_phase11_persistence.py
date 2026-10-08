from alembic import op
import sqlalchemy as sa

revision = "0002_phase11_persistence"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "nutrients",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False, unique=True),
        sa.Column("unit", sa.String(30), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_nutrients_name", "nutrients", ["name"])

    op.create_table(
        "foods",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("serving_size_g", sa.Float(), nullable=False),
        sa.Column("source", sa.String(500), nullable=False),
        sa.Column("is_synthetic", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_foods_name", "foods", ["name"])

    op.create_table(
        "food_nutrients",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("food_id", sa.String(36), sa.ForeignKey("foods.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nutrient_id", sa.String(36), sa.ForeignKey("nutrients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount_per_100g", sa.Float(), nullable=False),
        sa.Column("source", sa.String(500), nullable=False),
    )
    op.create_index("ix_food_nutrients_food_id", "food_nutrients", ["food_id"])
    op.create_index("ix_food_nutrients_nutrient_id", "food_nutrients", ["nutrient_id"])

    op.create_table(
        "recipe_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("servings", sa.Integer(), nullable=False),
        sa.Column("instructions", sa.JSON(), nullable=False),
        sa.Column("dietary_tags", sa.JSON(), nullable=False),
        sa.Column("allergens", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_recipe_records_name", "recipe_records", ["name"])

    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("recipe_id", sa.String(36), sa.ForeignKey("recipe_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("food_id", sa.String(36), sa.ForeignKey("foods.id", ondelete="SET NULL")),
        sa.Column("ingredient_name", sa.String(255), nullable=False),
        sa.Column("quantity_g", sa.Float(), nullable=False),
    )
    op.create_index("ix_recipe_ingredients_recipe_id", "recipe_ingredients", ["recipe_id"])
    op.create_index("ix_recipe_ingredients_food_id", "recipe_ingredients", ["food_id"])

    op.create_table(
        "safety_evidence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("topic", sa.String(255), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("source", sa.String(1000), nullable=False),
        sa.Column("source_type", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("jurisdiction", sa.String(100)),
        sa.Column("effective_date", sa.String(50)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_safety_evidence_subject", "safety_evidence", ["subject"])
    op.create_index("ix_safety_evidence_topic", "safety_evidence", ["topic"])

    op.create_table(
        "trace_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("subject_id", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("timestamp", sa.String(50), nullable=False),
        sa.Column("location", sa.String(255)),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_trace_events_subject_id", "trace_events", ["subject_id"])
    op.create_index("ix_trace_events_event_type", "trace_events", ["event_type"])

    op.create_table(
        "feedback",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("subject_id", sa.String(255), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text()),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_feedback_subject_id", "feedback", ["subject_id"])

    op.create_table(
        "knowledge_entities",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("canonical_name", sa.String(500), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("source_ids", sa.JSON(), nullable=False),
    )
    op.create_index("ix_knowledge_entities_entity_type", "knowledge_entities", ["entity_type"])
    op.create_index("ix_knowledge_entities_canonical_name", "knowledge_entities", ["canonical_name"])

    op.create_table(
        "knowledge_relations",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("subject_id", sa.String(255), nullable=False),
        sa.Column("predicate", sa.String(100), nullable=False),
        sa.Column("object_id", sa.String(255), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source_ids", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_knowledge_relations_subject_id", "knowledge_relations", ["subject_id"])
    op.create_index("ix_knowledge_relations_predicate", "knowledge_relations", ["predicate"])
    op.create_index("ix_knowledge_relations_object_id", "knowledge_relations", ["object_id"])

    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("total_cases", sa.Integer(), nullable=False),
        sa.Column("passed_cases", sa.Integer(), nullable=False),
        sa.Column("pass_rate", sa.Float(), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("results_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

def downgrade():
    for table in [
        "evaluation_runs","knowledge_relations","knowledge_entities","feedback",
        "trace_events","safety_evidence","recipe_ingredients","recipe_records",
        "food_nutrients","foods","nutrients"
    ]:
        op.drop_table(table)
