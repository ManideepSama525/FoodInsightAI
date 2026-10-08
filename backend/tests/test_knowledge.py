from app.knowledge.bootstrap import build_demo_graph
from app.knowledge.resolution import EntityResolver, normalize_name

def test_graph_relationships():
    graph = build_demo_graph()
    neighbors = graph.neighbors("recipe:lentil-rice", "contains")
    assert len(neighbors) == 2

def test_exact_entity_resolution():
    graph = build_demo_graph()
    result = EntityResolver(list(graph.entities.values())).resolve("dal")
    assert result.resolved_entity_id == "food:lentils"
    assert result.resolution_status == "resolved_exact"

def test_normalization():
    assert normalize_name("  Cooked-Rice! ") == "cooked rice"
