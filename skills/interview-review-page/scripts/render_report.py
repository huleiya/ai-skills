#!/usr/bin/env python3
"""Render an evidence-based interview review to an A4 PDF report and Markdown.

Only Python's standard library is required. The PDF is printed by a locally
installed Chromium-based browser (Edge or Chrome) in headless mode from a
temporary, fully offline HTML file that is deleted afterwards. This script does
not analyze a transcript, execute embedded content, contact a network, or
publish anything.
"""
import argparse
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

# 「亮点／合格／薄弱」是报告展示档位；旧版 JSON 的三档按映射兼容。
LEVELS = {"亮点", "合格", "薄弱", "未作答", "转写不清"}
LEGACY_LEVELS = {"清晰": "亮点", "部分到位": "合格", "需重练": "薄弱"}
DATA_STATES = {"已核验", "原话口述", "待补", "不适用"}
STEPS = (("结论", "conclusion"), ("机制", "mechanism"), ("取舍", "tradeoffs"))
BROWSER_ENV = "INTERVIEW_REPORT_BROWSER"


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: expected non-empty text")
    return value


def strings(value, label, minimum=0):
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError(f"{label}: expected a list of non-empty strings")
    if len(value) < minimum:
        raise ValueError(f"{label}: expected at least {minimum} item(s)")


def level_of(q):
    raw = q["assessment"]["level"]
    return LEGACY_LEVELS.get(raw, raw)


def clock(value):
    """'00:12:51' -> 12:51, '01:02:03' -> 1:02:03, '05:30' -> 05:30."""
    m = re.search(r"\d{1,2}:\d{2}(?::\d{2})?", value or "")
    if not m:
        return ""
    parts = m.group(0).split(":")
    if len(parts) == 3 and int(parts[0]) == 0:
        parts = parts[1:]
    elif len(parts) == 3:
        parts[0] = str(int(parts[0]))
    return ":".join(parts)


def seconds(value, label):
    m = re.fullmatch(r"(?:(\d+):)?(\d{1,2}):(\d{2})", value.strip()) if isinstance(value, str) else None
    if not m:
        raise ValueError(f"{label}: expected mm:ss or hh:mm:ss")
    return int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + int(m.group(3))


def validate(data):
    if not isinstance(data, dict):
        raise ValueError("Report must be a JSON object")
    text(data.get("title"), "title")
    meta = data.get("metadata")
    if not isinstance(meta, dict):
        raise ValueError("metadata must be an object")
    for key in ("source_label", "coverage_note"):
        text(meta.get(key), f"metadata.{key}")
    for key in ("company", "role", "round", "interview_date", "candidate", "duration", "result", "eyebrow_note", "footer_note"):
        if key in meta:
            text(meta[key], f"metadata.{key}")
    strings(meta.get("limitations", []), "metadata.limitations")
    summary = data.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("summary must be an object")
    text(summary.get("headline"), "summary.headline")
    for key in ("strengths", "issues", "priorities"):
        strings(summary.get(key, []), f"summary.{key}")
    cards = summary.get("cards", [])
    if not isinstance(cards, list) or len(cards) > 3:
        raise ValueError("summary.cards: up to three cards")
    for c in cards:
        if not isinstance(c, dict) or c.get("kind") not in {"优势", "短板"}:
            raise ValueError("summary.cards: kind must be 优势 or 短板")
        text(c.get("title"), "summary.cards.title")
        text(c.get("text"), "summary.cards.text")
    for ab in summary.get("abilities", []):
        if not isinstance(ab, dict) or ab.get("score") not in {1, 2, 3, 4, 5}:
            raise ValueError("summary.abilities: score must be an integer 1-5")
        text(ab.get("name"), "summary.abilities.name")
        text(ab.get("note"), "summary.abilities.note")
    if summary.get("abilities"):
        text(summary.get("ability_note"), "summary.ability_note (state that scores are subjective)")
    timeline = summary.get("timeline", [])
    if not isinstance(timeline, list):
        raise ValueError("summary.timeline must be a list")
    for seg in timeline:
        if not isinstance(seg, dict):
            raise ValueError("summary.timeline items must be objects")
        text(seg.get("label"), "summary.timeline.label")
        text(seg.get("note"), "summary.timeline.note")
        if seconds(seg.get("end"), "timeline.end") <= seconds(seg.get("start"), "timeline.start"):
            raise ValueError("summary.timeline: end must be after start")
    rm = data.get("role_match")
    if rm is not None:
        if not isinstance(rm, dict):
            raise ValueError("role_match must be an object")
        for col in rm.get("columns", []):
            for key in ("label", "title", "text"):
                text(col.get(key) if isinstance(col, dict) else None, f"role_match.columns.{key}")
        strings(rm.get("matches", []), "role_match.matches")
        strings(rm.get("gaps", []), "role_match.gaps")
    for act in data.get("actions", []):
        if not isinstance(act, dict):
            raise ValueError("actions items must be objects")
        for key in ("title", "tag", "text"):
            text(act.get(key), f"actions.{key}")
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
        for key in ("locator", "question", "intent", "title", "better_answer"):
            text(q.get(key), f"{ident}.{key}")
        if not isinstance(q.get("candidate_answer"), str):
            raise ValueError(f"{ident}.candidate_answer must be text, possibly empty")
        a = q.get("assessment", {})
        if not isinstance(a, dict) or LEGACY_LEVELS.get(a.get("level"), a.get("level")) not in LEVELS:
            raise ValueError(f"{ident}: invalid assessment level")
        if not q["candidate_answer"].strip() and level_of(q) not in {"未作答", "转写不清"}:
            raise ValueError(f"{ident}: absent answer requires 未作答 or 转写不清")
        if q["candidate_answer"].strip():
            strings(q.get("answer_points"), f"{ident}.answer_points", 1)
        else:
            strings(q.get("answer_points", []), f"{ident}.answer_points")
        strings(q.get("lost_points"), f"{ident}.lost_points", 1)
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


