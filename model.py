"""
基于 DSPy 的新闻情报抽取模型。

核心组件：
- ``NewsClassifier``：判断新闻类型。
- ``IntelligenceExtractor``：一次性生成标题与多层摘要。
- ``NewsPipeline``：串联分类与抽取，同时执行 Gatekeeper 逻辑。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping, Optional

import dspy

import config

dspy.settings.configure(lm=config.lm)

TARGET_CATEGORIES = ["研究前沿", "产业应用", "政策计划"]


class NewsClassifier(dspy.Signature):
    """判定新闻类别，输出限定在目标列表内，否则返回“其他”。"""

    content = dspy.InputField(desc="新闻原文内容。")
    category = dspy.OutputField(
        desc="新闻类型，仅可从「研究前沿、产业应用、政策计划、其他」中选择，输出必须是中文。"
    )


class IntelligenceExtractor(dspy.Signature):
    """在单次调用中生成标题与两层摘要，确保语境一致。"""

    content = dspy.InputField(desc="新闻原文内容。")
    category = dspy.InputField(desc="上一步的分类结果。")
    title = dspy.OutputField(desc="中文标题，简洁直观，勿超过30个汉字。")
    short_summary = dspy.OutputField(
        desc="本期看点，单段中文简介，不可分条，控制在40个汉字以内。"
    )
    detailed_summary = dspy.OutputField(
        desc="本期概要，使用(1)(2)(3)编号的中文分点描述，覆盖关键信息。"
    )


@dataclass
class NewsMetadata:
    """读取文件后附加的元数据。"""

    raw_content: str
    release_time: Optional[str] = None
    source_institution: Optional[str] = None
    url: Optional[str] = None


class NewsPipeline(dspy.Module):
    """串联分类与情报抽取的完整工作流。"""

    def __init__(self) -> None:
        super().__init__()
        self.classifier = dspy.ChainOfThought(NewsClassifier)
        self.extractor = dspy.ChainOfThought(IntelligenceExtractor)

    def forward(
        self,
        content: str,
        metadata: Optional[Mapping[str, Any] | NewsMetadata] = None,
    ) -> Optional[Dict[str, Any]]:
        """处理单条新闻，返回结构化情报。"""
        classification = self.classifier(content=content)
        normalized_category = self._normalize_category(classification.category)
        if normalized_category not in TARGET_CATEGORIES:
            return None

        extraction = self.extractor(content=content, category=normalized_category)
        result = {
            "category": normalized_category,
            "title": extraction.title.strip(),
            "short_summary": extraction.short_summary.strip(),
            "detailed_summary": extraction.detailed_summary.strip(),
        }

        result.update(self._extract_metadata(metadata, fallback_content=content))
        return result

    @staticmethod
    def _normalize_category(category: Optional[str]) -> str:
        if not category:
            return "其他"
        category = category.strip()
        for target in TARGET_CATEGORIES:
            if target in category:
                return target
        return "其他"

    @staticmethod
    def _extract_metadata(
        metadata: Optional[Mapping[str, Any] | NewsMetadata],
        fallback_content: str,
    ) -> Dict[str, Optional[str]]:
        if metadata is None:
            return {
                "raw_content": fallback_content,
                "release_time": None,
                "source_institution": None,
                "url": None,
            }
        if isinstance(metadata, NewsMetadata):
            meta_dict = asdict(metadata)
        else:
            meta_dict = dict(metadata)
        return {
            "raw_content": meta_dict.get("raw_content", fallback_content),
            "release_time": meta_dict.get("release_time"),
            "source_institution": meta_dict.get("source_institution"),
            "url": meta_dict.get("url"),
        }

