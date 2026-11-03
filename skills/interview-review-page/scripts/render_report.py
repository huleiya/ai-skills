#!/usr/bin/env python3
"""Render an evidence-based interview review to offline HTML and Markdown.

Only Python's standard library is required. This script does not analyze a
transcript, execute embedded content, contact a network, or publish anything.
"""
import argparse
import html
import json
from pathlib import Path
import re

LEVELS = {"清晰", "部分到位", "需重练", "未作答", "转写不清"}
DATA_STATES = {"已核验", "原话口述", "待补", "不适用"}
STEPS = (("结论", "conclusion"), ("机制", "mechanism"), ("取舍", "tradeoffs"))


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: expected non-empty text")
    return value


def strings(value, label):
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError(f"{label}: expected a list of non-empty strings")


def validate(data):
    if not isinstance(data, dict):
        raise ValueError("Report must be a JSON object")
    text(data.get("title"), "title")
    meta = data.get("metadata")
    if not isinstance(meta, dict):
        raise ValueError("metadata must be an object")
    for key in ("source_label", "coverage_note"):
        text(meta.get(key), f"metadata.{key}")
    for key in ("company", "role", "round", "interview_date"):
        if key in meta:
            text(meta[key], f"metadata.{key}")
    strings(meta.get("limitations", []), "metadata.limitations")
    summary = data.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("summary must be an object")
    text(summary.get("headline"), "summary.headline")
    for key in ("strengths", "issues", "priorities"):
        strings(summary.get(key, []), f"summary.{key}")
    questions = data.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("At least one real interview question is required; no empty reports")
    seen = set()
    for q in questions:
        if not isinstance(q, dict):
            raise ValueError("Each question must be an object")
        ident = text(q.get("id"), "question.id")
        if not re.fullmatch(r"Q[0-9]{2,}", ident) or ident in seen:
            raise ValueError(f"Invalid or duplicate question ID: {ident}")
        seen.add(ident)
        for key in ("locator", "question", "intent"):
            text(q.get(key), f"{ident}.{key}")
        if not isinstance(q.get("candidate_answer"), str):
            raise ValueError(f"{ident}.candidate_answer must be text, possibly empty")
        a = q.get("assessment", {})
        if not isinstance(a, dict) or a.get("level") not in LEVELS:
            raise ValueError(f"{ident}: invalid assessment level")
        if not q["candidate_answer"].strip() and a["level"] not in {"未作答", "转写不清"}:
            raise ValueError(f"{ident}: absent answer requires 未作答 or 转写不清")
        text(a.get("reason"), f"{ident}.assessment.reason")
        evidence = a.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise ValueError(f"{ident}: evidence with a source locator is required")
        for ev in evidence:
            if not isinstance(ev, dict):
                raise ValueError(f"{ident}: evidence must be an object")
            text(ev.get("locator"), f"{ident}.evidence.locator")
            text(ev.get("quote"), f"{ident}.evidence.quote")
        r = q.get("rewrite")
        if not isinstance(r, dict):
            raise ValueError(f"{ident}: four-step rewrite is required")
        for _, key in STEPS:
            text(r.get(key), f"{ident}.rewrite.{key}")
        ds = r.get("data")
        if not isinstance(ds, dict) or ds.get("status") not in DATA_STATES:
            raise ValueError(f"{ident}: invalid data evidence status")
        text(ds.get("text"), f"{ident}.rewrite.data.text")
        strings(ds.get("needed", []), f"{ident}.data.needed")
        followups = q.get("followups")
        if not isinstance(followups, list) or len(followups) < 2:
            raise ValueError(f"{ident}: at least two followups are required")
        for fu in followups:
            if not isinstance(fu, dict):
                raise ValueError(f"{ident}: followup must be an object")
            text(fu.get("question"), f"{ident}.followup.question")
            text(fu.get("approach"), f"{ident}.followup.approach")
        p = q.get("practice", {})
        if not isinstance(p, dict) or p.get("priority") not in {"P0", "P1", "P2"}:
            raise ValueError(f"{ident}: invalid practice priority")
        for key in ("action", "done_when"):
            text(p.get(key), f"{ident}.practice.{key}")
        checks = q.get("verification", [])
        if not isinstance(checks, list):
            raise ValueError(f"{ident}.verification must be a list")
        for check in checks:
            if not isinstance(check, dict):
                raise ValueError(f"{ident}: verification must be an object")
            for key in ("claim", "status", "source", "note"):
                text(check.get(key), f"{ident}.verification.{key}")
    return data


def esc(value):
    return html.escape(str(value), quote=True)


def md_plain(value):
    value = html.escape(str(value), quote=False).replace("\r", "").replace("\n", " ")
    return re.sub(r"([\\`*_{}\[\]()#!|])", r"\\\1", value)


