import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_REPORT = ROOT / 'examples' / 'sample-report.md'
SAMPLE_REWRITE = ROOT / 'examples' / 'rewrite-last-sample.md'
REPORT_TEMPLATE = ROOT / 'skills' / 'score' / 'references' / 'report-template.md'
REWRITE_TEMPLATE = ROOT / 'skills' / 'rewrite-last' / 'references' / 'output-template.md'


def read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def assert_in_order(testcase: unittest.TestCase, text: str, markers: list[str]) -> None:
    cursor = -1
    for marker in markers:
        position = text.find(marker)
        testcase.assertGreater(position, cursor, f"Expected marker order to include {marker!r}")
        cursor = position


class PromptIQOutputContractTests(unittest.TestCase):
    def test_report_template_preserves_required_section_order(self):
        text = read(REPORT_TEMPLATE)
        assert_in_order(
            self,
            text,
            [
                '## PromptIQ Review',
                '**Why It Is Not Higher**',
                '**Dimension Breakdown**',
                '**Strongest Evidence**',
                '**Course Corrections**',
                '**Next Session Drill**',
                '**Recent Trend**',
                '**Focus Area**',
            ],
        )

    def test_report_template_uses_summary_table(self):
        text = read(REPORT_TEMPLATE)
        self.assertIn('| Metric | Value |', text)
        self.assertIn('| Score | [X.X]/10 |', text)
        self.assertIn('| Band | [foundational / competent / strong / elite] |', text)
        self.assertIn('| Confidence | [low / medium / high] |', text)
        self.assertIn('| Complexity | [low / medium / high] |', text)
        self.assertIn('| Delta | [if available: +0.3 vs last compatible session] |', text)

    def test_sample_report_matches_contract_sections(self):
        text = read(SAMPLE_REPORT)
        assert_in_order(
            self,
            text,
            [
                '## PromptIQ Review',
                '**Why It Is Not Higher**',
                '**Dimension Breakdown**',
                '**Strongest Evidence**',
                '**Course Corrections**',
                '**Next Session Drill**',
                '**Recent Trend**',
                '**Focus Area**',
            ],
        )

    def test_sample_report_has_eight_dimension_lines(self):
        text = read(SAMPLE_REPORT)
        block_match = re.search(r"\*\*Dimension Breakdown\*\*\n\n```text\n(?P<body>.*?)\n```", text, re.S)
        self.assertIsNotNone(block_match)
        lines = [line for line in block_match.group('body').splitlines() if line.strip()]
        self.assertEqual(len(lines), 8)
        self.assertTrue(any('Instruction Clarity' in line for line in lines))
        self.assertTrue(any('Tool Awareness' in line for line in lines))

    def test_sample_report_keeps_verification_language_visible(self):
        text = read(SAMPLE_REPORT)
        self.assertIn('verification implicit', text)
        self.assertIn('verification rule', text)
        self.assertIn('concrete check', text)

    def test_rewrite_template_preserves_required_section_order(self):
        text = read(REWRITE_TEMPLATE)
        assert_in_order(
            self,
            text,
            [
                '## Rewrite Last',
                '**What Changed**',
                '**Rewrites**',
                '**Reusable Pattern**',
            ],
        )

    def test_rewrite_sample_matches_contract(self):
        text = read(SAMPLE_REWRITE)
        assert_in_order(
            self,
            text,
            [
                '## Rewrite Last',
                '**What Changed**',
                '**Rewrites**',
                '**Reusable Pattern**',
            ],
        )
        self.assertEqual(text.count('Original:'), 3)
        self.assertEqual(text.count('Rewrite:'), 3)
        self.assertEqual(text.count('Why:'), 3)
        self.assertIn('verify', text.lower())


if __name__ == '__main__':
    unittest.main()