# ---------------------------------------------------------------- Markdown

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
    for label, key in (("候选人", "candidate"), ("公司", "company"), ("岗位", "role"), ("轮次", "round"),
                       ("面试日期", "interview_date"), ("时长", "duration"), ("结果", "result"), ("来源", "source_label")):
        if key in m or key in ("company", "role", "round", "interview_date", "source_label"):
            lines.append(f"- {label}：{md_plain(m.get(key, '未提供'))}")
    lines += [f"- 本次收录：{len(qs)} 道实质性问题。{md_plain(m['coverage_note'])}", "", "## 整体复盘", "", s["headline"], ""]
    for label, key in (("表现亮点", "strengths"), ("主要问题", "issues"), ("优先改进", "priorities")):
        if s.get(key):
            lines += ["### " + label, ""] + ["- " + x for x in s[key]] + [""]
    if m.get("limitations"):
        lines += ["### 材料边界", ""] + ["- " + md_plain(x) for x in m["limitations"]] + [""]
    lines += ["## 逐题目录", ""]
    lines += [f"- [{q['id']} · {md_plain(q['title'])}](#{q['id'].lower()})（{level_of(q)}）" for q in qs]
    for q in qs:
        r, a, p = q["rewrite"], q["assessment"], q["practice"]
        lines += ["", f"<a id=\"{q['id'].lower()}\"></a>", f"## {q['id']} · {md_plain(q['title'])}", "",
                  "**面试官问。** " + md_plain(q["question"]), "",
                  f"- 原稿定位：{md_plain(q['locator'])}", f"- 考察意图：{md_plain(q['intent'])}",
                  f"- 原回答档位：{level_of(q)}；练习优先级：{p['priority']}", "", "### 原回答", "",
                  fenced(q["candidate_answer"]) if q["candidate_answer"].strip() else "原稿未提供可确认的本人回答。", ""]
        if q.get("answer_points"):
            lines += ["### 回答要点", ""] + ["- " + x for x in q["answer_points"]] + [""]
        lines += ["### 失分点", ""] + ["- " + x for x in q["lost_points"]] + [""]
        lines += ["### 点评与依据", "", a["reason"], ""]
        for ev in a["evidence"]:
            lines += ["原话定位：" + md_plain(ev["locator"]), "", fenced(ev["quote"]), ""]
        lines += ["### 更好的答法（速记）", "", q["better_answer"], "", "### 详细优化回答", ""]
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


# ---------------------------------------------------------------- PDF (print HTML)

def esc(value):
    return html.escape(str(value), quote=True)


def para(value):
    return esc(value).replace("\n", "<br>")


