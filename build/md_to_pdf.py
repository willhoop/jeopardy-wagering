"""Render one Markdown file to a PDF companion.

Usage:
    python build/md_to_pdf.py <input.md> <output.pdf>

The script converts Markdown to HTML with Python-Markdown (extensions:
tables, fenced_code, toc) and applies one light print stylesheet.

Renderers, in order:
  1. WeasyPrint (the intended renderer).
  2. Headless Microsoft Edge or Google Chrome (--print-to-pdf).

WeasyPrint needs the GTK/Pango C libraries. On a Windows machine without
GTK, `import weasyprint` fails. Edge ships with Windows, so the fallback
needs no installation. The script prints which renderer it used.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

CSS = """
@page { size: Letter; margin: 20mm 18mm;
        @bottom-center { content: counter(page); font-size: 9pt; color: #888; } }
body { font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; font-size: 10.5pt;
       line-height: 1.5; color: #1a1a1a; background: #fff; }
h1 { font-size: 20pt; border-bottom: 2px solid #1f3a93; padding-bottom: 6px; margin: 0 0 10px; }
h2 { font-size: 14.5pt; margin: 24px 0 8px; border-bottom: 1px solid #ddd; padding-bottom: 3px;
     page-break-after: avoid; }
h3 { font-size: 12pt; margin: 18px 0 6px; color: #1f3a93; page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9pt; }
tr { page-break-inside: avoid; }
th { background: #f0f2f7; text-align: left; font-weight: 600; }
th, td { border: 1px solid #ccc; padding: 4px 6px; vertical-align: top; }
code { font-family: "Cascadia Mono", Consolas, monospace; font-size: 9pt; background: #f4f4f6;
       padding: 1px 3px; border-radius: 3px; }
pre { background: #f7f7f9; border: 1px solid #e0e0e4; border-left: 3px solid #1f3a93;
      padding: 8px 10px; font-size: 8.5pt; line-height: 1.4; white-space: pre-wrap;
      word-wrap: break-word; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
blockquote { border-left: 3px solid #ccc; margin: 10px 0; padding: 2px 14px; color: #444; }
a { color: #1f5fbf; text-decoration: none; word-break: break-word; }
"""


def to_html(md_text, title):
    import markdown
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "toc"])
    return ('<!DOCTYPE html><html><head><meta charset="utf-8">'
            f"<title>{title}</title><style>{CSS}</style></head><body>{body}</body></html>")


def via_weasyprint(html, out, base):
    from weasyprint import HTML
    HTML(string=html, base_url=base).write_pdf(out)
    return "weasyprint"


def find_browser():
    for p in [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        shutil.which("msedge") or "", shutil.which("chromium") or "",
        shutil.which("google-chrome") or "",
    ]:
        if p and os.path.exists(p):
            return p
    return None


def via_browser(html, out):
    exe = find_browser()
    if not exe:
        raise RuntimeError("no Edge or Chrome found for the fallback renderer")
    tmp = tempfile.mkdtemp(prefix="md-to-pdf-")
    src = os.path.join(tmp, "page.html")
    with open(src, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    if os.path.exists(out):
        os.remove(out)
    cmd = [exe, "--headless", "--disable-gpu", "--no-pdf-header-footer",
           f"--user-data-dir={os.path.join(tmp, 'profile')}",
           f"--print-to-pdf={os.path.abspath(out)}", "file:///" + src.replace("\\", "/")]
    # Headless browsers sometimes exit before the PDF lands. Retry.
    last = ""
    for attempt in range(3):
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if os.path.exists(out) and os.path.getsize(out) > 0:
            return os.path.basename(exe)
        last = r.stderr[-500:]
        time.sleep(1.5)
    shutil.rmtree(tmp, ignore_errors=True)
    raise RuntimeError(f"{os.path.basename(exe)} wrote no PDF after 3 attempts\n{last}")


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    src, out = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        md = f.read()
    m = re.search(r"^#\s+(.+)$", md, re.M)
    title = m.group(1).strip() if m else os.path.basename(src)
    html = to_html(md, title)
    errors = []
    for render in (lambda: via_weasyprint(html, out, os.path.dirname(os.path.abspath(src))),
                   lambda: via_browser(html, out)):
        try:
            used = render()
            print(f"wrote {out} ({used})")
            return 0
        except Exception as e:  # noqa: BLE001 -- try the next renderer
            errors.append(f"{type(e).__name__}: {str(e).splitlines()[0] if str(e) else ''}")
    print("FAILED: " + " | ".join(errors), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
