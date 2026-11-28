#!/usr/bin/env python3
"""Build self-contained illustrated menu SVGs from two 3 × 4 dish atlases and one 2 × 2 atlas and one 2 × 2 atlas.

Run from any directory: python3 scripts/build-illustrated-menu.py
Pillow and fonttools are needed only for rebuilding; SVGs require no runtime dependencies.
"""
from __future__ import annotations
import base64
import io
import json
from pathlib import Path
from html import escape
from PIL import Image, ImageFont
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
OUT = ASSETS / 'basilik' / 'menu-pages'
INK = '#302e24'
BURGUNDY = '#6b2438'
GREEN = '#315b37'
PAPER = '#eee5d1'

# Atlas mapping is deliberately separate from page composition. Cell numbers start
# at zero and read left to right, top to bottom across three columns and four rows.
ATLAS_MAP = {
    'plov': (1,0), 'manty': (1,1), 'dish-e6ed66d0': (1,2),
    'dish-a7bd5ba6': (1,3), 'dish-2650e5c9': (1,4), 'dish-e7bbc24c': (1,5),
    'kazan-kebab': (1,6), 'dish-e05f0b9e': (1,7), 'dish-cc643972': (1,8),
    'shurpa': (1,9), 'dish-555c7d64': (1,9), 'dish-0a018072': (1,10), 'mastava': (1,11),
    'lagman': (2,0), 'lyulya': (2,1), 'shashlik': (2,2), 'dish-394f54db': (2,3),
    'dish-e505ba1f': (2,4), 'lepeshka': (2,5), 'samsa': (2,6),
    'dish-0dc8d7ff': (2,7), 'dish-39b4a9e2': (2,8), 'dish-7e17e642': (2,9),
    'shakarop': (2,10), 'dish-d4b9d7e9': (2,11), 'dish-3f6375dc': (3,0),
    'dish-9d78cd68': (3,1), 'dish-080d3ddd': (3,2), 'dish-4c724774': (3,3),
}

PAGES = [
    ('Дастархан', 'Начнём с самого любимого', ['plov', 'manty', 'dish-a7bd5ba6', 'dish-e6ed66d0']),
    ('Из казана', 'Томится не спеша. Подаётся от души.', ['kazan-kebab', 'dish-e05f0b9e', 'dish-2650e5c9', 'dish-e7bbc24c']),
    ('Горячие супы', 'По ложечке — и становится теплее', ['dish-cc643972', 'shurpa', 'dish-555c7d64', 'dish-0a018072', 'mastava', 'lagman']),
    ('С дымком', 'Огонь, специи и хорошая компания', ['lyulya', 'shashlik', 'dish-394f54db', 'dish-e505ba1f']),
    ('Из тандыра', 'Ломайте руками. Делитесь с близкими.', ['samsa', 'lepeshka']),
    ('Свежесть к столу', 'Зелень, овощи и немного хруста', ['dish-0dc8d7ff', 'dish-39b4a9e2', 'dish-7e17e642', 'shakarop', 'dish-d4b9d7e9', 'dish-3f6375dc']),
    ('К чаю', 'У хорошего вечера — сладкое продолжение', ['dish-9d78cd68', 'dish-080d3ddd', 'dish-4c724774']),
]

# Concise editorial captions keep the density and rhythm of the original drawn
# sheets. Full ingredient descriptions remain available in the live catalogue.
CAPTIONS = {
    'plov': 'Рис, мясо, морковь и ароматные специи.',
    'manty': 'Сочная мясная начинка в тонком тесте.',
    'dish-a7bd5ba6': 'Домашняя лапша, говядина, овощи и яйцо.',
    'dish-e6ed66d0': 'Баранина с картофелем и овощами из казана.',
    'kazan-kebab': 'Баранина с золотистым картофелем.',
    'dish-e05f0b9e': 'Говядина, картофель, лук и специи.',
    'dish-2650e5c9': 'Румяная баранина с восточными специями.',
    'dish-e7bbc24c': 'Сочная говядина, обжаренная с луком.',
    'dish-cc643972': 'Баранина и овощи в душистом бульоне.',
    'shurpa': 'Наваристый бульон, баранина и зелень.',
    'dish-555c7d64': 'Говядина, свежие овощи и специи.',
    'dish-0a018072': 'Домашние пельмени в горячем бульоне.',
    'mastava': 'Густой рисовый суп с мясом и овощами.',
    'lagman': 'Домашняя лапша, мясо и пряный бульон.',
    'lyulya': 'Баранина, пряности и огонь мангала.',
    'shashlik': 'Нежная баранина, специи и аромат углей.',
    'dish-394f54db': 'Сочная говядина с луком и специями.',
    'dish-e505ba1f': 'Курица в маринаде из трав и специй.',
    'samsa': 'Хрустящее тесто и сочная мясная начинка.',
    'lepeshka': 'Золотистая корочка. Тёплая, прямо из печи.',
    'dish-0dc8d7ff': 'Свежие овощи и молодая зелень.',
    'dish-39b4a9e2': 'Вкус лета — и ничего лишнего.',
    'dish-7e17e642': 'Нежный салат с сочной курицей.',
    'shakarop': 'Помидоры, лук и кисломолочный соус.',
    'dish-d4b9d7e9': 'Густая кисломолочная чака к овощам.',
    'dish-3f6375dc': 'Хрустящие соленья с душистыми травами.',
    'dish-9d78cd68': 'Сладости к неспешному чаепитию.',
    'dish-080d3ddd': 'Фруктовый, домашний, освежающий.',
    'dish-4c724774': 'Освежающий лимонад к любимым блюдам.',
}
DEMO_PRICES = dict(zip([item for _, _, items in PAGES for item in items], [590,490,560,1250,690,650,1190,1090,450,420,410,390,390,460,390,590,560,420,150,100,290,290,350,290,190,250,290,150,220]))