CSS = """
@page{size:A4;margin:12mm 0;background:#f3f4f6}
:root{--bg:#f3f4f6;--card:#fff;--ink:#111827;--body:#374151;--muted:#6b7280;--line:#e5e7eb;--blue:#1d4ed8;
--blue-soft:#eef4ff;--orange:#b45309;--gray:#6b7280;--navy:#111827;--navy-line:#374151;--chip:#f3f4f6}
*{box-sizing:border-box}
html{background:var(--bg);-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{margin:0;background:var(--bg);color:var(--body);font:12.5px/1.65 "Noto Sans SC","Source Han Sans SC","Source Han Sans CN","PingFang SC","Microsoft YaHei",sans-serif}
.mono{font-family:"JetBrains Mono","Cascadia Mono","SF Mono",Consolas,Menlo,monospace}
.page{padding:0 15mm}
h1,h2,h3,h4{color:var(--ink);margin:0}
.eyebrow{font-size:10.5px;color:var(--muted);margin:2mm 0 4mm}.eyebrow b{color:var(--blue);letter-spacing:.06em;font-weight:600}
h1{font-size:36px;line-height:1.22;font-weight:800;letter-spacing:.01em;margin-bottom:6mm}
.card{background:var(--card);border:1px solid var(--line);border-radius:9px}
.meta{display:grid;grid-template-columns:repeat(4,1fr)}.meta div{padding:10px 14px}.meta div+div{border-left:1px solid var(--line)}
.meta small{display:block;color:var(--muted);font-size:10.5px}.meta strong{color:var(--ink);font-size:13.5px}
.sec{display:flex;align-items:baseline;gap:9px;margin:12mm 0 5mm;break-after:avoid}.sec .n{color:var(--blue);font-size:10.5px;font-weight:700}.sec h2{font-size:21px;font-weight:800}
.hero{background:var(--navy);border-radius:11px;padding:22px 24px;color:#fff;break-inside:avoid}
.hero p{margin:0 0 16px;font-size:18.5px;line-height:1.6;font-weight:700;color:#fff}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.stats div{border:1px solid var(--navy-line);border-radius:8px;padding:10px 14px}
.stats b{display:block;font-size:26px;line-height:1.3;color:#fff}.stats span{font-size:10.5px;color:#d1d5db}.stats .hi b{color:#93c5fd}.stats .weak b{color:#fdba74}
.trio{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:10px;break-inside:avoid}.trio .card{padding:14px 16px}
.kind{font-size:10.5px;font-weight:700}.kind.good{color:var(--blue)}.kind.bad{color:var(--orange)}
.trio h3{font-size:14.5px;margin:4px 0 5px}.trio p{margin:0;font-size:11.5px}
.duo{display:grid;grid-template-columns:1fr 1fr;gap:16px}.duo.single{grid-template-columns:1fr}
.panel{padding:16px 20px}.ab,.tl,.judge{break-inside:avoid}
.ab{margin-bottom:12px}.ab-head{display:flex;justify-content:space-between;color:var(--ink);font-weight:700;font-size:12.5px}.ab-head .mono{font-size:11px}
.bar{display:grid;grid-template-columns:repeat(5,1fr);gap:4px;margin:5px 0 4px}.bar i{height:7px;border-radius:2px;background:var(--line)}
.bar.s-hi i.on{background:var(--blue)}.bar.s-mid i.on{background:var(--gray)}.bar.s-low i.on{background:var(--orange)}
.ab small{color:var(--muted);font-size:10.5px}.note{color:var(--muted);font-size:10px;margin-top:6px}
.stack{display:flex;height:30px;border-radius:6px;overflow:hidden;gap:2px;margin-bottom:14px}
.tl{display:grid;grid-template-columns:12px 1fr auto;gap:2px 8px;align-items:baseline;margin-bottom:10px}
.tl i{width:9px;height:9px;border-radius:2px;display:inline-block}.tl strong{color:var(--ink);font-size:12px}.tl .mono{font-size:10.5px;color:var(--body);white-space:nowrap}.tl small{grid-column:2/4;color:var(--muted);font-size:10.5px}
.judge{border-top:1px solid var(--line);margin-top:6px;padding-top:10px;font-size:11.5px}.judge b{color:var(--ink)}
.grid5{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}.idx{padding:9px 11px;break-inside:avoid}
.idx-top{display:flex;justify-content:space-between;align-items:center;color:var(--muted);font-size:10px}.idx b{display:block;color:var(--ink);font-size:12px;margin-top:5px;line-height:1.35}
.chip{display:inline-block;font-size:9.5px;font-weight:700;border-radius:10px;padding:1px 8px;background:var(--chip);color:var(--body);white-space:nowrap}
.chip.hi{background:#dbeafe;color:var(--blue)}.chip.weak{background:#ffedd5;color:var(--orange)}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:10px;color:var(--muted);margin-top:9px}.legend i{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:5px}
.q{padding:15px 20px 17px;margin-bottom:10px;border-top:3px solid var(--gray);break-inside:avoid}.q.hi{border-top-color:var(--blue)}.q.weak{border-top-color:var(--orange)}
.q-head{display:flex;align-items:center;gap:8px;margin-bottom:9px}.q-head .mono{font-size:11px;color:var(--ink);font-weight:700}.q-head .t{color:var(--muted);font-weight:400}.q-head h3{font-size:16px;flex:1}
.ask{background:var(--chip);border-radius:6px;padding:9px 13px;margin-bottom:11px;color:var(--body);font-size:12px}.ask b{color:var(--ink)}
.cols{display:grid;grid-template-columns:1fr 1fr .95fr;gap:16px}
.cols h4{font-size:11px;margin-bottom:5px}.cols h4.bad{color:var(--orange)}
.cols ul{margin:0;padding:0;list-style:none}.cols li{position:relative;padding-left:12px;margin-bottom:5px;font-size:11.2px;line-height:1.55}
.cols li:before{content:"";position:absolute;left:1px;top:.62em;width:4px;height:4px;border-radius:50%;background:#9ca3af}.cols .lost li:before{background:var(--orange)}
.better{background:var(--blue-soft);border-radius:7px;padding:11px 13px}.better h4{color:var(--blue)}.better p{margin:0;font-size:11.2px;line-height:1.6;color:var(--ink)}
.empty{color:var(--muted);font-size:11px}
.match{padding:16px 20px;break-inside:avoid}.match .three{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;padding-bottom:12px;border-bottom:1px solid var(--line);margin-bottom:12px}
.match small{color:var(--muted);font-size:10.5px}.match h3{font-size:14px;margin:3px 0}.match p{margin:0;font-size:11px}
.match .two{display:grid;grid-template-columns:1fr 1fr;gap:16px}.match h4{font-size:11px;color:var(--blue);margin-bottom:5px}.match h4.bad{color:var(--orange)}
.match ul{margin:0;padding-left:15px;font-size:11px}.match .two div:first-child li::marker{color:var(--blue)}.match .two div:last-child li::marker{color:var(--orange)}
.act{display:grid;grid-template-columns:44px 1fr;padding:13px 16px;margin-bottom:8px;break-inside:avoid}
.act .num{color:var(--blue);font-size:17px;font-weight:700}.act h3{font-size:14px;display:flex;align-items:center;gap:8px}.act p{margin:2px 0 0;font-size:11.5px}
footer{border-top:1px solid #d1d5db;margin-top:12mm;padding-top:10px;font-size:10.5px;color:var(--muted)}
"""

