"""Synthetic fixtures only; no personal transcripts or credentials."""
import copy
from html.parser import HTMLParser
import tempfile
from pathlib import Path
import unittest
from unittest import mock

import render_report
from render_report import validate, render_print_html, render_markdown, write_outputs, find_browser, clock


def fixture():
    return {
        'title': '合成测试\n面试分析报告',
        'metadata': {'source_label': 'synthetic.txt', 'coverage_note': '测试数据，不是真实面试。',
                     'candidate': '测试候选人', 'duration': '约 10 分钟', 'result': '待通知'},
        'summary': {'headline': '测试状态覆盖', 'strengths': ['Q01 回答结论明确。'],
                    'cards': [{'kind': '优势', 'title': '幂等', 'text': '讲清了编号复用。'}],
                    'abilities': [{'name': '一致性', 'score': 3, 'note': '方向对。'}],
                    'ability_note': '主观评估。',
                    'timeline': [{'label': '项目', 'start': '00:00', 'end': '05:30', 'note': '一题。'}]},
        'actions': [{'title': '重试时间线', 'tag': '本周', 'text': '画请求重试时间线。'}],
        'questions': [{
            'id': 'Q01', 'locator': '00:01:10—00:02:00', 'title': '请求编号复用',
            'question': '为什么同一请求要复用编号？',
            'candidate_answer': '为了识别重试。\n```\n</script><script>alert(1)</script>',
            'answer_points': ['用编号识别重试'], 'lost_points': ['缺少冲突处理'],
            'better_answer': '先答：重试复用编号；再讲同编号不同内容返回冲突。',
            'intent': '幂等边界', 'assessment': {'level': '合格', 'reason': '缺少冲突处理。',
                'evidence': [{'locator': '第 4 行', 'quote': '为了识别重试。'}]},
            'rewrite': {'conclusion': '同一次操作重试时使用同一个编号。',
                'mechanism': '按用户和编号查已有任务，并核对内容。',
                'tradeoffs': '不能仅按输入去重，因为用户可能主动重复发起。',
                'data': {'status': '待补', 'text': '未提供压测，先验证同编号同内容只创建一个任务。', 'needed': ['并发测试记录']}},
            'followups': [{'question': '输入不同呢？', 'approach': '解释冲突拒绝。'},
                          {'question': '缓存过期呢？', 'approach': '解释数据库持久约束。'}],
            'practice': {'priority': 'P0', 'action': '画请求重试时间线。', 'done_when': '能解释响应丢失后的重试。'}
        }]
    }


class Parse(HTMLParser):
    def __init__(self):
        super().__init__(); self.scripts = 0; self.articles = []; self.urls = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script': self.scripts += 1
        if tag == 'article': self.articles.append(attrs.get('id'))
        for k in ('src', 'href'):
            if attrs.get(k): self.urls.append(attrs[k])


def fake_print(html_text, pdf_path, browser):
    Path(pdf_path).write_bytes(b'%PDF-1.7 synthetic')


