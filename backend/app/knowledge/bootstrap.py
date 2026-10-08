from app.knowledge.models import KnowledgeEntity, KnowledgeRelation
from app.knowledge.store import KnowledgeGraphStore
from app.knowledge.neo4j_store import Neo4jKnowledgeGraphStore
from app.core.config import settings


def build_demo_graph() -> KnowledgeGraphStore:
    graph = KnowledgeGraphStore()

    entities = [
        KnowledgeEntity(
            entity_id="food:rice",
            entity_type="food",
            canonical_name="Cooked white rice",
            aliases=["rice", "cooked rice"],
            source_ids=["demo_catalog"],
        ),
        KnowledgeEntity(
            entity_id="food:lentils",
            entity_type="food",
            canonical_name="Cooked lentils",
            aliases=["lentils", "dal"],
            source_ids=["demo_catalog"],
        ),
        KnowledgeEntity(
            entity_id="nutrient:protein",
            entity_type="nutrient",
            canonical_name="Protein",
            aliases=["protein"],
            source_ids=["demo_schema"],
        ),
        KnowledgeEntity(
            entity_id="recipe:lentil-rice",
            entity_type="recipe",
            canonical_name="Lentil Rice Bowl",
            aliases=["lentil rice"],
            source_ids=["demo_recipe"],
        ),
    ]

    for entity in entities:
        graph.upsert_entity(entity)

    graph.add_relation(
        KnowledgeRelation(
            relation_id="rel:recipe-lentils",
            subject_id="recipe:lentil-rice",
            predicate="contains",
            object_id="food:lentils",
            confidence=1.0,
            source_ids=["demo_recipe"],
        )
    )

    graph.add_relation(
        KnowledgeRelation(
            relation_id="rel:recipe-rice",
            subject_id="recipe:lentil-rice",
            predicate="contains",
            object_id="food:rice",
            confidence=1.0,
            source_ids=["demo_recipe"],
        )
    )

    graph.add_relation(
        KnowledgeRelation(
            relation_id="rel:lentils-protein",
            subject_id="food:lentils",
            predicate="has_nutrient",
            object_id="nutrient:protein",
            confidence=1.0,
            source_ids=["demo_catalog"],
        )
    )

    return graph


def bootstrap_demo_graph_neo4j() -> Neo4jKnowledgeGraphStore:
    graph = Neo4jKnowledgeGraphStore(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )

    demo = build_demo_graph()

    for entity in demo.entities.values():
        graph.upsert_entity(entity)

    for relation in demo.relations.values():
        graph.add_relation(relation)

    return graph
