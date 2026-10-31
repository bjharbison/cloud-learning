#!/usr/bin/env python3
"""Render a course infographic from a JSON spec to PNG.

Usage:  python3 render.py spec.json out.png
Needs:  pip install playwright && playwright install chromium

One shared visual language for every learning repo: dark canvas, numbered
colour-coded steps, monospace keywords, a callout for the rule that trips
people up. Layouts:

  "steps"  numbered sequence (an order things happen in). Optional
           "written" strip shows how the written order maps to step numbers.
  "cards"  2-column grid of concepts (comparisons, building blocks).
  "compare" two side-by-side panels (before/after, wrong/right). Each
           panel: {label, key, tone: bad|good|neutral, code [lines],
           flow [text], result}.
  "matrix" rows x columns grid (layered stacks, who-owns-what tables).
           columns [labels]; rows [{key, desc?, tag?, cells}]; a cell is a
           string or {text, sub, tone}. "tones" maps a cell text or tone
           name to a palette hue: that cell is drawn as a filled chip.

Spec keys: layout, eyebrow, title, accent (word in title to highlight),
subtitle, steps|cards [{key, desc, note}] | panels | columns+rows+tones,
written [{text, step}],
callout {label, text}, footer.
"""
import html
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

# Eight hues, ordered as a warm-to-cool walk so sequences read top to bottom.
PALETTE = ["#FF8A3D", "#F5C542", "#7ED957", "#2FD4B4", "#3DA9FC",
           "#7B6CFF", "#C86BFA", "#FF5C8A"]

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0B0D12;color:#E8ECF3;font-family:Inter,sans-serif;width:1080px}
.wrap{padding:64px 64px 48px}
.eyebrow{font:600 20px/1 'DejaVu Sans Mono',monospace;letter-spacing:.14em;
  text-transform:uppercase;color:#8A93A6;margin-bottom:18px}
h1{font:800 64px/1.05 'Inter Display',Inter,sans-serif;letter-spacing:-.02em}
h1 em{font-style:normal;background:linear-gradient(90deg,#F5C542,#FF8A3D);
  -webkit-background-clip:text;color:transparent}
.sub{font-size:24px;line-height:1.45;color:#AEB6C6;margin:20px 0 40px;max-width:900px}
.steps{display:flex;flex-direction:column;gap:14px;position:relative}
.step{display:grid;grid-template-columns:72px 1fr auto;align-items:center;gap:22px;
  background:#141821;border:1px solid #232938;border-left:6px solid var(--c);
  border-radius:16px;padding:18px 26px 18px 18px}
.num{width:64px;height:64px;border-radius:50%;background:var(--c);color:#0B0D12;
  display:flex;align-items:center;justify-content:center;font:800 32px/1 Inter,sans-serif}
.key{font:700 30px/1.1 'DejaVu Sans Mono',monospace;color:var(--c)}
.desc{font-size:21px;line-height:1.4;color:#C9D0DC;margin-top:6px}
.note{font:600 19px/1.2 'DejaVu Sans Mono',monospace;color:#E8ECF3;background:#1D2330;
  border:1px solid #2C3446;border-radius:999px;padding:10px 18px;white-space:nowrap}
.note.dim{color:#6E7789}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.card{background:#141821;border:1px solid #232938;border-top:6px solid var(--c);
  border-radius:16px;padding:24px}
.card .key{font-size:26px}
.card .note{display:inline-block;margin-top:14px}
.compare{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.panel{background:#141821;border:1px solid #232938;border-top:6px solid var(--c);
  border-radius:16px;padding:24px;display:flex;flex-direction:column}
.plabel{font:700 17px/1 'DejaVu Sans Mono',monospace;letter-spacing:.12em;
  text-transform:uppercase;color:var(--c);margin-bottom:12px}
.panel .key{font-size:24px;line-height:1.3;color:#E8ECF3}
.code{margin-top:16px;background:#10141C;border:1px solid #232938;border-radius:12px;
  padding:14px 16px;font:500 17px/1.6 'DejaVu Sans Mono',monospace;color:#C9D0DC;white-space:pre}
.code .hl{color:var(--c);font-weight:700}
.flow{margin-top:18px;display:flex;flex-direction:column;gap:12px;flex:1}
.flow div{display:grid;grid-template-columns:30px 1fr;gap:10px;font-size:19px;line-height:1.4;color:#C9D0DC}
.flow i{font-style:normal;width:30px;height:30px;border-radius:50%;background:#1D2330;
  border:1px solid var(--c);color:var(--c);display:flex;align-items:center;justify-content:center;
  font:800 15px/1 Inter,sans-serif;margin-top:1px}
.flow code{font-family:'DejaVu Sans Mono',monospace;font-size:.88em;background:#1D2330;
  padding:1px 6px;border-radius:5px}
.flow b{color:#E8ECF3}
.result{margin-top:20px;align-self:flex-start;font:700 22px/1.2 'DejaVu Sans Mono',monospace;
  color:#0B0D12;background:var(--c);border-radius:999px;padding:10px 20px}
.matrix{display:grid;gap:10px;align-items:stretch}
.mh{font:700 17px/1.2 'DejaVu Sans Mono',monospace;letter-spacing:.1em;text-transform:uppercase;
  color:#8A93A6;text-align:center;align-self:end;padding-bottom:4px}
.mrow{background:#141821;border:1px solid #232938;border-left:6px solid var(--c);border-radius:14px;
  padding:12px 16px;display:flex;flex-direction:column;justify-content:center}
.mrow .key{font-size:22px;line-height:1.2}
.mrow .desc{font-size:17px;margin-top:4px}
.tag{display:inline-block;margin-top:8px;align-self:flex-start;font:700 14px/1 'DejaVu Sans Mono',monospace;
  letter-spacing:.08em;text-transform:uppercase;color:#0B0D12;background:var(--c);border-radius:999px;padding:6px 10px}
.cell{border-radius:14px;border:1px dashed #2C3446;background:#10141C;display:flex;flex-direction:column;
  align-items:center;justify-content:center;text-align:center;padding:10px 8px;min-height:64px}
.cell .t{font:600 19px/1.25 'DejaVu Sans Mono',monospace;color:#AEB6C6}
.cell .s{font:500 15px/1.3 'DejaVu Sans Mono',monospace;color:#6E7789;margin-top:4px}
.cell.on{background:var(--c);border:1px solid var(--c)}
.cell.on .t{color:#0B0D12;font-weight:800}
.cell.on .s{color:#1D2330}
.written{margin-top:36px;background:#10141C;border:1px dashed #2C3446;border-radius:16px;
  padding:22px 26px}
.written h2{font:600 18px/1 'DejaVu Sans Mono',monospace;letter-spacing:.12em;
  text-transform:uppercase;color:#8A93A6;margin-bottom:16px}
.line{display:flex;align-items:center;gap:14px;font:500 22px/1.6 'DejaVu Sans Mono',monospace}
.line span:last-child{white-space:pre}
.badge{min-width:34px;height:34px;border-radius:50%;background:var(--c);color:#0B0D12;
  display:inline-flex;align-items:center;justify-content:center;font:800 17px/1 Inter,sans-serif}
.callout{margin-top:28px;display:flex;gap:20px;align-items:flex-start;background:#1F1A0E;
  border:1px solid #5C4A17;border-radius:16px;padding:22px 26px}
.bang{flex:none;width:44px;height:44px;border-radius:50%;background:#F5C542;color:#0B0D12;
  display:flex;align-items:center;justify-content:center;font:900 26px/1 Inter,sans-serif}
.callout p{font-size:21px;line-height:1.5;color:#E9DFC4}
.callout b{color:#F5C542}
.callout code{white-space:nowrap}
.callout code,.desc code{font-family:'DejaVu Sans Mono',monospace;font-size:.9em;
  background:#2A2414;padding:1px 6px;border-radius:5px}
.desc code{background:#1D2330}
footer{margin-top:36px;display:flex;justify-content:space-between;font:500 17px/1
  'DejaVu Sans Mono',monospace;color:#5F687A}
"""


def rich(text):
    """Escape, then allow `code` spans and **bold**."""
    out = html.escape(text)
    parts = out.split("`")
    out = "".join(f"<code>{p}</code>" if i % 2 else p for i, p in enumerate(parts))
    parts = out.split("**")
    return "".join(f"<b>{p}</b>" if i % 2 else p for i, p in enumerate(parts))


def colour(i):
    return PALETTE[i % len(PALETTE)]


def build(spec):
    title = html.escape(spec["title"])
    if spec.get("accent"):
        acc = html.escape(spec["accent"])
        title = title.replace(acc, f"<em>{acc}</em>", 1)
    body = [f'<div class="eyebrow">{html.escape(spec.get("eyebrow", ""))}</div>',
            f"<h1>{title}</h1>",
            f'<p class="sub">{rich(spec.get("subtitle", ""))}</p>']

    if spec.get("layout", "steps") == "steps":
        rows = []
        for i, s in enumerate(spec["steps"]):
            note = s.get("note", "")
            dim = " dim" if s.get("dim") else ""
            note_html = f'<div class="note{dim}">{rich(note)}</div>' if note else "<div></div>"
            rows.append(
                f'<div class="step" style="--c:{colour(i)}"><div class="num">{i+1}</div>'
                f'<div><div class="key">{html.escape(s["key"])}</div>'
                f'<div class="desc">{rich(s["desc"])}</div></div>{note_html}</div>')
        body.append(f'<div class="steps">{"".join(rows)}</div>')
    elif spec["layout"] == "compare":
        tones = {"bad": "#FF5C8A", "good": "#7ED957", "neutral": "#3DA9FC"}
        panels = []
        for i, pn in enumerate(spec["panels"]):
            c = tones.get(pn.get("tone"), colour(i))
            code = "\n".join(
                f'<span class="hl">{html.escape(l[2:])}</span>' if l.startswith("> ") else html.escape(l)
                for l in pn.get("code", []))
            flow = "".join(f"<div><i>{j+1}</i><span>{rich(f)}</span></div>"
                           for j, f in enumerate(pn.get("flow", [])))
            res = f'<div class="result">{rich(pn["result"])}</div>' if pn.get("result") else ""
            panels.append(
                f'<div class="panel" style="--c:{c}"><div class="plabel">{html.escape(pn.get("label", ""))}</div>'
                f'<div class="key">{html.escape(pn.get("key", ""))}</div>'
                f'{f"<div class=code>{code}</div>" if code else ""}'
                f'<div class="flow">{flow}</div>{res}</div>')
        body.append(f'<div class="compare">{"".join(panels)}</div>')
    elif spec["layout"] == "matrix":
        tones = spec.get("tones", {})
        cols = spec["columns"]
        grid = [f'<div class="mh"></div>'] + [f'<div class="mh">{rich(c)}</div>' for c in cols]
        for i, r in enumerate(spec["rows"]):
            rc = r.get("colour", colour(i))
            desc = f'<div class="desc">{rich(r["desc"])}</div>' if r.get("desc") else ""
            tag = f'<div class="tag">{html.escape(r["tag"])}</div>' if r.get("tag") else ""
            grid.append(f'<div class="mrow" style="--c:{rc}"><div class="key">{html.escape(r["key"])}</div>'
                        f'{desc}{tag}</div>')
            for cell in r["cells"]:
                if isinstance(cell, str):
                    cell = {"text": cell}
                t = cell.get("tone", cell.get("text", ""))
                hue = tones.get(t)
                cls = "cell on" if hue else "cell"
                style = f' style="--c:{hue}"' if hue else ""
                sub = f'<div class="s">{rich(cell["sub"])}</div>' if cell.get("sub") else ""
                grid.append(f'<div class="{cls}"{style}><div class="t">{rich(cell.get("text", ""))}</div>{sub}</div>')
        first = spec.get("label_width", "260px")
        body.append(f'<div class="matrix" style="grid-template-columns:{first} repeat({len(cols)},1fr)">'
                    f'{"".join(grid)}</div>')
    else:
        cards = []
        for i, c in enumerate(spec["cards"]):
            note = f'<div class="note">{rich(c["note"])}</div>' if c.get("note") else ""
            cards.append(
                f'<div class="card" style="--c:{colour(i)}"><div class="key">'
                f'{html.escape(c["key"])}</div><div class="desc">{rich(c["desc"])}</div>{note}</div>')
        body.append(f'<div class="cards">{"".join(cards)}</div>')

    if spec.get("written"):
        lines = []
        for w in spec["written"]:
            badge = (f'<span class="badge" style="--c:{colour(w["step"]-1)}">{w["step"]}</span>'
                     if w.get("step") else '<span style="min-width:34px"></span>')
            lines.append(f'<div class="line">{badge}<span>{html.escape(w["text"])}</span></div>')
        body.append(f'<div class="written"><h2>{html.escape(spec.get("written_title", "As you write it"))}'
                    f'</h2>{"".join(lines)}</div>')

    if spec.get("callout"):
        c = spec["callout"]
        body.append(f'<div class="callout"><div class="bang">!</div><p><b>{html.escape(c["label"])}</b> '
                    f'{rich(c["text"])}</p></div>')

    foot = spec.get("footer", ["", ""])
    body.append(f"<footer><span>{html.escape(foot[0])}</span><span>{html.escape(foot[1])}</span></footer>")
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f'<body><div class="wrap">{"".join(body)}</div></body></html>')


def main():
    spec = json.loads(Path(sys.argv[1]).read_text())
    out = Path(sys.argv[2])
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 800}, device_scale_factor=2)
        page.set_content(build(spec), wait_until="networkidle")
        page.locator(".wrap").screenshot(path=str(out))
        browser.close()
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
