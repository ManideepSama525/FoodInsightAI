from __future__ import annotations

import json

from neo4j import GraphDatabase

from app.knowledge.models import KnowledgeEntity, KnowledgeRelation


class Neo4jKnowledgeGraphStore:
    """Neo4j-backed implementation of the FoodInsight knowledge graph."""

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
    ):
        self.driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
        )

    def close(self) -> None:
        self.driver.close()

    def upsert_entity(
        self,
        entity: KnowledgeEntity,
    ) -> KnowledgeEntity:
        with self.driver.session() as session:
            session.run(
                """
                MERGE (e:KnowledgeEntity {entity_id: $entity_id})
                SET e.entity_type = $entity_type,
                    e.canonical_name = $canonical_name,
                    e.aliases = $aliases,
                    e.attributes_json = $attributes_json,
                    e.source_ids = $source_ids
                """,
                entity_id=entity.entity_id,
                entity_type=entity.entity_type,
                canonical_name=entity.canonical_name,
                aliases=entity.aliases,
                attributes_json=json.dumps(
                    entity.attributes,
                    ensure_ascii=False,
                ),
                source_ids=entity.source_ids,
            ).consume()

        return entity

    def add_relation(
        self,
        relation: KnowledgeRelation,
    ) -> KnowledgeRelation:
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:KnowledgeEntity {entity_id: $subject_id})
                MATCH (o:KnowledgeEntity {entity_id: $object_id})
                MERGE (s)-[r:KNOWLEDGE_RELATION {
                    relation_id: $relation_id
                }]->(o)
                SET r.predicate = $predicate,
                    r.confidence = $confidence,
                    r.source_ids = $source_ids,
                    r.metadata_json = $metadata_json
                """,
                relation_id=relation.relation_id,
                subject_id=relation.subject_id,
                object_id=relation.object_id,
                predicate=relation.predicate,
                confidence=relation.confidence,
                source_ids=relation.source_ids,
                metadata_json=json.dumps(
                    relation.metadata,
                    ensure_ascii=False,
                ),
            ).consume()

        return relation

    def get_entity(
        self,
        entity_id: str,
    ) -> KnowledgeEntity | None:
        with self.driver.session() as session:
            record = session.run(
                """
                MATCH (e:KnowledgeEntity {entity_id: $entity_id})
                RETURN e
                """,
                entity_id=entity_id,
            ).single()

        if record is None:
            return None

        node = record["e"]

        return KnowledgeEntity(
            entity_id=node["entity_id"],
            entity_type=node["entity_type"],
            canonical_name=node["canonical_name"],
            aliases=list(node.get("aliases") or []),
            attributes=json.loads(
                node.get("attributes_json") or "{}"
            ),
            source_ids=list(node.get("source_ids") or []),
        )

    def get_entities(self) -> list[KnowledgeEntity]:
        with self.driver.session() as session:
            records = session.run(
                """
                MATCH (e:KnowledgeEntity)
                RETURN e
                ORDER BY e.entity_id
                """
            )

            result = []

            for record in records:
                node = record["e"]

                result.append(
                    KnowledgeEntity(
                        entity_id=node["entity_id"],
                        entity_type=node["entity_type"],
                        canonical_name=node["canonical_name"],
                        aliases=list(node.get("aliases") or []),
                        attributes=json.loads(
                            node.get("attributes_json") or "{}"
                        ),
                        source_ids=list(
                            node.get("source_ids") or []
                        ),
                    )
                )

            return result

    @property
    def entities(self) -> dict[str, KnowledgeEntity]:
        return {
            entity.entity_id: entity
            for entity in self.get_entities()
        }

    def neighbors(
        self,
        entity_id: str,
        predicate: str | None = None,
    ) -> list[KnowledgeRelation]:

        with self.driver.session() as session:

            if predicate is None:
                records = session.run(
                    """
                    MATCH (s:KnowledgeEntity)-[r:KNOWLEDGE_RELATION]-(o:KnowledgeEntity)
                    WHERE s.entity_id = $entity_id
                       OR o.entity_id = $entity_id
                    RETURN
                        r.relation_id AS relation_id,
                        s.entity_id AS subject_id,
                        r.predicate AS predicate,
                        o.entity_id AS object_id,
                        r.confidence AS confidence,
                        r.source_ids AS source_ids,
                        r.metadata_json AS metadata_json
                    """,
                    entity_id=entity_id,
                )
            else:
                records = session.run(
                    """
                    MATCH (s:KnowledgeEntity)-[r:KNOWLEDGE_RELATION]-(o:KnowledgeEntity)
                    WHERE (s.entity_id = $entity_id
                       OR o.entity_id = $entity_id)
                      AND r.predicate = $predicate
                    RETURN
                        r.relation_id AS relation_id,
                        s.entity_id AS subject_id,
                        r.predicate AS predicate,
                        o.entity_id AS object_id,
                        r.confidence AS confidence,
                        r.source_ids AS source_ids,
                        r.metadata_json AS metadata_json
                    """,
                    entity_id=entity_id,
                    predicate=predicate,
                )

            return [
                KnowledgeRelation(
                    relation_id=record["relation_id"],
                    subject_id=record["subject_id"],
                    predicate=record["predicate"],
                    object_id=record["object_id"],
                    confidence=float(record["confidence"]),
                    source_ids=list(
                        record["source_ids"] or []
                    ),
                    metadata=json.loads(
                        record["metadata_json"] or "{}"
                    ),
                )
                for record in records
            ]
