#!/usr/bin/env python3
"""Build the minimal, offline PDF helper archive for ordinary ChatGPT uploads."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parent.parent
files = ["SKILL.md", "CHATGPT_START_HERE.md", "chatgpt/PDF_DELIVERY.md",
         "chatgpt/export_pdf.py", "assets/fonts/NotoSansSC-Regular.ttf",
         "assets/fonts/OFL.txt", "LICENSE"]
for name in files:
    if not (root / name).is_file():
        raise SystemExit(f"Missing bundle input: {name}")
output = root / "chatgpt/paper-logic-simplifier-chatgpt.zip"
with ZipFile(output, "w", ZIP_DEFLATED) as archive:
    for name in files:
        archive.write(root / name, f"paper-logic-simplifier/{name}")
print(f"ChatGPT upload bundle: {output} ({output.stat().st_size:,} bytes)")