def fenced(value):
    runs = re.findall(r"`+", value)
    fence = "`" * max(3, 1 + max((len(x) for x in runs), default=0))
    return fence + "text\n" + value.rstrip() + "\n" + fence


def render_markdown(d):
    m, s, qs = d["metadata"], d["summary"], d["questions"]
    lines = ["# " + md_plain(d["title"]), "", "## 面试信息", ""]
    for label, key in (("公司", "company"), ("岗位", "role"), ("轮次", "round"), ("面试日期", "interview_date"), ("来源", "source_label")):
        lines.append(f"- {label}：{md_plain(m.get(key, '未提供'))}")
    lines += [f"- 本次收录：{len(qs)} 道实质性问题。{md_plain(m['coverage_note'])}", "", "## 整体复盘", "", s["headline"], ""]
    for label, key in (("表现亮点", "strengths"), ("主要问题", "issues"), ("优先改进", "priorities")):
        if s.get(key):
            lines += ["### " + label, ""] + ["- " + x for x in s[key]] + [""]
    if m.get("limitations"):
        lines += ["### 材料边界", ""] + ["- " + md_plain(x) for x in m["limitations"]] + [""]
    lines += ["## 逐题目录", ""]
    lines += [f"- [{q['id']} · {md_plain(q['question'])}](#{q['id'].lower()})" for q in qs]
    for q in qs:
        r, a, p = q["rewrite"], q["assessment"], q["practice"]
        lines += ["", f"<a id=\"{q['id'].lower()}\"></a>", f"## {q['id']} · {md_plain(q['question'])}", "",
                  f"- 原稿定位：{md_plain(q['locator'])}", f"- 考察意图：{md_plain(q['intent'])}",
                  f"- 原回答状态：{a['level']}；练习优先级：{p['priority']}", "", "### 原回答", "",
                  fenced(q["candidate_answer"]) if q["candidate_answer"].strip() else "原稿未提供可确认的本人回答。", "",
                  "### 点评与依据", "", a["reason"], ""]
        for ev in a["evidence"]:
            lines += ["原话定位：" + md_plain(ev["locator"]), "", fenced(ev["quote"]), ""]
        lines += ["### 详细优化回答", ""]
        for label, key in STEPS:
            lines += ["#### " + label, "", r[key], ""]
        ds = r["data"]
        lines += ["#### 数据", "", f"数据状态：**{ds['status']}**", "", ds["text"], ""]
        if ds.get("needed"):
            lines += ["需补充："] + ["- " + x for x in ds["needed"]] + [""]
        lines += ["### 追问准备", ""]
        for fu in q["followups"]:
            lines += ["**" + md_plain(fu["question"]) + "**", "", fu["approach"], ""]
        lines += ["### 练习任务", "", f"- 优先级：{p['priority']}", f"- 动作：{p['action']}", f"- 完成标准：{p['done_when']}", ""]
        if q.get("verification"):
            lines += ["### 核验记录", ""]
            for v in q["verification"]:
                lines += [f"- **{md_plain(v['claim'])}**：{md_plain(v['status'])}；来源：{md_plain(v['source'])}。{md_plain(v['note'])}"]
    return "\n".join(lines).rstrip() + "\n"