class ReportTests(unittest.TestCase):
    def test_four_steps_in_markdown_and_card_in_pdf_page(self):
        d = fixture(); validate(d); h = render_print_html(d); md = render_markdown(d)
        for label, key in [('结论', 'conclusion'), ('机制', 'mechanism'), ('取舍', 'tradeoffs')]:
            self.assertIn('#### ' + label, md)
            self.assertIn(d['questions'][0]['rewrite'][key], md)
        self.assertIn('#### 数据', md)
        for part in ('回答要点', '失分点', '更好的答法', '面试官问。', '题目索引', '逐题复盘', '行动清单', '能力评估', '时间分布'):
            self.assertIn(part, h)
        self.assertIn(d['questions'][0]['better_answer'], h)
        self.assertIn(d['questions'][0]['better_answer'], md)
    def test_each_step_and_card_field_is_mandatory(self):
        for key in ['conclusion', 'mechanism', 'tradeoffs', 'data']:
            d = fixture(); del d['questions'][0]['rewrite'][key]
            with self.assertRaises(ValueError): validate(d)
        for key in ['title', 'better_answer', 'lost_points', 'answer_points']:
            d = fixture(); del d['questions'][0][key]
            with self.assertRaises(ValueError): validate(d)
    def test_unknown_data_status_and_missing_evidence_rejected(self):
        for mutate in [lambda q: q['rewrite']['data'].update(status='猜测'),
                       lambda q: q['assessment'].update(evidence=[])]:
            d = fixture(); mutate(d['questions'][0])
            with self.assertRaises(ValueError): validate(d)
    def test_abilities_need_subjective_note_and_valid_scores(self):
        d = fixture(); del d['summary']['ability_note']
        with self.assertRaises(ValueError): validate(d)
        d = fixture(); d['summary']['abilities'][0]['score'] = 6
        with self.assertRaises(ValueError): validate(d)
        d = fixture(); d['summary']['timeline'][0]['end'] = '00:00'
        with self.assertRaises(ValueError): validate(d)
    def test_legacy_levels_map_to_report_tiers(self):
        d = fixture(); d['questions'][0]['assessment']['level'] = '需重练'
        validate(d); h = render_print_html(d)
        self.assertIn('class="chip weak">薄弱', h)
    def test_no_blank_reports_or_duplicate_ids(self):
        d = fixture(); d['questions'] = []
        with self.assertRaises(ValueError): validate(d)
        d = fixture(); d['questions'].append(copy.deepcopy(d['questions'][0]))
        with self.assertRaises(ValueError): validate(d)
    def test_print_page_is_offline_and_escaped(self):
        h = render_print_html(fixture()); p = Parse(); p.feed(h)
        self.assertEqual(p.scripts, 0); self.assertEqual(p.articles, ['Q01']); self.assertEqual(p.urls, [])
        self.assertNotIn('<script>alert(1)</script>', h)
        self.assertNotIn('http', h.split('<style>')[1].split('</style>')[0])
    def test_markdown_raw_answer_fence_is_safe(self):
        md = render_markdown(fixture())
        self.assertIn('````text\n为了识别重试。\n```', md)
    def test_missing_answer_does_not_become_invented_original(self):
        d = fixture(); q = d['questions'][0]; q['candidate_answer'] = ''; q['answer_points'] = []
        q['assessment']['level'] = '转写不清'
        validate(d); self.assertIn('原稿未提供可确认的本人回答。', render_markdown(d))
        q['assessment']['level'] = '亮点'
        with self.assertRaises(ValueError): validate(d)
    def test_clock_drops_zero_hour(self):
        self.assertEqual(clock('00:12:51'), '12:51'); self.assertEqual(clock('01:02:03'), '1:02:03')
        self.assertEqual(clock('约 05:30'), '05:30'); self.assertEqual(clock('第 3 行'), '')
    def test_outputs_are_pdf_and_markdown_and_preserve_existing(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(render_report, 'print_pdf', fake_print), \
                mock.patch.object(render_report, 'find_browser', lambda b=None: 'browser'):
            paths = write_outputs(fixture(), tmp)
            self.assertEqual([p.name for p in paths], ['report.pdf', 'post-interview.md'])
            self.assertFalse(any(Path(tmp).glob('*.html')))
            paths[1].write_text('Manual notes', encoding='utf-8')
            with self.assertRaises(FileExistsError): write_outputs(fixture(), tmp)
            self.assertEqual(paths[1].read_text(encoding='utf-8'), 'Manual notes')
            write_outputs(fixture(), tmp, overwrite=True)
            self.assertIn('#### 数据', paths[1].read_text(encoding='utf-8'))
    def test_real_browser_print_when_available(self):
        try:
            exe = find_browser()
        except FileNotFoundError:
            self.skipTest('No Chromium-based browser installed')
        with tempfile.TemporaryDirectory() as tmp:
            pdf, _ = write_outputs(fixture(), tmp, browser=exe)
            self.assertTrue(pdf.read_bytes().startswith(b'%PDF'))


if __name__ == '__main__':
    unittest.main()