LEVEL_CLASS = {"亮点": "hi", "合格": "", "薄弱": "weak", "未作答": "weak", "转写不清": ""}
SEGMENT_COLORS = ("#9ca3af", "#1d4ed8", "#b45309", "#374151", "#60a5fa", "#d97706")


def chip(level):
    cls = LEVEL_CLASS.get(level, "")
    return f'<span class="chip {cls}">{esc(level)}</span>'


def bullets(items, empty="原稿未提供可确认的本人回答。"):
    if not items:
        return f'<p class="empty">{esc(empty)}</p>'
    return "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in items) + "</ul>"


def render_print_html(d):
    m, s, qs = d["metadata"], d["summary"], d["questions"]
    levels = [level_of(q) for q in qs]
    counter = iter(range(1, 20))

    def sec(title):
        return f'<div class="sec"><span class="n mono">{next(counter):02d}</span><h2>{esc(title)}</h2></div>'

    eyebrow = " · ".join(esc(x) for x in (m.get("interview_date", "日期未提供"), m.get("eyebrow_note")) if x)
    meta_cells = (("候选人", m.get("candidate", "未提供")), ("岗位", m.get("role", "未提供")),
                  ("时长", m.get("duration", "未提供")), ("结果", m.get("result", "未提供")))
    meta = "".join(f"<div><small>{label}</small><strong>{esc(v)}</strong></div>" for label, v in meta_cells)
    stats = [("题目总数", len(qs), ""), ("亮点", levels.count("亮点"), "hi"),
             ("合格", levels.count("合格"), ""), ("薄弱", sum(lv in {"薄弱", "未作答"} for lv in levels), "weak")]
    stat_html = "".join(f'<div class="{c}"><b>{n}</b><span>{label}</span></div>' for label, n, c in stats)
    trio = ""
    if s.get("cards"):
        trio = '<div class="trio">' + "".join(
            f'<div class="card"><div class="kind {"good" if c["kind"] == "优势" else "bad"}">{esc(c["kind"])}</div>'
            f'<h3>{esc(c["title"])}</h3><p>{esc(c["text"])}</p></div>' for c in s["cards"]) + "</div>"
    parts = [f'<div class="eyebrow"><b class="mono">INTERVIEW REVIEW</b> · {eyebrow}</div>',
             f"<h1>{para(d['title'])}</h1>", f'<div class="card meta">{meta}</div>', sec("综合结论"),
             f'<div class="hero"><p>{esc(s["headline"])}</p><div class="stats">{stat_html}</div></div>', trio]

    duo = []
    if s.get("abilities"):
        rows = []
        for ab in s["abilities"]:
            tone = "s-hi" if ab["score"] >= 4 else "s-mid" if ab["score"] == 3 else "s-low"
            cells = "".join(f'<i class="{"on" if i < ab["score"] else ""}"></i>' for i in range(5))
            rows.append(f'<div class="ab"><div class="ab-head"><span>{esc(ab["name"])}</span><span class="mono">{ab["score"]} / 5</span></div>'
                        f'<div class="bar {tone}">{cells}</div><small>{esc(ab["note"])}</small></div>')
        duo.append(sec("能力评估") + f'<div class="card panel">{"".join(rows)}<div class="note">{esc(s["ability_note"])}</div></div>')
    if s.get("timeline"):
        segs = s["timeline"]
        spans = [seconds(x["end"], "end") - seconds(x["start"], "start") for x in segs]
        total = sum(spans)
        stack, items = [], []
        for i, (seg, span) in enumerate(zip(segs, spans)):
            color = SEGMENT_COLORS[i % len(SEGMENT_COLORS)]
            share = round(span * 100 / total)
            stack.append(f'<span style="flex:{span};background:{color}"></span>')
            items.append(f'<div class="tl"><i style="background:{color}"></i><strong>{esc(seg["label"])}</strong>'
                         f'<span class="mono">{esc(clock(seg["start"]))}-{esc(clock(seg["end"]))} · 约 {share}%</span>'
                         f'<small>{esc(seg["note"])}</small></div>')
        judge = f'<div class="judge"><b>判断。</b>{esc(s["time_judgement"])}</div>' if s.get("time_judgement") else ""
        duo.append(sec("时间分布") + f'<div class="card panel"><div class="stack">{"".join(stack)}</div>{"".join(items)}{judge}</div>')
    if duo:
        parts.append(f'<div class="duo{" single" if len(duo) == 1 else ""}">' + "".join(f"<div>{x}</div>" for x in duo) + "</div>")

    index = "".join(f'<div class="card idx"><div class="idx-top"><span class="mono">{q["id"]} · {esc(q.get("time") or clock(q["locator"]))}</span>'
                    f'{chip(level_of(q))}</div><b>{esc(q["title"])}</b></div>' for q in qs)
    parts += [sec("题目索引"), f'<div class="grid5">{index}</div>',
              '<div class="legend"><span><i style="background:#1d4ed8"></i>亮点：可直接复用的答法</span>'
              '<span><i style="background:#6b7280"></i>合格：方向对，缺关键细节</span>'
              '<span><i style="background:#b45309"></i>薄弱：需要重新准备</span><span>时间点为转写中的约略位置</span></div>',
              sec("逐题复盘")]
    for q in qs:
        lv = level_of(q)
        parts.append(
            f'<article class="card q {LEVEL_CLASS.get(lv, "")}" id="{q["id"]}"><div class="q-head">'
            f'<span class="mono">{q["id"]} <span class="t">{esc(q.get("time") or clock(q["locator"]))}</span></span>'
            f'<h3>{esc(q["title"])}</h3>{chip(lv)}</div>'
            f'<div class="ask"><b>面试官问。</b>{para(q["question"])}</div><div class="cols">'
            f'<div><h4>回答要点</h4>{bullets(q.get("answer_points", []))}</div>'
            f'<div class="lost"><h4 class="bad">失分点</h4>{bullets(q["lost_points"])}</div>'
            f'<div class="better"><h4>更好的答法</h4><p>{para(q["better_answer"])}</p></div></div></article>')

    rm = d.get("role_match")
    if rm:
        three = "".join(f'<div><small>{esc(c["label"])}</small><h3>{esc(c["title"])}</h3><p>{esc(c["text"])}</p></div>'
                        for c in rm.get("columns", []))
        parts += [sec("岗位匹配"), f'<div class="card match">{"<div class=three>" + three + "</div>" if three else ""}'
                  f'<div class="two"><div><h4>匹配点</h4>{bullets(rm.get("matches", []), "未提供")}</div>'
                  f'<div><h4 class="bad">差距</h4>{bullets(rm.get("gaps", []), "未提供")}</div></div></div>']
    actions = d.get("actions") or [{"title": x, "tag": "待安排", "text": ""} for x in s.get("priorities", [])]
    if actions:
        parts.append(sec("行动清单"))
        for i, act in enumerate(actions, 1):
            body = f"<p>{esc(act['text'])}</p>" if act["text"] else ""
            parts.append(f'<div class="card act"><span class="num mono">{i:02d}</span><div><h3>{esc(act["title"])}'
                         f'<span class="chip">{esc(act["tag"])}</span></h3>{body}</div></div>')
    footer = m.get("footer_note") or f'依据{m.get("source_label")}整理。{m["coverage_note"]}'
    parts.append(f"<footer>{esc(footer)}</footer>")
    return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; img-src data:\">"
            f"<title>{esc(d['title'])}</title><style>{CSS}</style></head><body><main class=\"page\">"
            + "".join(parts) + "</main></body></html>")


