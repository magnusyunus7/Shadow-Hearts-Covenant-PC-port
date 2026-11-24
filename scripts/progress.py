"""Draw docs/progress.svg from docs/status.json (hand-edited).

Usage: python scripts/progress.py            (run from the repository root)
States: "done" (counts 1), "partial" (counts 0.5), "todo" (counts 0).
"""
import json
import os
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS = os.path.join(ROOT, "docs", "status.json")
OUT = os.path.join(ROOT, "docs", "progress.svg")

BG, CARD, BORDER = "#0d1117", "#161b22", "#30363d"
TEXT, MUTED = "#e6edf3", "#8b949e"
COLORS = {"done": "#3fb950", "partial": "#d29922", "todo": "#484f58"}
LABELS = {"done": "done", "partial": "partial", "todo": "not yet"}
WEIGHT = {"done": 1.0, "partial": 0.5, "todo": 0.0}
FONT = "-apple-system,Segoe UI,Helvetica,Arial,sans-serif"

W = 900
PAD = 24
ROW = 26


def section(y, title, items, out):
    score = sum(WEIGHT[i["state"]] for i in items)
    pct = 100.0 * score / len(items)
    h = 74 + ROW * len(items) + 12
    out.append(f'<rect x="{PAD}" y="{y}" width="{W - 2 * PAD}" height="{h}" rx="8" fill="{CARD}" stroke="{BORDER}"/>')
    out.append(f'<text x="{PAD + 20}" y="{y + 32}" fill="{TEXT}" font-size="20" font-weight="600">{escape(title)}</text>')
    out.append(f'<text x="{W - PAD - 20}" y="{y + 32}" fill="{TEXT}" font-size="20" font-weight="600" text-anchor="end">{pct:.0f}%</text>')
    bar_w = W - 2 * PAD - 40
    out.append(f'<rect x="{PAD + 20}" y="{y + 44}" width="{bar_w}" height="10" rx="5" fill="#21262d"/>')
    if pct > 0:
        out.append(f'<rect x="{PAD + 20}" y="{y + 44}" width="{bar_w * pct / 100:.1f}" height="10" rx="5" fill="{COLORS["done"]}"/>')
    ty = y + 82
    for it in items:
        st = it["state"]
        out.append(f'<circle cx="{PAD + 28}" cy="{ty - 5}" r="6" fill="{COLORS[st]}"/>')
        out.append(f'<text x="{PAD + 44}" y="{ty}" fill="{TEXT}" font-size="14">{escape(it["name"])}</text>')
        note = it.get("note", "")
        right = LABELS[st] + (f" - {note}" if note else "")
        out.append(f'<text x="{W - PAD - 20}" y="{ty}" fill="{MUTED}" font-size="13" text-anchor="end">{escape(right)}</text>')
        ty += ROW
    return y + h + 16


def main():
    with open(STATUS, encoding="utf-8") as f:
        status = json.load(f)
    body = []
    y = 70
    y = section(y, "Story milestones", status["milestones"], body)
    y = section(y, "Systems", status["systems"], body)
    height = y + 8
    head = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" font-family="{FONT}">',
        f'<rect width="{W}" height="{height}" rx="10" fill="{BG}"/>',
        f'<text x="{PAD}" y="44" fill="{TEXT}" font-size="28" font-weight="700">Progress</text>',
        f'<text x="{W - PAD}" y="44" fill="{MUTED}" font-size="13" text-anchor="end">updated {escape(status["updated"])}'
        f' - green = done, amber = partial (counts half), grey = not yet</text>',
    ]
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(head + body + ["</svg>"]) + "\n")
    print("wrote", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
