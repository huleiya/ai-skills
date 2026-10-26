#!/usr/bin/env python3
"""Lightweight quality checks for get-job.skill output folders."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


BANNED_PATTERNS = [
    r"迁移句\s*[:：]",
    r"迁移说明\s*[:：]",
    r"可迁移性\s*[:：]",
    r"产品级分轮次版本",
    r"产品级版本",
    r"保留作参考",
    r"旧版",
    r"旧脚本版",
    r"旧排版版",
    r"半成品",
    r"(?i)transfer sentence\s*:",
    r"(?i)transfer note\s*:",
    r"(?i)transferability\s*:",
    r"(?i)production-grade round-by-round version",
    r"(?i)production version",
    r"(?i)kept for reference",
    r"(?i)legacy (?:script|layout) version",
    r"(?i)half-finished",
]

INTERVIEW_LAYOUTS = {
    "面试准备": {
        "files": [
            "00-总览.md",
            "01-简历bullet逐条深挖.md",
            "02-表达状态与自我介绍.md",
            "99-面后复盘题库.md",
        ],
        "markers": {
            "00-总览.md": ["轮次地图", "风险地图", "Bullet coverage"],
            "01-简历bullet逐条深挖.md": ["Bullet", "追问", "证据"],
            "02-表达状态与自我介绍.md": ["关键字卡", "项目逐字稿", "不会"],
            "99-面后复盘题库.md": ["复盘", "题库"],
        },
    },
    "interview-prep": {
        "files": [
            "00-overview.md",
            "01-resume-bullet-deep-dives.md",
            "02-delivery-and-self-introduction.md",
            "99-post-interview-review.md",
        ],
        "markers": {
            "00-overview.md": [
                "## Interview-stage map",
                "## Risk map",
                "## Resume-bullet coverage",
            ],
            "01-resume-bullet-deep-dives.md": [
                "## Bullet inventory",
                "## Deep dives",
                "Likely follow-ups",
                "Evidence boundary",
            ],
            "02-delivery-and-self-introduction.md": [
                "## Keyword card",
                "## Project walkthrough",
                "## Honest boundary lines",
            ],
            "99-post-interview-review.md": [
                "## Review template",
                "## Question bank",
            ],
        },
    },
}

RESEARCH_LAYOUTS = {
    "岗位调研.md": ["来源", "覆盖"],
    "role-research.md": ["## Source coverage", "## Coverage gaps"],
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def check_banned_patterns(root: Path) -> list[str]:
    failures: list[str] = []
    for path in sorted(root.rglob("*.md")):
        text = read_text(path)
        for pattern in BANNED_PATTERNS:
            if re.search(pattern, text):
                failures.append(f"{path}: banned pattern `{pattern}`")
    return failures


def check_interview_folder(folder: Path) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    layout = INTERVIEW_LAYOUTS[folder.name]
    required_files = layout["files"]
    required_markers = layout["markers"]

    for filename in required_files:
        if not (folder / filename).exists():
            failures.append(f"{folder}: missing `{filename}`")

    for filename, markers in required_markers.items():
        path = folder / filename
        if not path.exists():
            continue
        text = read_text(path)
        missing = [marker for marker in markers if marker not in text]
        if missing:
            failures.append(f"{path}: missing marker(s) {', '.join(missing)}")

    round_files = sorted(
        p.name
        for p in folder.glob("*.md")
        if p.name not in required_files
    )
    bad_round_names = [
        name
        for name in round_files
        if not re.match(r"0[3-9]-", name)
    ]
    if bad_round_names:
        failures.append(
            f"{folder}: round files must start at 03-, got {', '.join(bad_round_names)}"
        )

    if not round_files:
        warnings.append(f"{folder}: no confirmed/high-confidence round file found")

    return failures, warnings


def check_research_file(path: Path) -> list[str]:
    warnings: list[str] = []
    text = read_text(path)
    for marker in RESEARCH_LAYOUTS[path.name]:
        if marker not in text:
            warnings.append(f"{path}: research file may be missing source coverage")
            break
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check public-facing get-job.skill artifacts for structural quality issues."
    )
    parser.add_argument("paths", nargs="+", help="Output/example folder(s) to check")
    args = parser.parse_args()

    failures: list[str] = []
    warnings: list[str] = []

    for raw_path in args.paths:
        root = Path(raw_path).expanduser().resolve()
        if not root.exists():
            failures.append(f"{root}: path does not exist")
            continue

        failures.extend(check_banned_patterns(root))

        interview_folders = []
        for folder_name in INTERVIEW_LAYOUTS:
            interview_folders.extend(
                p for p in root.rglob(folder_name) if p.is_dir()
            )
        if root.name in INTERVIEW_LAYOUTS and root.is_dir():
            interview_folders.append(root)
        seen = set()
        for folder in interview_folders:
            if folder in seen:
                continue
            seen.add(folder)
            folder_failures, folder_warnings = check_interview_folder(folder)
            failures.extend(folder_failures)
            warnings.extend(folder_warnings)

        for filename in RESEARCH_LAYOUTS:
            for research in root.rglob(filename):
                warnings.extend(check_research_file(research))

    for warning in warnings:
        print(f"[WARN] {warning}")
    for failure in failures:
        print(f"[FAIL] {failure}")

    if failures:
        print(f"Quality check failed: {len(failures)} issue(s).")
        return 1

    print("Quality check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
