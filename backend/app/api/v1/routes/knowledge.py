from fastapi import APIRouter, HTTPException, Query

from app.knowledge.bootstrap import bootstrap_demo_graph_neo4j
from app.knowledge.models import KnowledgeEntity, KnowledgeRelation, ResolutionResult
from app.knowledge.resolution import EntityResolver

router = APIRouter()
graph = bootstrap_demo_graph_neo4j()


@router.get("/entities/{entity_id}", response_model=KnowledgeEntity)
async def get_entity(entity_id: str):
    entity = graph.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.get(
    "/entities/{entity_id}/neighbors",
    response_model=list[KnowledgeRelation],
)
async def neighbors(
    entity_id: str,
    predicate: str | None = Query(default=None),
):
    if not graph.get_entity(entity_id):
        raise HTTPException(status_code=404, detail="Entity not found")
    return graph.neighbors(entity_id, predicate)


@router.get("/resolve", response_model=ResolutionResult)
async def resolve(q: str = Query(min_length=1, max_length=200)):
    resolver = EntityResolver(graph.get_entities())
    return resolver.resolve(q)
