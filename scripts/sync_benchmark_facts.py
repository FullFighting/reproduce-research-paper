#!/usr/bin/env python3
"""Synchronize generated benchmark facts and reject stale documentation."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "benchmarks" / "benchmark-summary.json"
REPORT_PATH = ROOT / "benchmarks" / "benchmark-report.md"
START = "<!-- benchmark-facts:start -->"
END = "<!-- benchmark-facts:end -->"


def load_renderer():
    path = ROOT / "benchmarks" / "run_benchmarks.py"
    spec = importlib.util.spec_from_file_location("benchmark_runner", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load benchmark renderer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.render_report


def generated_blocks(summary: dict) -> dict[Path, str]:
    cases = summary["case_count"]
    reproduced = summary["reproduced_count"]
    verified = summary["verified_bundle_count"]
    tokens = summary["total_api_tokens"]
    cost = summary["total_estimated_cost_usd"]
    english_block = "\n".join(
        [
            START,
            f"- {cases} public, paper-linked, claim-level executable cases.",
            f"- {reproduced}/{cases} claims reproduced within their declared tolerance.",
            f"- {verified}/{cases} evidence bundles pass full artifact re-hashing and report recomputation.",
            f"- {tokens} deterministic-runtime API tokens and ${cost} estimated external API cost.",
            END,
        ]
    )
    return {
        ROOT / "README.md": english_block,
        ROOT / "docs" / "codex-fund-application.md": english_block,
        ROOT / "README_ZH.md": "\n".join(
            [
                START,
                f"- {cases} 个公开、关联论文、claim-level 的可执行案例；",
                f"- {reproduced}/{cases} 个 claim 在预声明容差内复现；",
                f"- {verified}/{cases} 个 evidence bundle 通过重新哈希、重新比较和重新渲染报告；",
                f"- 确定性 runtime 使用 {tokens} 个 API token，估算外部 API 成本 ${cost}；",
                END,
            ]
        ),
    }


def replace_block(text: str, block: str, path: Path) -> str:
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError(f"{path} must contain exactly one generated facts block")
    before, remainder = text.split(START, 1)
    _, after = remainder.split(END, 1)
    return before + block + after


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="fail if generated facts are stale")
    mode.add_argument("--write", action="store_true", help="update generated facts")
    args = parser.parse_args()

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    expected_report = load_renderer()(summary)
    stale: list[str] = []

    actual_report = REPORT_PATH.read_text(encoding="utf-8")
    if actual_report != expected_report:
        stale.append(str(REPORT_PATH.relative_to(ROOT)))
        if args.write:
            REPORT_PATH.write_text(expected_report, encoding="utf-8")

    for path, block in generated_blocks(summary).items():
        actual = path.read_text(encoding="utf-8")
        expected = replace_block(actual, block, path)
        if actual != expected:
            stale.append(str(path.relative_to(ROOT)))
            if args.write:
                path.write_text(expected, encoding="utf-8")

    result = {
        "status": "updated" if args.write and stale else ("stale" if stale else "current"),
        "source": str(SUMMARY_PATH.relative_to(ROOT)),
        "stale_files": stale,
    }
    print(json.dumps(result, indent=2))
    return 1 if args.check and stale else 0


if __name__ == "__main__":
    sys.exit(main())
