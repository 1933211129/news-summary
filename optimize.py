"""使用 BootstrapFewShot 对 NewsPipeline 进行编译优化。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

import dspy

import config
from model import NewsPipeline

dspy.settings.configure(lm=config.lm)

EXAMPLE_PATH = Path(__file__).resolve().parent / "example.json"
BEST_PIPELINE_PATH = Path(__file__).resolve().parent / "best_pipeline.json"


def load_training_examples(path: Path) -> List[dspy.Example]:
    if not path.exists():
        raise FileNotFoundError(f"未找到示例数据：{path}")
    with path.open("r", encoding="utf-8") as fp:
        raw_data = json.load(fp)
    if isinstance(raw_data, dict):
        raw_data = [raw_data]
    examples: List[dspy.Example] = []
    for item in raw_data:
        example = dspy.Example(
            content=item["content"],
            category=item["category"],
            title=item["title"],
            short_summary=item["short_summary"],
            detailed_summary=item["detailed_summary"],
        )
        example = example.with_inputs("content")
        examples.append(example)
    return examples


def evaluation_metric(gold: dspy.Example, pred: dspy.Prediction, **_: object) -> bool:
    category_match = _safe_get(pred, "category") == gold.category
    detailed_ok = bool(_safe_get(pred, "detailed_summary"))
    return bool(category_match and detailed_ok)


def _safe_get(pred: dspy.Prediction, field: str):
    if isinstance(pred, dict):
        return pred.get(field)
    return getattr(pred, field, None)


def main() -> None:
    trainset = load_training_examples(EXAMPLE_PATH)
    pipeline = NewsPipeline()
    teleprompter = dspy.teleprompt.BootstrapFewShot(
        metric=evaluation_metric,
        max_bootstrapped_demos=min(4, len(trainset)),
        max_labeled_demos=len(trainset),
    )
    compiled_model = teleprompter.compile(student=pipeline, trainset=trainset)
    compiled_model.save(str(BEST_PIPELINE_PATH))
    print(f"已保存优化后的 Pipeline 至：{BEST_PIPELINE_PATH}")


if __name__ == "__main__":
    main()

