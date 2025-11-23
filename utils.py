"""
数据读取与结果写出工具集合。

功能点：
- 根据文件后缀自适应选择 Excel/CSV 解析。
- 将不同命名的列映射为统一字段，方便主流程使用。
- 将推理结果写入 JSONL 文件，并确保落盘。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence

import pandas as pd

ColumnAliases = Mapping[str, Sequence[str]]

DEFAULT_COLUMN_ALIASES: Dict[str, Sequence[str]] = {
    "release_time": ("资源发布时间", "发布时间", "时间"),
    "source_institution": ("资源来源机构", "来源", "机构"),
    "url": ("资源URL", "资源url", "链接", "url"),
    "raw_content": ("原文内容", "内容", "新闻内容", "正文"),
}


def read_news_file(
    file_path: str | Path,
    column_aliases: ColumnAliases | None = None,
) -> List[Dict[str, Any]]:
    """
    读取 Excel/CSV 文件并返回标准化字段。

    Args:
        file_path: 数据文件路径。
        column_aliases: 可选列映射，覆盖默认值时按需传入。
    """
    column_aliases = column_aliases or DEFAULT_COLUMN_ALIASES
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"未找到数据文件：{path}")

    loader = _select_loader(path.suffix.lower())
    try:
        df = loader(path)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"读取文件失败：{path}") from exc

    df = df.fillna("")
    standardized_columns = _build_column_mapping(df.columns, column_aliases)
    missing = [field for field, column in standardized_columns.items() if column is None]
    if missing:
        raise KeyError(f"缺少必要列：{', '.join(missing)}")

    results: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        record = {
            field: str(row[column]).strip()
            for field, column in standardized_columns.items()
            if column is not None
        }
        results.append(record)
    return results


class JsonlWriter:
    """按照 JSON Lines 格式写入，逐条 flush 并落盘。"""

    def __init__(self, file_path: str | Path, *, ensure_ascii: bool = False) -> None:
        self.file_path = Path(file_path)
        self.ensure_ascii = ensure_ascii
        self._fp: Any = None

    def __enter__(self) -> "JsonlWriter":
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._fp = self.file_path.open("w", encoding="utf-8")
        return self

    def append(self, record: Mapping[str, Any]) -> None:
        if self._fp is None:
            raise RuntimeError("JsonlWriter 尚未打开。")
        line = json.dumps(record, ensure_ascii=self.ensure_ascii)
        self._fp.write(line + "\n")
        self._flush()

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        if self._fp is None:
            return
        self._flush()
        self._fp.close()
        self._fp = None

    def _flush(self) -> None:
        if self._fp is None:
            return
        self._fp.flush()
        os.fsync(self._fp.fileno())


def write_jsonl(
    records: Sequence[Mapping[str, Any]],
    file_path: str | Path,
    *,
    ensure_ascii: bool = False,
) -> None:
    """按 JSONL 写入所有记录。"""
    with JsonlWriter(file_path, ensure_ascii=ensure_ascii) as writer:
        for record in records:
            writer.append(record)


def write_json(
    records: Sequence[Mapping[str, Any]],
    file_path: str | Path,
    *,
    indent: int = 2,
) -> None:
    """兼容旧接口，内部调用 JSONL 写入，不再支持缩进参数。"""
    write_jsonl(records, file_path)


def _select_loader(suffix: str):
    if suffix in {".xls", ".xlsx"}:
        return lambda file_path: pd.read_excel(file_path)  # type: ignore[return-value]
    if suffix == ".csv":
        return lambda file_path: pd.read_csv(file_path)  # type: ignore[return-value]
    raise ValueError(f"暂不支持的文件格式：{suffix}")


def _normalize(name: Any) -> str:
    return str(name).replace("：", ":").strip().lower()


def _build_column_mapping(
    columns: Iterable[Any],
    column_aliases: ColumnAliases,
) -> MutableMapping[str, str | None]:
    normalized = {_normalize(col): str(col) for col in columns}
    mapping: MutableMapping[str, str | None] = {}
    for field, aliases in column_aliases.items():
        target_column = None
        for alias in aliases:
            alias_norm = _normalize(alias)
            if alias_norm in normalized:
                target_column = normalized[alias_norm]
                break
        mapping[field] = target_column
    return mapping

