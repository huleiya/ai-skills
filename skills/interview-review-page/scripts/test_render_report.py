"""Synthetic fixtures only; no personal transcripts or credentials."""
import copy
from html.parser import HTMLParser
import tempfile
from pathlib import Path
import unittest

from render_report import validate, render_html, render_markdown, write_outputs


def fixture():
    return {
        'title':'合成测试 · 面试复盘',
        'metadata':{'source_label':'synthetic.txt','coverage_note':'测试数据，不是真实面试。'},
        'summary':{'headline':'测试状态覆盖','strengths':['Q01 回答结论明确。']},
        'questions':[{
            'id':'Q01','locator':'第 2—6 行','question':'为什么同一请求要复用编号？',
            'candidate_answer':'为了识别重试。\n```\n</script><script>alert(1)</script>',
            'intent':'幂等边界','assessment':{'level':'部分到位','reason':'缺少冲突处理。',
                'evidence':[{'locator':'第 4 行','quote':'为了识别重试。'}]},
            'rewrite':{'conclusion':'同一次操作重试时使用同一个编号。',
                'mechanism':'按用户和编号查已有任务，并核对内容。',
                'tradeoffs':'不能仅按输入去重，因为用户可能主动重复发起。',
                'data':{'status':'待补','text':'未提供压测，先验证同编号同内容只创建一个任务。','needed':['并发测试记录']}},
            'followups':[{'question':'输入不同呢？','approach':'解释冲突拒绝。'},
                         {'question':'缓存过期呢？','approach':'解释数据库持久约束。'}],
            'practice':{'priority':'P0','action':'画请求重试时间线。','done_when':'能解释响应丢失后的重试。'}
        }]
    }


class Parse(HTMLParser):
    def __init__(self):
        super().__init__();self.scripts=0;self.articles=[];self.ids=set()
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=='script':self.scripts+=1
        if tag=='article':self.articles.append(attrs.get('id'))
        if 'id' in attrs:self.ids.add(attrs['id'])


class ReportTests(unittest.TestCase):
    def test_four_steps_and_both_outputs(self):
        d=fixture();validate(d);h=render_html(d);md=render_markdown(d)
        for label,key in [('结论','conclusion'),('机制','mechanism'),('取舍','tradeoffs')]:
            self.assertIn('#### '+label,md)
            self.assertIn(d['questions'][0]['rewrite'][key],h)
            self.assertIn(d['questions'][0]['rewrite'][key],md)
        self.assertIn('#### 数据',md);self.assertIn('待补',h)
    def test_each_step_is_mandatory(self):
        for key in ['conclusion','mechanism','tradeoffs','data']:
            d=fixture();del d['questions'][0]['rewrite'][key]
            with self.assertRaises(ValueError):validate(d)
    def test_unknown_data_status_and_missing_evidence_rejected(self):
        for mutate in [lambda q:q['rewrite']['data'].update(status='猜测'),
                       lambda q:q['assessment'].update(evidence=[])]:
            d=fixture();mutate(d['questions'][0])
            with self.assertRaises(ValueError):validate(d)
    def test_no_blank_reports_or_duplicate_ids(self):
        d=fixture();d['questions']=[]
        with self.assertRaises(ValueError):validate(d)
        d=fixture();d['questions'].append(copy.deepcopy(d['questions'][0]))
        with self.assertRaises(ValueError):validate(d)
    def test_source_escaped_and_controls_exist(self):
        h=render_html(fixture());p=Parse();p.feed(h)
        self.assertEqual(p.scripts,1);self.assertEqual(p.articles,['Q01'])
        self.assertIn('&lt;/script&gt;&lt;script&gt;',h)
        self.assertTrue({'search','priority','expand','collapse','print'}<=p.ids)
        self.assertNotIn('<script>alert(1)</script>',h)
        self.assertNotIn('fetch(',h)
    def test_markdown_raw_answer_fence_is_safe(self):
        md=render_markdown(fixture())
        self.assertIn('````text\n为了识别重试。\n```',md)
    def test_missing_answer_does_not_become_invented_original(self):
        d=fixture();q=d['questions'][0];q['candidate_answer']='';q['assessment']['level']='转写不清'
        validate(d);self.assertIn('原稿未提供可确认的本人回答。',render_markdown(d))
        q['assessment']['level']='清晰'
        with self.assertRaises(ValueError):validate(d)
    def test_preserve_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths=write_outputs(fixture(),tmp)
            self.assertTrue(all(p.exists() for p in paths))
            paths[1].write_text('Manual notes',encoding='utf-8')
            with self.assertRaises(FileExistsError):write_outputs(fixture(),tmp)
            self.assertEqual(paths[1].read_text(encoding='utf-8'),'Manual notes')
            write_outputs(fixture(),tmp,overwrite=True)
            self.assertIn('#### 数据',paths[1].read_text(encoding='utf-8'))


if __name__=='__main__':
    unittest.main()
