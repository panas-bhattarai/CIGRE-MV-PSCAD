"""Render README.md (the paper) to docs/paper.html and docs/paper.pdf.

HTML: python-markdown with tables, toc ids and fenced code; every figure image is
embedded as a base64 data URI so the file is self-contained. PDF: headless Microsoft
Edge (or Chrome) printing that HTML to A4. Usage: python scripts/make_paper.py
"""
import os, re, sys, base64, subprocess, shutil
import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SRC = os.path.join(ROOT, "README.md")
HTML = os.path.join(ROOT, "docs", "paper.html")
PDF = os.path.join(ROOT, "docs", "paper.pdf")

STYLE = """<!doctype html><html><head><meta charset='utf-8'><title>CIGRE-MV-PSCAD</title><style>
body{font-family:Georgia,'Times New Roman',serif;font-size:11pt;line-height:1.45;max-width:190mm;margin:20mm auto;color:#111}
h1{font-size:18pt;line-height:1.25} h2{font-size:14pt;margin-top:1.6em;border-bottom:1px solid #ccc;padding-bottom:2px} h3{font-size:12pt}
table{border-collapse:collapse;font-size:9.5pt;margin:0.6em 0} th,td{border:1px solid #bbb;padding:3px 6px;vertical-align:top} th{background:#f2f2f2}
figure{margin:1em 0;text-align:center;page-break-inside:avoid} figure img{max-width:100%;height:auto}
figcaption{font-size:9.5pt;color:#333;text-align:left;margin-top:4px}
code{font-family:Consolas,monospace;font-size:9.5pt;background:#f4f4f4;padding:1px 3px} pre{background:#f4f4f4;padding:8px;font-size:9.5pt}
p{text-align:justify} @page{size:A4;margin:18mm}
h1{text-align:center} table.byline{margin:0.8em auto;font-size:11pt} table.byline td{border:none;padding:0 2.5em;text-align:center} p.meta{text-align:center}
</style></head><body>"""

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def embed(m):
    alt, src = m.group(1), m.group(2)
    path = os.path.join(ROOT, src)
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return '<figure><img src="data:image/png;base64,%s" alt="%s"><figcaption>%s</figcaption></figure>' % (data, alt, alt)


def main():
    md = open(SRC, encoding="utf-8").read()
    body = markdown.markdown(md, extensions=["tables", "toc", "fenced_code"])
    body = re.sub(r'<p><img alt="([^"]*)" src="([^"]+)" /></p>', embed, body)
    open(HTML, "w", encoding="utf-8", newline="\n").write(STYLE + body + "</body></html>")
    print("wrote", HTML, "(%.1f MB)" % (os.path.getsize(HTML) / 1e6))

    exe = next((b for b in BROWSERS if os.path.exists(b)), shutil.which("msedge") or shutil.which("chrome"))
    if not exe:
        sys.exit("no Edge/Chrome found for PDF export; open docs/paper.html and print to PDF manually")
    url = "file:///" + HTML.replace("\\", "/")
    import tempfile
    # a private profile keeps the export independent of any running browser and of its page cache
    prof = os.path.join(tempfile.gettempdir(), "cigre_mv_pscad_paper_profile")
    if os.path.exists(PDF):
        os.remove(PDF)
    subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-first-run", "--user-data-dir=" + prof,
                    "--no-pdf-header-footer", "--print-to-pdf=" + PDF, url], check=True, timeout=180)
    if not os.path.exists(PDF):
        sys.exit("browser exited without writing the PDF")
    print("wrote", PDF, "(%.1f MB)" % (os.path.getsize(PDF) / 1e6))


if __name__ == "__main__":
    main()