CSS = """
:root{color-scheme:light;--ink:#202b35;--muted:#64707c;--blue:#245c78;--line:#dbe2e7;--paper:#fff;--wash:#f4f6f8}
*{box-sizing:border-box}body{margin:0;background:var(--wash);color:var(--ink);font:16px/1.8 system-ui,-apple-system,'Segoe UI','Microsoft YaHei',sans-serif}
a{color:var(--blue);text-underline-offset:3px}button,input,select{font:inherit}button,select,input{border:1px solid var(--line);background:var(--paper);border-radius:5px;padding:7px 11px;color:var(--ink)}
button{cursor:pointer}a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid var(--blue);outline-offset:3px}
.shell{display:grid;grid-template-columns:235px minmax(0,920px);gap:34px;max-width:1230px;margin:auto;padding:32px 22px}aside{position:sticky;top:24px;align-self:start;max-height:92vh;overflow:auto}aside strong{font-size:14px}nav a{display:block;font-size:13px;padding:8px 0;border-bottom:1px solid var(--line);text-decoration:none}
main{min-width:0}h1{font-size:28px;line-height:1.4;margin:8px 0 14px}h2{font-size:21px;line-height:1.5}h3{font-size:17px;margin:20px 0 8px}h4{font-size:16px;margin:0 0 7px}.eyebrow{font-size:12px;letter-spacing:.13em;color:var(--blue)}.muted,small{color:var(--muted)}.meta{display:flex;flex-wrap:wrap;gap:4px 20px;font-size:13px}
.overview{border-top:3px solid var(--blue);padding-top:16px;margin:24px 0}.summary-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}.summary-grid h3{color:var(--blue)}ul{padding-left:21px}.limitations{font-size:13px;color:var(--muted);border-top:1px solid var(--line);padding-top:8px}.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin:25px 0 8px}.toolbar input{flex:1;min-width:180px}.count{font-size:13px;margin:8px 0 20px}
.question{background:var(--paper);padding:25px 28px;margin:0 0 24px;border:1px solid var(--line);border-radius:7px;scroll-margin-top:15px}.question h2{margin:8px 0 10px}.tags{display:flex;gap:8px;flex-wrap:wrap;align-items:center;font-size:12px}.qid{font-weight:700;color:var(--blue)}.tag{border:1px solid var(--line);padding:1px 8px;border-radius:4px}.steps{margin:20px 0;border-left:3px solid var(--blue);padding-left:20px}.step{margin:0 0 20px}.prose{white-space:pre-wrap;overflow-wrap:anywhere}.source{padding:13px 16px;background:var(--wash);border-left:2px solid var(--line);font-size:14px;white-space:pre-wrap;overflow-wrap:anywhere}.source small{display:block;margin-bottom:5px}details{margin:14px 0}summary{cursor:pointer;color:var(--blue);font-size:14px}details>.source,details>.prose{margin-top:10px}.practice{border-top:1px solid var(--line);padding-top:13px;font-size:14px}.practice p{margin:4px 0}.verification{font-size:13px}.followup{margin:12px 0}.followup p{margin:4px 0}.hidden,[hidden]{display:none!important}footer{font-size:12px;color:var(--muted);padding:16px 0}
@media(max-width:850px){.shell{grid-template-columns:1fr;gap:12px;padding:18px 13px}aside{position:static;max-height:160px}.summary-grid{grid-template-columns:1fr;gap:0}.question{padding:18px}h1{font-size:24px}}
@media print{body{background:white;font-size:11pt}.shell{display:block;max-width:none;padding:0}aside,.toolbar,.count{display:none}.question{padding:12px 0;border:0;border-top:1px solid #aaa;break-inside:auto}h2,h3,h4{break-after:avoid}.step,.source,.followup{break-inside:avoid}.summary-grid{display:block}.question[hidden]{display:block!important}a{color:inherit}details>summary{font-weight:bold}}
"""

JS = """
const search=document.getElementById('search'), priority=document.getElementById('priority');
const cards=[...document.querySelectorAll('.question')];
function filter(){const needle=search.value.trim().toLocaleLowerCase();let count=0;cards.forEach(card=>{const show=(!needle||card.dataset.search.includes(needle))&&(!priority.value||card.dataset.priority===priority.value);card.hidden=!show;if(show)count++});document.getElementById('count').textContent=`显示 ${count} / ${cards.length} 道问题`;document.getElementById('no-match').hidden=count!==0;}
search.addEventListener('input',filter);priority.addEventListener('change',filter);
document.getElementById('expand').addEventListener('click',()=>document.querySelectorAll('details').forEach(d=>d.open=true));
document.getElementById('collapse').addEventListener('click',()=>document.querySelectorAll('details').forEach(d=>d.open=false));
function printReport(){search.value='';priority.value='';filter();document.querySelectorAll('details').forEach(d=>d.open=true);window.print();}
document.getElementById('print').addEventListener('click',printReport);filter();
"""


