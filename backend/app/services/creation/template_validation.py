"""Validation helpers shared by AI template schemas and endpoints."""

from __future__ import annotations

from string import Formatter
from typing import Any


def normalize_options_schema(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict) or not value:
        raise ValueError("模板至少需要一个选项变量")

    normalized: dict[str, list[str]] = {}
    for raw_key, raw_values in value.items():
        key = str(raw_key).strip()
        if not key or not key.isidentifier() or not key.isascii():
            raise ValueError(f"选项变量名无效：{raw_key}")
        if key in normalized:
            raise ValueError(f"选项变量名重复：{key}")
        if not isinstance(raw_values, list) or not raw_values:
            raise ValueError(f"选项变量 {key} 至少需要一个候选值")

        values: list[str] = []
        for raw_value in raw_values:
            candidate = str(raw_value).strip()
            if not candidate:
                raise ValueError(f"选项变量 {key} 不能包含空值")
            if candidate in values:
                raise ValueError(f"选项变量 {key} 包含重复值：{candidate}")
            values.append(candidate)
        normalized[key] = values
    return normalized


def validate_template_contract(
    prompt_template: str,
    options_schema: dict[str, list[str]],
) -> None:
    prompt = prompt_template.strip()
    if not prompt:
        raise ValueError("Prompt 模板不能为空")
    try:
        placeholders = {
            field_name
            for _, field_name, _, _ in Formatter().parse(prompt)
            if field_name is not None
        }
    except ValueError as exc:
        raise ValueError("Prompt 模板中的花括号格式无效") from exc

    invalid = sorted(
        name for name in placeholders if not name.isidentifier() or not name.isascii()
    )
    if invalid:
        raise ValueError(f"Prompt 包含无效占位符：{', '.join(invalid)}")

    option_names = set(options_schema)
    missing_options = sorted(placeholders - option_names)
    unused_options = sorted(option_names - placeholders)
    messages: list[str] = []
    if missing_options:
        messages.append(f"占位符缺少选项配置：{', '.join(missing_options)}")
    if unused_options:
        messages.append(f"选项未在 Prompt 中使用：{', '.join(unused_options)}")
    if messages:
        raise ValueError("；".join(messages))


def validate_creation_options(
    value: Any,
    options_schema: dict[str, list[str]],
) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError("创作选项必须是对象")

    option_names = set(options_schema)
    provided_names = set(value)
    missing = sorted(option_names - provided_names)
    unknown = sorted(provided_names - option_names)
    messages: list[str] = []
    if missing:
        messages.append(f"缺少模板选项：{', '.join(missing)}")
    if unknown:
        messages.append(f"包含未知模板选项：{', '.join(unknown)}")
    if messages:
        raise ValueError("；".join(messages))

    normalized: dict[str, str] = {}
    for name, candidates in options_schema.items():
        selected = value[name]
        if not isinstance(selected, str) or not selected.strip():
            raise ValueError(f"模板选项 {name} 必须是非空字符串")
        selected = selected.strip()
        if selected not in candidates:
            raise ValueError(f"模板选项 {name} 的值不在候选范围内")
        normalized[name] = selected
    return normalized
