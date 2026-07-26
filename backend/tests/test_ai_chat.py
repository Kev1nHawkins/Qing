"""AI文化问答接口契约测试。"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.ai.dependencies import get_rag_service
from app.services.ai.rag_service import RAGAnswer, RAGSource


class StubRAGService:
    async def answer(self, question: str) -> RAGAnswer:
        if "电脑" in question:
            return RAGAnswer(
                question=question,
                answer="该问题不属于小棉的岭南文化知识范围，我暂时无法回答。",
                answerable=False,
                sources=[],
            )
        if "医疗功效" in question:
            return RAGAnswer(
                question=question,
                answer="当前知识库没有相关信息，无法准确回答。",
                answerable=True,
                sources=[
                    RAGSource(
                        source_path="01_hongmian.md",
                        title="木棉文化",
                        section="回答边界与人工确认项",
                        score=0.72,
                    )
                ],
            )
        return RAGAnswer(
            question=question,
            answer="木棉是广州市花，也是广州城市精神和英雄文化的重要象征。",
            answerable=True,
            sources=[
                RAGSource(
                    source_path="01_hongmian.md",
                    title="木棉文化",
                    section="木棉文化 > 常见问题 > Q1",
                    score=0.83,
                )
            ],
        )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_rag_service] = lambda: StubRAGService()
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_rag_service, None)


def test_cultural_question_returns_grounded_answer_and_source(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/ai/chat",
        json={"question": "为什么木棉是广州的象征？"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["message"] == "success"
    assert payload["requestId"]
    assert payload["data"]["answer"]
    assert payload["data"]["sources"][0]["source_path"] == "01_hongmian.md"


def test_unrelated_question_is_refused(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ai/chat",
        json={"question": "电脑无法开机应该怎样维修？"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert "不属于" in data["answer"]
    assert data["sources"] == []
    assert data["creation_suggestion"]["enable"] is False


def test_medical_question_is_refused(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ai/chat",
        json={"question": "木棉有哪些医疗功效？"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["answer"] == "当前知识库没有相关信息，无法准确回答。"
    assert data["creation_suggestion"] == {
        "enable": False,
        "culture": "",
        "campus": "",
        "style": "",
    }


def test_cultural_answer_returns_creation_suggestion(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ai/chat",
        json={"question": "为什么木棉是广州的象征？"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["creation_suggestion"] == {
        "enable": True,
        "culture": "木棉文化",
        "campus": "广州大学",
        "style": "国潮风",
    }
