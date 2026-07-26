"""成员3：岭南文化高频问题数据驱动验收。"""

from __future__ import annotations

import json
import re
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.ai.dependencies import get_rag_service
from app.services.ai.llm_service import LLMService, MockLLM
from app.services.ai.rag_service import RAGService


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = BACKEND_ROOT.parent
DATA_PATH = Path(__file__).parent / "data" / "culture_questions.json"
KNOWLEDGE_DIR = REPOSITORY_ROOT / "data" / "knowledge_base"
PROMPT_PATH = REPOSITORY_ROOT / "data" / "prompts" / "rag_chat.txt"

CASES: list[dict[str, Any]] = json.loads(DATA_PATH.read_text(encoding="utf-8"))
CULTURE_CASES = [case for case in CASES if case["expected_source"] is not None]
BOUNDARY_CASES = [case for case in CASES if case["expected_source"] is None]

REQUIRED_CATEGORIES = {
    "木棉文化",
    "岭南文化",
    "粤剧",
    "广绣",
    "广彩",
    "骑楼",
    "陈家祠",
    "广州早茶",
    "舞狮",
    "龙舟文化",
    "五羊传说",
    "广州大学校园文化",
}

EXPECTED_SUGGESTION_CULTURE = {
    "01_hongmian.md": "木棉文化",
    "02_lingnan_culture.md": "岭南文化",
    "03_yueju.md": "粤剧文化",
    "04_lingnan_architecture.md": "岭南建筑文化",
    "05_guangzhou_food.md": "广州早茶文化",
    "06_guangzhou_university.md": "广州大学校园文化",
}


class FileBackedStubRetriever:
    """按验收数据选择真实知识文件，不加载Embedding模型。"""

    _TITLE_PATTERN = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)

    def __init__(self, cases: list[dict[str, Any]]) -> None:
        self.cases = {str(case["question"]): case for case in cases}

    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        case = self.cases[query]
        expected_source = case["expected_source"]
        if expected_source is None:
            return []

        source_path = KNOWLEDGE_DIR / str(expected_source)
        source_text = source_path.read_text(encoding="utf-8")
        title_match = self._TITLE_PATTERN.search(source_text)
        title = title_match.group(1).strip() if title_match else source_path.stem
        grounded_text = self._first_grounded_paragraph(source_text)
        return [
            {
                "chunk_id": f"stub-{source_path.stem}",
                "text": grounded_text,
                "metadata": {
                    "source_path": source_path.name,
                    "title": title,
                    "section": str(case["category"]),
                },
                "score": 0.95,
                "distance": 0.05,
            }
        ][:top_k]

    @staticmethod
    def _first_grounded_paragraph(source_text: str) -> str:
        seen_title = False
        for line in source_text.splitlines():
            clean_line = line.strip()
            if clean_line.startswith("# "):
                seen_title = True
                continue
            if (
                seen_title
                and clean_line
                and not clean_line.startswith("#")
                and not clean_line.startswith("---")
            ):
                return re.sub(r"^[-*>]\s*", "", clean_line)
        raise AssertionError("知识文件没有可用于回答的正文")


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    rag_service = RAGService(
        retriever=FileBackedStubRetriever(CASES),
        llm_service=LLMService(MockLLM(), PROMPT_PATH),
        top_k=5,
    )
    app.dependency_overrides[get_rag_service] = lambda: rag_service
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_rag_service, None)


def test_question_data_is_complete_and_covers_required_categories() -> None:
    assert len(CULTURE_CASES) >= 20
    assert len(BOUNDARY_CASES) >= 3
    assert len({str(case["question"]) for case in CASES}) == len(CASES)
    assert all(
        set(case) == {"question", "expected_source", "category"} for case in CASES
    )
    assert REQUIRED_CATEGORIES.issubset(
        {str(case["category"]) for case in CULTURE_CASES}
    )
    assert all(
        (KNOWLEDGE_DIR / str(case["expected_source"])).is_file()
        for case in CULTURE_CASES
    )


@pytest.mark.parametrize(
    "case",
    CULTURE_CASES,
    ids=[
        f"{case['category']}-{index + 1}"
        for index, case in enumerate(CULTURE_CASES)
    ],
)
def test_culture_question_returns_grounded_answer_source_and_suggestion(
    client: TestClient,
    case: dict[str, Any],
) -> None:
    response = client.post(
        "/api/v1/ai/chat",
        json={"question": case["question"]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["requestId"]
    data = payload["data"]
    assert data["answer"]
    assert data["answer"] != RAGService.FALLBACK_ANSWER
    assert data["sources"]
    assert case["expected_source"] in {
        source["source_path"] for source in data["sources"]
    }
    source_text = (KNOWLEDGE_DIR / str(case["expected_source"])).read_text(
        encoding="utf-8"
    )
    assert data["answer"] in source_text, "回答必须能够追溯到预期知识文件"
    assert data["creation_suggestion"] == {
        "enable": True,
        "culture": EXPECTED_SUGGESTION_CULTURE[str(case["expected_source"])],
        "campus": "广州大学",
        "style": "国潮风",
    }


@pytest.mark.parametrize(
    "case",
    BOUNDARY_CASES,
    ids=[str(case["category"]) for case in BOUNDARY_CASES],
)
def test_boundary_question_is_refused_without_source_or_suggestion(
    client: TestClient,
    case: dict[str, Any],
) -> None:
    response = client.post(
        "/api/v1/ai/chat",
        json={"question": case["question"]},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["answer"] == RAGService.FALLBACK_ANSWER
    assert data["sources"] == []
    assert data["creation_suggestion"] == {
        "enable": False,
        "culture": "",
        "campus": "",
        "style": "",
    }
    assert not any(
        phrase in data["answer"]
        for phrase in ("可以治疗", "现任总统是", "维修步骤如下")
    )