def embedded_font(filename, characters):
    font = TTFont(ASSETS / filename)
    options = subset.Options()
    sub = subset.Subsetter(options=options)
    sub.populate(text=characters)
    sub.subset(font)
    output = io.BytesIO()
    font.save(output)
    return base64.b64encode(output.getvalue()).decode()


def text(x, y, value, cls, **attrs):
    extra = ' '.join(f'{k.replace("_", "-")}="{escape(str(v))}"' for k, v in attrs.items())
    return f'<text x="{x}" y="{y}" class="{cls}" {extra}>{escape(str(value))}</text>'


def wrap(value, font_name, size, width):
    font = ImageFont.truetype(str(ASSETS / font_name), size)
    result, current = [], ''
    for word in value.split():
        next_line = (current + ' ' + word).strip()
        if current and font.getlength(next_line) > width:
            result.append(current)
            current = word
        else:
            current = next_line
    if current:
        result.append(current)
    return result


def embedded_atlas(path):
    """Embed the complete original atlas without removing or retouching pixels."""
    with Image.open(path) as im:
        width,height=im.size
    mime='image/webp' if path.suffix=='.webp' else 'image/png'
    return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode(),width,height



def cell_roi(atlas, cell):
    """Measure the visible illustration; keep source pixels and embed unchanged.

    A modest alpha threshold ignores nearly invisible compression fringes. Three
    percent breathing room is added, bounded by the authored atlas cell.
    """
    path=ASSETS/'basilik'/f'dish-atlas-{atlas}.webp'
    with Image.open(path) as im:
        cols,rows=(2,2) if atlas==3 else (3,4)
        cw=im.width/cols
        bounds=([0,277,520,778,1024] if atlas==1 else [0,272,517,772,1024]) if atlas in (1,2) else [0,im.height/2,im.height]
        left,top=round((cell%cols)*cw),round(bounds[cell//cols])
        right,bottom=round(left+cw),round(bounds[cell//cols+1])
        alpha=im.convert('RGBA').getchannel('A').crop((left,top,right,bottom))
        bbox=alpha.point(lambda value:255 if value>80 else 0).getbbox()
        if bbox is None:return left,top,right-left,bottom-top
        x0,y0,x1,y1=bbox
        pad=round(max(x1-x0,y1-y0)*.03)
        x0=max(left,left+x0-pad);y0=max(top,top+y0-pad)
        x1=min(right,left+x1+pad);y1=min(bottom,top+y1+pad)
        return x0,y0,x1-x0,y1-y0


def sprig(x, y, scale=1, rotate=0):
    return f'''<g transform="translate({x} {y}) rotate({rotate}) scale({scale})" stroke="{GREEN}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M0 54Q5 25 2 0" fill="none"/><path d="M2 15Q-22 0-19 20Q-14 28 2 22M3 28Q25 7 25 28Q18 38 3 34M2 42Q-20 24-19 43Q-12 52 1 48" fill="#6c8144"/><path d="M-14 16 2 22M20 24 3 34M-13 40 1 48" fill="none" stroke="#d7cf93" stroke-width=".7"/></g>'''


def render_page(number, title, note, ids, items, atlases):
    all_text = title + note + 'ЧАЙХАНА БАЗИЛИК ВЛАДИМИР Цены предварительные ₽ г шт порция' + ''.join(items[x]['name'] + CAPTIONS.get(x,'') + items[x]['portion'] + str(DEMO_PRICES[x]) for x in ids)
    all_text += all_text.upper() + '0123456789.,—–₽'
    fonts = ''.join(f"@font-face{{font-family:{family};src:url(data:font/ttf;base64,{embedded_font(filename, all_text)}) format('truetype');font-weight:{weight};}}" for family,filename,weight in [('Amatic','amatic-bold.ttf',700),('Caveat','caveat.ttf',400),('Manrope','manrope-regular.ttf',400)])
    atlas_defs=''.join(f'<image id="atlas-{n}" href="{atlases[n][0]}" width="{atlases[n][1]}" height="{atlases[n][2]}"/>' for n in sorted({ATLAS_MAP[ident][0] for ident in ids}))
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="853" viewBox="0 0 480 853"><title>{escape(title)} — Чайхана Базилик</title><defs>{atlas_defs}<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".7" numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="linear" slope=".075"/></feComponentTransfer><feBlend in="SourceGraphic" mode="multiply"/></filter></defs><style>{fonts}text{{fill:{INK};}}.brand{{font:10px Manrope;letter-spacing:2px;fill:{GREEN};}}.heading{{font:700 49px Amatic;fill:{BURGUNDY};}}.note{{font:20px Caveat;fill:{GREEN};}}.name{{font:700 25px Amatic;}}.desc{{font:10px Manrope;}}.portion{{font:10px Caveat;fill:{GREEN};}}.price{{font:25px Caveat;fill:{BURGUNDY};}}.footer{{font:9px Manrope;fill:{GREEN};}}</style><rect width="480" height="853" fill="{PAPER}"/><rect width="480" height="853" fill="{PAPER}" filter="url(#grain)"/>
''',text(32,30,'ЧАЙХАНА БАЗИЛИК · ВЛАДИМИР','brand'),text(32,86,title.upper(),'heading'),text(32,115,note,'note'),f'<path d="M32 126Q150 121 282 126" fill="none" stroke="{BURGUNDY}" stroke-width="1.4"/>',sprig(439,61,.62,20)]
    count=len(ids)
    if count==6:
        positions=[(28+228*(n%2),142+210*(n//2),198,112) for n in range(count)]
    elif count==4:
        positions=[(28+228*(n%2),156+321*(n//2)+(9 if n%2 else 0),198,170) for n in range(count)]
    elif count==2:
        positions=[(65,151,350,235),(65,471,350,220)]
    else:
        positions=[(55,150,370,230),(28,494,198,150),(256,494,198,150)]
    for n,(ident,pos) in enumerate(zip(ids,positions)):
        x,y,w,h=pos;item=items[ident]
        atlas,cell=ATLAS_MAP[ident]
        _,aw,ah=atlases[atlas]
        vx,vy,cw,ch=cell_roi(atlas,cell)
        parts.append(f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{vx} {vy} {cw} {ch}" preserveAspectRatio="xMidYMax meet" overflow="hidden"><defs><clipPath id="cell-{ident}" clipPathUnits="userSpaceOnUse"><rect x="{vx}" y="{vy}" width="{cw}" height="{ch}"/></clipPath></defs><g clip-path="url(#cell-{ident})"><use href="#atlas-{atlas}"/></g></svg>')
        ty=y+h+20
        names=wrap(item['name'].replace('Казан-Кебаб','Казан-кебаб').upper(), 'amatic-bold.ttf',25,w-6)
        for line in names:
            parts.append(text(x+5,ty,line.upper(),'name'));ty+=25
        for line in wrap(CAPTIONS.get(ident,''),'manrope-regular.ttf',10,w-10)[:2]:
            parts.append(text(x+5,ty-9,line,'desc'));ty+=14
        parts.append(text(x+5,ty+3,item['portion'],'portion'))
        parts.append(text(x+w-6,ty+7,str(DEMO_PRICES[ident])+' ₽','price',text_anchor='end'))
    parts.extend([sprig(35,773,.48,-34),f'<path d="M77 811Q240 807 440 812" fill="none" stroke="{GREEN}" opacity=".4"/>',text(78,829,'Цены предварительные','footer'),text(440,830,str(number).zfill(2),'note',text_anchor='end'),'</svg>'])
    return ''.join(parts)


def main():
    raw=(ROOT/'menu-data.js').read_text()
    data=json.loads(raw.split('window.TEBURASI_MENU = ',1)[1].strip().rstrip(';'))
    items={item['id']:item for item in data['items']}
    expected={item for _,_,ids in PAGES for item in ids}
    missing=expected-set(ATLAS_MAP)
    if missing:raise SystemExit('Atlas mapping missing: '+', '.join(sorted(missing)))
    atlases={n:embedded_atlas(ASSETS/'basilik'/f'dish-atlas-{n}.webp') for n in (1,2,3)}
    OUT.mkdir(parents=True,exist_ok=True)
    for i,(title,note,ids) in enumerate(PAGES,1):
        target=OUT/f'{i:02}.svg';target.write_text(render_page(i,title,note,ids,items,atlases))
        print(target.relative_to(ROOT),target.stat().st_size)
    metadata=[{'src':str((OUT/f'{n:02}.svg').relative_to(ROOT)),'title':title,'width':480,'height':853,'itemIds':ids,'demoPrices':{i:DEMO_PRICES[i] for i in ids}} for n,(title,note,ids) in enumerate(PAGES,1)]
    (OUT/'manifest.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
