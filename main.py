"""生产环境入口脚本。"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import dspy

import config
from model import NewsMetadata, NewsPipeline
from utils import JsonlWriter, read_news_file

dspy.settings.configure(lm=config.lm)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_FILE = BASE_DIR / "test_data.xls"
DEFAULT_OUTPUT_FILE = BASE_DIR / "result_output.jsonl"
BEST_PIPELINE_PATH = BASE_DIR / "best_pipeline.json"


def load_pipeline(compiled_path: Path) -> NewsPipeline:
    pipeline = NewsPipeline()
    if compiled_path.exists():
        pipeline.load(str(compiled_path))
        print(f"[INFO] 已加载优化 Pipeline：{compiled_path}")
    else:
        print(f"[WARN] 未找到 {compiled_path}，将使用未优化模型。")
    return pipeline


def process_records(
    pipeline: NewsPipeline,
    records: Iterable[dict],
    output_path: Path,
) -> None:
    written = 0
    with JsonlWriter(output_path) as writer:
        for record in records:
            metadata = NewsMetadata(
                raw_content=record.get("raw_content", ""),
                release_time=record.get("release_time"),
                source_institution=record.get("source_institution"),
                url=record.get("url"),
            )
            if not metadata.raw_content.strip():
                continue
            prediction = pipeline(content=metadata.raw_content, metadata=metadata)
            if prediction is None:
                continue
            short_summary = prediction.get("short_summary")
            detailed_summary = prediction.get("detailed_summary")
            if short_summary and detailed_summary:
                prediction["detailed_summary"] = f"{short_summary}\n{detailed_summary}"
            writer.append(prediction)
            written += 1
    print(f"[INFO] 已写入 {written} 条结果至 {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="新闻情报自动化抽取")
    parser.add_argument(
        "--data-file",
        type=Path,
        default=DEFAULT_DATA_FILE,
        help="待处理的 Excel/CSV 文件路径。",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="结果输出 JSONL 文件路径。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pipeline = load_pipeline(BEST_PIPELINE_PATH)
    records = read_news_file(args.data_file)
    process_records(pipeline, records, args.output_file)


if __name__ == "__main__":
    main()

