#!/usr/bin/env python3
"""Render one resume JSON to matching Markdown and an embedded-font A4 PDF.

Dependencies: reportlab, pypdf. No network or private repository access.
"""
import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape


def validate(data):
    if not isinstance(data, dict):
        raise ValueError('Input must be a JSON object')
    for key in ('name', 'target'):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f'{key} must be a nonempty string')
    if not isinstance(data.get('summary', ''), str):
        raise ValueError('summary must be a string')
    contact = data.get('contact', [])
    if not isinstance(contact, list) or any(not isinstance(x, str) for x in contact):
        raise ValueError('contact must be an array of strings')
    sections = data.get('sections')
    if not isinstance(sections, list) or not sections:
        raise ValueError('sections must be a nonempty array')
    for section in sections:
        if not isinstance(section, dict) or not isinstance(section.get('title'), str) or not section['title'].strip():
            raise ValueError('Each section needs a title')
        if not isinstance(section.get('items'), list) or not section['items']:
            raise ValueError('Each section needs items')
        for item in section['items']:
            if not isinstance(item, dict):
                raise ValueError('Each item must be an object')
            for key in ('title', 'subtitle', 'period', 'stack', 'description'):
                if not isinstance(item.get(key, ''), str):
                    raise ValueError(f'Item {key} must be a string')
            bullets = item.get('bullets', [])
            if not isinstance(bullets, list):
                raise ValueError('bullets must be an array')
            for bullet in bullets:
                if isinstance(bullet, str) and bullet.strip():
                    continue
                if (isinstance(bullet, dict) and isinstance(bullet.get('text'), str)
                        and bullet['text'].strip() and isinstance(bullet.get('label', ''), str)):
                    continue
                raise ValueError('Bullet must be a nonempty string or {label, text}')
            if not item.get('title') and not bullets:
                raise ValueError('Item requires a title or bullets')
    return data


def bullet_parts(bullet):
    return ('', bullet) if isinstance(bullet, str) else (bullet.get('label', ''), bullet['text'])


def blocks(data):
    """Single ordered source for both formats and text-completeness checks."""
    yield 'name', data['name']
    yield 'target', data['target']
    if data.get('contact'):
        yield 'contact', '  |  '.join(data['contact'])
    if data.get('summary'):
        yield 'summary', data['summary']
    for section in data['sections']:
        yield 'section', section['title']
        for item in section['items']:
            if item.get('title'):
                yield 'item', item['title']
            meta = '  |  '.join(item[k] for k in ('subtitle', 'period') if item.get(k))
            if meta:
                yield 'meta', meta
            for key in ('stack', 'description'):
                if item.get(key):
                    yield key, item[key]
            for bullet in item.get('bullets', []):
                label, text = bullet_parts(bullet)
                yield 'bullet', (label, text)


def plain(value):
    return (value[0] + '：' if value[0] else '') + value[1] if isinstance(value, tuple) else value


def markdown(data):
    lines = []
    for kind, value in blocks(data):
        if kind == 'bullet':
            label, text = value
            lines.append('- ' + (f'**{label}：**' if label else '') + text)
        else:
            prefix = {'name': '# ', 'section': '## ', 'item': '### '}.get(kind, '')
            lines.extend(['', prefix + value, ''])
    return '\n'.join(lines).strip() + '\n'


