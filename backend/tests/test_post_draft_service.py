import pytest

from app.core.config import Settings
from app.services.ai.llm_service import LLMNetworkError
from app.services.ai.post_draft_service import PostDraftService


def test_post_draft_parses_fenced_json() -> None:
    service = PostDraftService(Settings(llm_provider="mock"))
    draft = service._parse(
        '```json\n{"title":"校园新发现","content":"今天看见了新的校园风景。",'
        '"tags":["校园","#建筑","校园"]}\n```'
    )
    assert draft.title == "校园新发现"
    assert draft.content == "今天看见了新的校园风景。"
    assert draft.tags == ["校园", "建筑"]
    assert draft.fallback_used is False


@pytest.mark.asyncio
async def test_post_draft_provider_failure_uses_safe_fallback(monkeypatch) -> None:
    class FailingAdapter:
        async def generate(self, prompt: str) -> str:
            raise LLMNetworkError("secret-token-must-not-leak")

    monkeypatch.setattr(
        "app.services.ai.post_draft_service.DeepSeekLLM.from_settings",
        lambda settings: FailingAdapter(),
    )
    service = PostDraftService(
        Settings(llm_provider="deepseek", deepseek_api_key="test-key")
    )
    draft = await service.generate("介绍岭南建筑")
    assert draft.fallback_used is True
    assert draft.provider == "local-template"
    assert "secret-token" not in draft.content
