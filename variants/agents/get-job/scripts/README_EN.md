[简体中文](README.md) | **English**

# scripts

## generate_resume.py

Renders structured resume content from JSON into a consistent, professional DOCX template. It is the production tool used after Stage 2, “Resume Tailoring,” is complete: the skill develops and verifies the content using `references/resume-playbook.md`; this script handles layout only.

### Dependency

```bash
pip3 install python-docx
```

### Usage

```bash
python3 generate_resume.py <input.json> [-o output.docx]
```

Example:

```bash
python3 generate_resume.py sample_resume.en.json -o candidate_ai_product_resume.docx
```

### Fixed template specification

- Typeface: Aptos, with Microsoft YaHei as the East Asian fallback
- Page: A4 with narrow margins to support a concise one-page resume
- Name: centered, 18 pt, bold, restrained accent color
- Contact details: centered on one muted line
- Target role: a short positioning statement from the `objective` field
- Section headings: 12 pt, bold, with an accent-color bottom rule
- Experience entries: bold title, right-aligned date/location metadata, optional muted subtitle, and bullets
- Skills: bold category followed by its content

### Input JSON

See `sample_resume.en.json` for a complete English example. Its candidate, institution, employer, and claims are fictional; they demonstrate structure and evidence boundaries and must not be copied into a real application.

```json
{
  "locale": "en",
  "name": "Candidate Name",
  "contact": "City, State | candidate.email@example.com | 000-000-0000",
  "objective": "Target-role positioning statement",
  "sections": [
    {
      "title": "Education",
      "entries": [
        {
          "title": "Sample University — Degree",
          "meta": "Expected graduation",
          "subtitle": "Optional focus",
          "bullets": []
        }
      ]
    },
    {
      "title": "Core Project",
      "entries": [
        {
          "title": "Project name",
          "meta": "Date",
          "subtitle": "Role or scope",
          "bullets": ["Evidence-backed bullet one", "Evidence-backed bullet two"]
        }
      ]
    },
    {
      "title": "Skills",
      "type": "skills",
      "items": [
        {"category": "Product", "content": "Relevant skills"}
      ]
    }
  ]
}
```

Set the top-level `locale` to `"en"` for English labels and fallback copy. If `locale` is omitted, the existing Chinese behavior remains the default.

- `entries[].title` is recommended. If absent, the script inserts a visible placeholder and emits a warning.
- `meta` (right-aligned date/location), `subtitle` (role/focus), and `bullets` are optional.
- A section with `"type": "skills"` uses `items`; each item may be `{category, content}` or a plain string.
- The script strips accidental leading labels such as `Transfer sentence:`, `Transfer note:`, and `Transferability:` from bullets. This prevents internal drafting instructions from leaking into a submitted resume.

### Fault-tolerant behavior

The generator creates an inspectable DOCX when minor input gaps exist instead of failing immediately:

- Missing `name` or `contact`: inserts an English placeholder and writes a warning to stderr
- Missing or malformed `sections`: inserts an `Information to add` section
- Malformed sections, entries, or skill items: skips the affected item and writes a warning
- Non-array bullet: treats it as one bullet

These fallbacks keep the layout tool running; they do not certify content quality. Replace every placeholder and verify every claim against the candidate’s evidence before submission.

## quality_check.py

Scans public deliverables for structural omissions and internal drafting labels. It supplements the semantic review in `references/quality-gates.md`; it does not replace it.

### Usage

```bash
python3 quality_check.py <output-folder> [more-folders...]
```

English example:

```bash
python3 quality_check.py ../examples/en/ai-product-prototyping
```

The checker supports both the existing Chinese artifact names and the English structure under `interview-prep/`. It checks:

- Markdown files for internal labels such as `Transfer sentence:`, `kept for reference`, and `half-finished`
- Required English interview-prep files: `00-overview.md`, `01-resume-bullet-deep-dives.md`, `02-delivery-and-self-introduction.md`, and `99-post-interview-review.md`
- Round-specific files beginning at `03-`
- Public structure markers such as `Interview-stage map`, `Risk map`, `Resume-bullet coverage`, `Likely follow-ups`, and `Evidence boundary`
- `role-research.md` for both `Source coverage` and `Coverage gaps`

Exit codes:

- `0`: hard checks passed
- `1`: one or more required fixes were found

### Script self-checks

```bash
python3 -m unittest scripts/test_scripts.py
```

The tests verify English fallback text, English DOCX output without Chinese characters, the original Chinese default, and the English quality-check layout.

### Optional PDF conversion

```bash
# macOS; requires LibreOffice
soffice --headless --convert-to pdf <resume>.docx
# Or use the environment's PDF/DOCX tooling.
```