def render_html(d):
    m, s, qs = d["metadata"], d["summary"], d["questions"]
    nav = ''.join(f'<a href="#{q["id"]}">{q["id"]} · {esc(q["question"])}</a>' for q in qs)
    meta = ''.join(f'<span>{label}：{esc(m.get(key,"未提供"))}</span>' for label,key in
                   (("公司","company"),("岗位","role"),("轮次","round"),("日期","interview_date")))
    summary = ''.join('<section><h3>'+label+'</h3><ul>'+''.join('<li>'+esc(x)+'</li>' for x in s[key])+'</ul></section>'
                      for label,key in (("表现亮点","strengths"),("主要问题","issues"),("优先改进","priorities")) if s.get(key))
    limits = '<section class="limitations"><strong>材料边界</strong><ul>'+''.join('<li>'+esc(x)+'</li>' for x in m['limitations'])+'</ul></section>' if m.get('limitations') else ''
    cards = []
    for q in qs:
        a,r,p=q['assessment'],q['rewrite'],q['practice']
        evidence=''.join('<div class="source"><small>'+esc(ev['locator'])+'</small>'+esc(ev['quote'])+'</div>' for ev in a['evidence'])
        answer=('<div class="source">'+esc(q['candidate_answer'])+'</div>') if q['candidate_answer'].strip() else '<p class="muted">原稿未提供可确认的本人回答。</p>'
        steps=''.join('<section class="step"><h4>'+label+'</h4><div class="prose">'+esc(r[key])+'</div></section>' for label,key in STEPS)
        ds=r['data'];needed='<ul>'+''.join('<li>'+esc(x)+'</li>' for x in ds['needed'])+'</ul>' if ds.get('needed') else ''
        steps+='<section class="step"><h4>数据 <small>· '+esc(ds['status'])+'</small></h4><div class="prose">'+esc(ds['text'])+'</div>'+needed+'</section>'
        followups=''.join('<section class="followup"><strong>'+esc(f['question'])+'</strong><p class="prose">'+esc(f['approach'])+'</p></section>' for f in q['followups'])
        checks=''.join('<li><strong>'+esc(v['claim'])+'</strong> · '+esc(v['status'])+'<br>'+esc(v['source'])+'<br>'+esc(v['note'])+'</li>' for v in q.get('verification',[]))
        checkblock='<details class="verification"><summary>核验记录</summary><ul>'+checks+'</ul></details>' if checks else ''
        searchdata=esc(json.dumps(q,ensure_ascii=False).lower())
        cards.append(f'''<article class="question" id="{q['id']}" data-priority="{p['priority']}" data-search="{searchdata}">
<div class="tags"><span class="qid">{q['id']}</span><span class="tag">{esc(a['level'])}</span><span class="tag">{p['priority']}</span><small>{esc(q['locator'])}</small></div>
<h2>{esc(q['question'])}</h2><p class="muted">考察意图：{esc(q['intent'])}</p>
<details><summary>查看本人原回答</summary>{answer}</details>
<h3>点评</h3><div class="prose">{esc(a['reason'])}</div><details><summary>查看原话证据</summary>{evidence}</details>
<h3>详细优化回答</h3><div class="steps">{steps}</div>
<details><summary>追问准备</summary>{followups}</details>
<section class="practice"><strong>练习任务 · {p['priority']}</strong><p class="prose">{esc(p['action'])}</p><p class="prose"><strong>完成标准：</strong>{esc(p['done_when'])}</p></section>{checkblock}</article>''')
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'">
<title>{esc(d['title'])}</title><style>{CSS}</style></head><body><div class="shell">
<aside><strong>面试逐题复盘</strong><nav aria-label="问题目录">{nav}</nav></aside><main>
<header><div class="eyebrow">INTERVIEW REVIEW</div><h1>{esc(d['title'])}</h1><div class="meta">{meta}</div><p class="muted">来源：{esc(m['source_label'])}</p></header>
<section class="overview"><h2>{esc(s['headline'])}</h2><p class="muted">本次收录 {len(qs)} 道实质性问题。{esc(m['coverage_note'])}</p><div class="summary-grid">{summary}</div>{limits}</section>
<div class="toolbar" role="search"><input id="search" type="search" placeholder="搜索问题、回答或知识点" aria-label="搜索问题、回答或知识点"><select id="priority" aria-label="练习优先级"><option value="">全部优先级</option><option>P0</option><option>P1</option><option>P2</option></select><button id="expand">展开全部</button><button id="collapse">收起原文与追问</button><button id="print">打印报告</button></div>
<p id="count" class="count"></p><p id="no-match" hidden>未找到匹配的问题，请调整筛选条件。</p>{''.join(cards)}
<footer>结论 → 机制 → 取舍 → 数据 · 与 post-interview.md 同源生成 · 内容仅在本地展示</footer></main></div><script>{JS}</script></body></html>'''


def write_outputs(data, out_dir, overwrite=False):
    validate(data)
    out = Path(out_dir)
    targets = (out / 'report.html', out / 'post-interview.md')
    if not overwrite and any(p.exists() for p in targets):
        raise FileExistsError('Outputs already exist; use a new folder or explicitly authorize --overwrite')
    rendered = (render_html(data), render_markdown(data))
    out.mkdir(parents=True, exist_ok=True)
    for path, content in zip(targets, rendered):
        path.write_text(content, encoding='utf-8')
    return targets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--out-dir', required=True, type=Path)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    if not args.input.is_absolute() or not args.out_dir.is_absolute():
        parser.error('Use absolute input and output paths')
    try:
        data = json.loads(args.input.read_text(encoding='utf-8-sig'))
        paths = write_outputs(data, args.out_dir, args.overwrite)
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Error: {exc}\n')
    print(json.dumps({'files':[str(p) for p in paths], 'questions':len(data['questions']),
                      'validation':'schema and rendering passed; semantic/visual review still required'},ensure_ascii=False))


if __name__ == '__main__':
    main()