def fonts(args, all_text):
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    candidates = [
        (Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/msyh.ttc',
         Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/msyhbd.ttc'),
        (Path('/System/Library/Fonts/STHeiti Light.ttc'), Path('/System/Library/Fonts/STHeiti Medium.ttc')),
        (Path('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'), None),
    ]
    if args.font:
        chosen = (Path(args.font), Path(args.bold_font) if args.bold_font else None)
    else:
        chosen = next((pair for pair in candidates if pair[0].is_file()), None)
    if not chosen:
        raise ValueError('No CJK TrueType font found. Supply --font and optionally --bold-font.')
    regular, bold = chosen
    bold = Path(args.bold_font) if args.bold_font else bold
    if not bold or not bold.is_file():
        bold = regular
    for name, path in [('Resume', regular), ('ResumeBold', bold)]:
        font = TTFont(name, str(path), subfontIndex=0)
        missing = sorted({ch for ch in all_text if not ch.isspace() and ord(ch) not in font.face.charToGlyph})
        if missing:
            raise ValueError(f'Font {path.name} missing characters: {" ".join(missing[:20])}')
        pdfmetrics.registerFont(font)
    pdfmetrics.registerFontFamily('Resume', normal='Resume', bold='ResumeBold', italic='Resume', boldItalic='ResumeBold')


def render(data, args, path):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from pypdf import PdfReader

    rows = list(blocks(data))
    footer_text = '样式预览 / 非投递简历' if args.preview else data['name']
    fonts(args, ''.join(plain(value) for _, value in rows) + footer_text + '0123456789/：')
    accent = colors.HexColor(args.accent)
    body = ParagraphStyle('body', fontName='Resume', fontSize=args.body_size,
                          leading=args.body_size * 1.48, textColor=colors.HexColor('#222d38'),
                          wordWrap='CJK', alignment=TA_LEFT, spaceAfter=4,
                          allowWidows=0, allowOrphans=0)
    styles = {
        'name': ParagraphStyle('name', parent=body, fontName='ResumeBold', fontSize=25, leading=33, textColor=accent, spaceAfter=3, keepWithNext=True),
        'target': ParagraphStyle('target', parent=body, fontSize=12, leading=18, textColor=accent, keepWithNext=True),
        'contact': ParagraphStyle('contact', parent=body, fontSize=9.4, leading=14, textColor=colors.HexColor('#526171'), keepWithNext=True),
        'section': ParagraphStyle('section', parent=body, fontName='ResumeBold', fontSize=12, leading=18, textColor=accent, spaceBefore=10, spaceAfter=6, keepWithNext=True, borderWidth=0, borderPadding=0),
        'item': ParagraphStyle('item', parent=body, fontName='ResumeBold', fontSize=10.8, leading=16, spaceBefore=5, keepWithNext=True),
        'meta': ParagraphStyle('meta', parent=body, fontSize=9.3, leading=14, textColor=colors.HexColor('#526171'), keepWithNext=True),
        'stack': ParagraphStyle('stack', parent=body, fontSize=9.3, leading=14, textColor=accent, keepWithNext=True),
        'bullet': ParagraphStyle('bullet', parent=body, leftIndent=9, firstLineIndent=-9, splitLongWords=True),
    }
    story = []
    for kind, value in rows:
        if kind == 'bullet':
            label, text = value
            content = '- ' + (f'<b>{escape(label)}：</b>' if label else '') + escape(text)
        else:
            content = escape(value)
        story.append(Paragraph(content.replace('\n', '<br/>'), styles.get(kind, body)))
    story.append(Spacer(1, 2))
    width, height = A4

    def draw_page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(accent)
        canvas.rect(16 * mm, height - 11 * mm, 20 * mm, 1.2 * mm, fill=1, stroke=0)
        canvas.setStrokeColor(colors.HexColor('#d9e1e8'))
        canvas.line(16 * mm, 12 * mm, width - 16 * mm, 12 * mm)
        canvas.setFont('Resume', 8)
        canvas.setFillColor(colors.HexColor('#657385'))
        canvas.drawString(16 * mm, 7.8 * mm, footer_text)
        canvas.drawRightString(width - 16 * mm, 7.8 * mm, str(doc.page))
        canvas.restoreState()

    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=16 * mm,
                            leftMargin=16 * mm, topMargin=16 * mm, bottomMargin=17 * mm,
                            title=data['name'] + ' - ' + data['target'], author=data['name'])
    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    reader = PdfReader(path)
    if not 1 <= len(reader.pages) <= args.max_pages:
        raise ValueError(f'PDF has {len(reader.pages)} pages (maximum {args.max_pages}); shorten content before export.')
    normalize = lambda text: re.sub(r'\s+', '', text)
    page_texts = []
    for number, page in enumerate(reader.pages, 1):
        # draw_page writes the footer before Platypus writes body text. Strip only
        # that known prefix: visitor coordinates can describe the END of a text
        # run and would incorrectly drop long paragraphs near the page bottom.
        extracted_page = page.extract_text() or ''
        prefix = f'{footer_text}\n{number}\n'
        if not extracted_page.startswith(prefix):
            raise ValueError('Unexpected PDF footer extraction order; inspect the generated PDF')
        page_texts.append(extracted_page[len(prefix):])
    extracted = normalize('\n'.join(page_texts))
    cursor = 0
    for kind, value in rows:
        wanted = normalize(plain(value))
        position = extracted.find(wanted, cursor)
        if position < 0:
            raise ValueError(f'PDF text missing or out of order ({kind}): {wanted[:50]}')
        cursor = position + len(wanted)
    return len(reader.pages)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--out-dir', required=True, type=Path)
    parser.add_argument('--font')
    parser.add_argument('--bold-font')
    parser.add_argument('--body-size', type=float, default=10.2)
    parser.add_argument('--accent', default='#16324f')
    parser.add_argument('--max-pages', type=int, default=2)
    parser.add_argument('--text-only', action='store_true')
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    if not 9.5 <= args.body_size <= 12:
        parser.error('--body-size must be 9.5..12; edit content rather than shrinking further')
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', args.accent):
        parser.error('--accent must be #RRGGBB')
    if args.max_pages < 1:
        parser.error('--max-pages must be positive')
    data = validate(json.loads(args.input.read_text(encoding='utf-8-sig')))
    text = markdown(data)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    md = args.out_dir / 'resume.md'
    pdf = args.out_dir / 'resume.pdf'
    if md.exists() and md.read_text(encoding='utf-8') != text and not args.overwrite:
        raise ValueError('Existing resume.md differs; use a new output folder or --overwrite')
    if not args.text_only and pdf.exists() and not args.overwrite:
        raise ValueError('Existing resume.pdf; use a new output folder or --overwrite')
    if args.text_only:
        md.write_text(text, encoding='utf-8')
        print(json.dumps({'markdown': str(md)}, ensure_ascii=False))
        return
    with tempfile.TemporaryDirectory(prefix='resume-render-', dir=args.out_dir) as tmp:
        stage = Path(tmp) / 'resume.pdf'
        pages = render(data, args, stage)
        stage.replace(pdf)
    md.write_text(text, encoding='utf-8')
    print(json.dumps({'markdown': str(md), 'pdf': str(pdf), 'pages': pages,
                      'text_verified': True, 'visual_review_required': True}, ensure_ascii=False))


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    try:
        main()
    except Exception as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
