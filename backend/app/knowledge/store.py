from app.knowledge.models import KnowledgeEntity, KnowledgeRelation

class KnowledgeGraphStore:
    def __init__(self):
        self.entities: dict[str, KnowledgeEntity] = {}
        self.relations: dict[str, KnowledgeRelation] = {}

    def upsert_entity(self, entity: KnowledgeEntity) -> KnowledgeEntity:
        self.entities[entity.entity_id] = entity
        return entity

    def add_relation(self, relation: KnowledgeRelation) -> KnowledgeRelation:
        if relation.subject_id not in self.entities:
            raise ValueError(f"Unknown subject entity: {relation.subject_id}")
        if relation.object_id not in self.entities:
            raise ValueError(f"Unknown object entity: {relation.object_id}")
        self.relations[relation.relation_id] = relation
        return relation

    def get_entity(self, entity_id: str) -> KnowledgeEntity | None:
        return self.entities.get(entity_id)

    def neighbors(self, entity_id: str, predicate: str | None = None):
        results = []
        for relation in self.relations.values():
            if relation.subject_id == entity_id:
                if predicate is None or relation.predicate == predicate:
                    results.append(relation)
            elif relation.object_id == entity_id and predicate is None:
                results.append(relation)
        return results
