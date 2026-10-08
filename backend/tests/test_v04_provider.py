from app.llm.local.provider import SYSTEM_INSTRUCTION, LocalTransformersProvider


class Config:
    model_id = "test-model"
    revision = None
    trust_remote_code = True
    load_in_4bit = False
    load_in_8bit = False
    device = "cpu"
    max_new_tokens = 128
    temperature = 0.0
    top_p = 1.0


def test_v04_prompt_matches_validated_structure():
    provider = LocalTransformersProvider(Config())
    prompt = provider._build_prompt(
        "How much protein?",
        "Protein is 20 g per 100 g.",
    )
    assert prompt.startswith("System:\n")
    assert SYSTEM_INSTRUCTION in prompt
    assert "Question:\nHow much protein?" in prompt
    assert "Evidence:\nProtein is 20 g per 100 g." in prompt
    assert "Give a concise evidence-grounded answer." in prompt
    assert prompt.endswith("Assistant:\n")


def test_provider_does_not_use_chat_template():
    source = LocalTransformersProvider.answer.__code__.co_names
    assert "apply_chat_template" not in source
