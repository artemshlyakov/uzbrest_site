#!/usr/bin/env python3
"""Export compact menu previews; retain SVGs for the full-size gallery.
Rebuild: python3 scripts/build-illustrated-menu.py && python3 scripts/export-illustrated-menu.py
Requires Pillow, fonttools (builder) and Playwright with Chromium.
"""
import argparse
import base64
import io
import json
import shutil
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'assets/basilik/menu-pages/manifest.json'
parser=argparse.ArgumentParser()
parser.add_argument('--append',action='store_true',help='Export only the extension pages; retain approved originals')
args=parser.parse_args()
existing=json.loads(MANIFEST.read_text())
pages=json.loads((MANIFEST.parent/'extension-manifest.json').read_text()) if args.append else existing
with sync_playwright() as p:
    executable=shutil.which('chromium') or shutil.which('google-chrome')
    options={'headless':True,'args':['--no-sandbox']}
    if executable: options['executable_path']=executable
    browser=p.chromium.launch(**options)
    page=browser.new_page(viewport={'width':960,'height':1706},device_scale_factor=1)
    for item in pages:
        source=ROOT/item.get('fullSrc',item['src'])
        encoded=base64.b64encode(source.read_bytes()).decode()
        page.set_content('<style>html,body{margin:0}img{display:block;width:960px;height:1706px}</style><img src="data:image/svg+xml;base64,'+encoded+'">')
        page.wait_for_function('document.querySelector("img").complete && document.querySelector("img").naturalWidth > 0')
        png=page.screenshot()
        target=source.with_suffix('.webp')
        Image.open(io.BytesIO(png)).convert('RGB').save(target,quality=90,method=6)
        item['src']=str(target.relative_to(ROOT))
        item['fullSrc']=str(source.relative_to(ROOT))
        print(item['src'],target.stat().st_size)
    browser.close()
if args.append:
    extension_keys={Path(item['fullSrc']).stem for item in pages}
    pages=[item for item in existing if Path(item.get('fullSrc',item['src'])).stem not in extension_keys]+pages
MANIFEST.write_text(json.dumps(pages,ensure_ascii=False,indent=2)+'\n')
raw=(ROOT/'menu-data.js').read_text()
data=json.loads(raw[raw.index('{'):raw.rindex('}')+1])
data['pages']=pages
data['archive']=False
(ROOT/'menu-data.js').write_text('// Полное меню Shar-Shara. Первые семь рисованных листов сохранены; новые используют цены источника.\nwindow.TEBURASI_MENU = '+json.dumps(data,ensure_ascii=False,indent=2)+';\n')
