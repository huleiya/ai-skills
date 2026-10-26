#!/usr/bin/env python3
"""Minimal regression tests for the public scripts."""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import generate_resume  # noqa: E402
import quality_check  # noqa: E402


CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


class GenerateResumeTests(unittest.TestCase):
    def test_english_fallback_docx_contains_no_chinese(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "fallback.en.docx"
            generate_resume.build({"locale": "en"}, output)

            with zipfile.ZipFile(output) as archive:
                document_xml = archive.read("word/document.xml").decode("utf-8")

            self.assertIn("Name to add", document_xml)
            self.assertIn("Information to add", document_xml)
            self.assertIsNone(CJK_RE.search(document_xml))

    def test_english_sample_is_fictional_and_renders_without_chinese(self):
        sample_path = SCRIPT_DIR / "sample_resume.en.json"
        sample = json.loads(sample_path.read_text(encoding="utf-8"))
        self.assertTrue(sample["example"]["fictional"])

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "sample_resume.en.docx"
            generate_resume.build(sample, output)
            with zipfile.ZipFile(output) as archive:
                document_xml = archive.read("word/document.xml").decode("utf-8")

        self.assertIn("Target role: ", document_xml)
        self.assertIn("EventEase", document_xml)
        self.assertIsNone(CJK_RE.search(document_xml))

    def test_english_sample_matches_the_canonical_after_resume(self):
        sample = json.loads(
            (SCRIPT_DIR / "sample_resume.en.json").read_text(encoding="utf-8")
        )
        canonical = json.loads(
            (
                SCRIPT_DIR.parent
                / "examples/en/ai-product-prototyping/resume-after.json"
            ).read_text(encoding="utf-8")
        )
        sample["example"]["source_of_truth"] = "source-facts.md"

        self.assertEqual(sample, canonical)

    def test_chinese_remains_the_default_locale(self):
        normalized = generate_resume.normalize_resume_data({})

        self.assertEqual(normalized["locale"], "zh")
        self.assertEqual(normalized["name"], "姓名待补")
        self.assertEqual(normalized["contact"], "联系方式待补")
        self.assertEqual(normalized["sections"][0]["title"], "信息待补")

    def test_english_transfer_labels_are_removed(self):
        self.assertEqual(
            generate_resume.clean_bullet_text(
                "Transferability: Connects event operations to product testing."
            ),
            "Connects event operations to product testing.",
        )


class QualityCheckTests(unittest.TestCase):
    def test_complete_english_interview_prep_layout_passes(self):
        files = {
            "00-overview.md": (
                "## Interview-stage map\n## Risk map\n## Resume-bullet coverage\n"
            ),
            "01-resume-bullet-deep-dives.md": (
                "## Bullet inventory\n## Deep dives\nLikely follow-ups\nEvidence boundary\n"
            ),
            "02-delivery-and-self-introduction.md": (
                "## Keyword card\n## Project walkthrough\n## Honest boundary lines\n"
            ),
            "99-post-interview-review.md": (
                "## Review template\n## Question bank\n"
            ),
            "03-ai-product-prototyping-resume-deep-dive.md": "# Round 1\n",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir) / "interview-prep"
            folder.mkdir()
            for filename, content in files.items():
                (folder / filename).write_text(content, encoding="utf-8")

            failures, warnings = quality_check.check_interview_folder(folder)

        self.assertEqual(failures, [])
        self.assertEqual(warnings, [])

    def test_english_role_research_markers_are_recognized(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "role-research.md"
            path.write_text(
                "## Source coverage\nPrimary company source.\n\n"
                "## Coverage gaps\nInterview stages remain unconfirmed.\n",
                encoding="utf-8",
            )

            self.assertEqual(quality_check.check_research_file(path), [])


if __name__ == "__main__":
    unittest.main()
