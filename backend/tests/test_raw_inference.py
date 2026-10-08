from app.research_intelligence.raw_inference import (
    SYSTEM_INSTRUCTION,
    build_foodinsight_prompt,
    generation_kwargs,
)


def test_raw_prompt_has_expected_sections():
    prompt = build_foodinsight_prompt(
        "How much protein?",
        "Protein is 20 g per 100 g.",
    )
    assert prompt.startswith("System:\n")
    assert SYSTEM_INSTRUCTION in prompt
    assert "Question:\nHow much protein?" in prompt
    assert "Evidence:\nProtein is 20 g per 100 g." in prompt
    assert prompt.endswith("Assistant:\n")


def test_generation_kwargs_are_deterministic():
    class T:
        pad_token_id = 151643
        eos_token_id = 151643

    kwargs = generation_kwargs(T(), max_new_tokens=128)
    assert kwargs["max_new_tokens"] == 128
    assert kwargs["do_sample"] is False
    assert kwargs["pad_token_id"] == 151643
    assert kwargs["eos_token_id"] == 151643