def find_browser(explicit=None):
    candidates = [explicit, os.environ.get(BROWSER_ENV)]
    for env in ("PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA"):
        root = os.environ.get(env)
        if root:
            candidates += [os.path.join(root, "Microsoft", "Edge", "Application", "msedge.exe"),
                           os.path.join(root, "Google", "Chrome", "Application", "chrome.exe")]
    candidates += ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                   "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                   "/Applications/Chromium.app/Contents/MacOS/Chromium"]
    candidates += [shutil.which(n) for n in ("msedge", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome")]
    for c in candidates:
        if c and Path(c).is_file():
            return c
    raise FileNotFoundError(f"No Edge/Chrome/Chromium found for PDF printing; pass --browser or set {BROWSER_ENV}")


def print_pdf(html_text, pdf_path, browser):
    with tempfile.TemporaryDirectory(prefix="interview-report-") as tmp:
        src = Path(tmp) / "report-print.html"
        src.write_text(html_text, encoding="utf-8")
        out = Path(tmp) / "report.pdf"
        cmd = [browser, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
               "--disable-extensions", "--disable-background-networking", f"--user-data-dir={Path(tmp) / 'profile'}",
               "--no-pdf-header-footer", "--print-to-pdf-no-header", f"--print-to-pdf={out}", src.as_uri()]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if not out.is_file() or out.stat().st_size == 0:
            raise RuntimeError(f"Browser did not produce a PDF (exit {proc.returncode}): {proc.stderr.strip()[-400:]}")
        shutil.copyfile(out, pdf_path)


def write_outputs(data, out_dir, overwrite=False, browser=None):
    validate(data)
    out = Path(out_dir)
    targets = (out / "report.pdf", out / "post-interview.md")
    if not overwrite and any(p.exists() for p in targets):
        raise FileExistsError("Outputs already exist; use a new folder or explicitly authorize --overwrite")
    exe = find_browser(browser)
    page, md = render_print_html(data), render_markdown(data)
    out.mkdir(parents=True, exist_ok=True)
    print_pdf(page, targets[0], exe)
    targets[1].write_text(md, encoding="utf-8")
    return targets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--browser", help=f"Path to Edge/Chrome/Chromium; defaults to ${BROWSER_ENV} or auto-detect")
    args = parser.parse_args()
    if not args.input.is_absolute() or not args.out_dir.is_absolute():
        parser.error("Use absolute input and output paths")
    try:
        data = json.loads(args.input.read_text(encoding="utf-8-sig"))
        paths = write_outputs(data, args.out_dir, args.overwrite, args.browser)
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    print(json.dumps({"files": [str(p) for p in paths], "questions": len(data["questions"]),
                      "validation": "schema and rendering passed; open the PDF to review layout"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
