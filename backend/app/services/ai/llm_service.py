"""与具体模型厂商解耦的 LLM Adapter 和 Prompt 服务。"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path


class LLMAdapter(ABC):
    """所有 LLM 供应商适配器必须实现的最小异步接口。"""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """根据完整 Prompt 生成自然语言文本。"""


class LLMError(RuntimeError):
    """LLM 调用异常基类。"""


class LLMConfigurationError(LLMError):
    """LLM 配置缺失或无效。"""


class LLMNetworkError(LLMError):
    """LLM 网络请求失败。"""


class LLMResponseError(LLMError):
    """LLM 返回 HTTP 错误或无效响应。"""


class MockLLM(LLMAdapter):
    """不访问网络、只基于检索上下文返回答案的测试适配器。"""

    _CONTEXT_PATTERN = re.compile(
        r"<context>\s*(.*?)\s*</context>", re.DOTALL | re.IGNORECASE
    )
    _SOURCE_PATTERN = re.compile(
        r"\[资料\d+[^\]]*\]\s*(.*?)(?=\n\[资料\d+|\Z)", re.DOTALL
    )

    async def generate(self, prompt: str) -> str:
        context_match = self._CONTEXT_PATTERN.search(prompt)
        if not context_match:
            return "当前知识库中暂未找到足够可靠的相关资料，你可以换一种问法。"

        source_match = self._SOURCE_PATTERN.search(context_match.group(1).strip())
        source_text = source_match.group(1).strip() if source_match else ""
        answer = self._to_plain_answer(source_text)
        if not answer:
            return "当前知识库中暂未找到足够可靠的相关资料，你可以换一种问法。"
        return answer

    @staticmethod
    def _to_plain_answer(source_text: str) -> str:
        lines: list[str] = []
        for line in source_text.splitlines():
            clean_line = line.strip()
            if not clean_line or clean_line.startswith("---"):
                continue
            if clean_line.startswith("#"):
                continue
            clean_line = re.sub(r"^[-*>]\s*", "", clean_line)
            clean_line = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", clean_line)
            lines.append(clean_line)
        return "".join(lines).strip()


class LLMService:
    """加载外置 Prompt 模板并调用注入的 LLM Adapter。"""

    def __init__(self, adapter: LLMAdapter, prompt_path: str | Path) -> None:
        self.adapter = adapter
        self.prompt_path = Path(prompt_path)

    async def answer(self, question: str, context: str) -> str:
        prompt = self._render_prompt(question=question, context=context)
        answer = (await self.adapter.generate(prompt)).strip()
        if not answer:
            raise RuntimeError("LLM返回了空回答")
        return answer

    def _render_prompt(self, question: str, context: str) -> str:
        if not self.prompt_path.is_file():
            raise FileNotFoundError(f"问答Prompt模板不存在: {self.prompt_path}")
        template = self.prompt_path.read_text(encoding="utf-8")
        required_variables = ("{context}", "{question}")
        missing = [name for name in required_variables if name not in template]
        if missing:
            raise ValueError(f"问答Prompt缺少模板变量: {', '.join(missing)}")
        return template.replace("{context}", context).replace("{question}", question)
