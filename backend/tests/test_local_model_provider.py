
from app.llm.local.config import LocalModelConfig
from app.llm.local.provider import LocalTransformersProvider


def test_local_provider_is_lazy():
    provider = LocalTransformersProvider(
        LocalModelConfig(model_id="demo/model")
    )
    assert provider.model_name == "demo/model"
    assert provider._model is None
    assert provider._tokenizer is None
