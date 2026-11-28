#!/usr/bin/env python3
"""Append illustrated sheets 08–16, without rewriting any original sheet.

Requires an art mapping JSON, supplied with the generated illustration atlases:
  python3 scripts/append-illustrated-menu.py --mapping scripts/data/illustrated-menu-extension.json

Mapping shape:
 {"atlases":{"4":{"file":"assets/basilik/dish-atlas-4.webp","columns":3,"rows":4}},
  "art":{"beefsteak":[4,0], ...}}
Optional atlas rowBounds/columnBounds can correct the actual authored grid.
The source WebP pixels are embedded unchanged. Alpha bounds only select SVG ROI.
Use --plan to inspect all pending sheet titles, dishes and required art keys.
"""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/basilik/menu-pages'
SPEC=importlib.util.spec_from_file_location('original_illustrated_builder',ROOT/'scripts/build-illustrated-menu.py')
BASE=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(BASE)
PAGES=[
 ('Ещё горячего','Из казана — к вашему столу',['dish-bc337c76','dish-7cc23e26','dish-155d9542','dish-ea51fc2b']),
 ('Сытный обед','Неспешно. Вкусно. По-домашнему.',['dish-a34c2789','dish-37d72bec','dish-5f2b3fb6','dish-49b31f01']),
 ('Шаверма в лаваше','Хрустящий лаваш, сочная начинка',['dish-45035596','dish-279ef6a8','dish-e9c8b5d5','dish-3975672a','dish-6ecec897']),
 ('Пряные вкусы','Выбирайте свой любимый вкус',['dish-b5de6e82','dish-128aac86','dish-ff521a3f','dish-65d089b4','dish-2c1662b5','dish-bd089093']),
 ('Горячий перекус','Когда хочется чего-нибудь сытного',['dish-b43c4a7d','dish-45311173','dish-733baf12','dish-04aabc9d','dish-e9b70daf']),
 ('Курица и гарниры','Простые сочетания на каждый день',['dish-4c606af4','dish-3a2f2c6f','dish-dacfa34c','dish-14163704','dish-cb1d82c2','dish-d519c512']),
 ('Овощи к столу','Свежий салат и любимый гарнир',['dish-9ed34933','dish-a0ff0713','dish-48aed1f0','dish-8b416a9d','dish-fd1bce16','dish-6504efb6']),
 ('Прохлада','К горячему обеду — холодный напиток',['dish-f87f7c64','dish-63be8fcf','dish-4e3f5a20','dish-f2204b67','dish-f6134623']),
 ('Кувшин на стол','Поделитесь прохладой с близкими',['dish-85539fcf','dish-875c60c8','dish-2f230a05','dish-1d097760']),
]
ART={
 'dish-bc337c76':'beefsteak','dish-7cc23e26':'goulash','dish-155d9542':'beef-stew','dish-ea51fc2b':'kurutob',
 'dish-a34c2789':'solyanka','dish-37d72bec':'dumplings-cream','dish-5f2b3fb6':'fried-egg','dish-49b31f01':'lavash',
 'dish-45035596':'shawarma-wrap','dish-279ef6a8':'shawarma-wrap','dish-e9c8b5d5':'shawarma-wrap','dish-3975672a':'shawarma-wrap','dish-6ecec897':'shawarma-cheese',
 'dish-b5de6e82':'shawarma-wrap','dish-128aac86':'shawarma-wrap','dish-ff521a3f':'shawarma-wrap','dish-65d089b4':'shawarma-pita','dish-2c1662b5':'shawarma-plate','dish-bd089093':'shawarma-plate',
 'dish-b43c4a7d':'shawarma-beef-plate','dish-45311173':'hotdog-wrap','dish-733baf12':'hotdog-bbq','dish-04aabc9d':'hotdog-potatoes','dish-e9b70daf':'jalapeno',
 'dish-4c606af4':'grilled-breast','dish-3a2f2c6f':'cheese-breast','dish-dacfa34c':'chicken-cutlet','dish-14163704':'mushroom-thigh','dish-cb1d82c2':'buckwheat','dish-d519c512':'rice',
 'dish-9ed34933':'greek-salad','dish-a0ff0713':'korean-carrot','dish-48aed1f0':'olivier','dish-8b416a9d':'caesar','dish-fd1bce16':'baked-potatoes','dish-6504efb6':'pasta',
 'dish-f87f7c64':'cola','dish-63be8fcf':'apple-cola','dish-4e3f5a20':'cola','dish-f2204b67':'water','dish-f6134623':'cola',
 'dish-85539fcf':'dried-fruit-compote','dish-875c60c8':'saperavi-lemonade','dish-2f230a05':'juice','dish-1d097760':'juice-glass',
}
CAPTIONS={
 'dish-bc337c76':'Сочное мясо и овощи к сытному обеду.', 'dish-7cc23e26':'Нежная говядина в ароматной подливе.',
 'dish-155d9542':'Говядина с картофелем и овощами.', 'dish-ea51fc2b':'Слоёная лепёшка, овощи и кисломолочный соус.',
 'dish-a34c2789':'Густой мясной суп с ярким вкусом.', 'dish-37d72bec':'Мясные пельмени со сметаной и зеленью.',
 'dish-5f2b3fb6':'Жареное яйцо к любимому гарниру.', 'dish-49b31f01':'Тонкий лаваш из горячего тандыра.',
 'dish-45035596':'Сочная начинка в тонком лаваше.', 'dish-279ef6a8':'Курица, овощи и соус в лаваше.',
 'dish-e9c8b5d5':'Говядина, свежие овощи и соус.', 'dish-3975672a':'Двойная порция любимой начинки.',
 'dish-6ecec897':'Сочная начинка с щедрой порцией сыра.', 'dish-b5de6e82':'Мясо, овощи и соус барбекю.',
 'dish-128aac86':'Для любителей пряного вкуса.', 'dish-ff521a3f':'Ароматная начинка в тонком лаваше.',
 'dish-65d089b4':'Курица и свежие овощи в мягкой пите.', 'dish-2c1662b5':'Сытная подача на тарелке.',
 'dish-bd089093':'Курица с овощами, гарниром и соусом.', 'dish-b43c4a7d':'Говядина с гарниром и свежими овощами.',
 'dish-45311173':'Горячая сосиска и соус в лаваше.', 'dish-733baf12':'Хот-дог с соусом барбекю.',
 'dish-04aabc9d':'Картофель, хот-дог и любимый соус.', 'dish-e9b70daf':'Острый перец к мясу и шаверме.',
 'dish-4c606af4':'Нежное куриное филе с гриля.', 'dish-3a2f2c6f':'Куриное филе под румяным сыром.',
 'dish-dacfa34c':'Сочная домашняя куриная котлета.', 'dish-14163704':'Куриное бедро с грибами и сыром.',
 'dish-cb1d82c2':'Рассыпчатая гречка к горячим блюдам.', 'dish-d519c512':'Нежный рис к мясу и овощам.',
 'dish-9ed34933':'Овощи, мягкий сыр и маслины.', 'dish-a0ff0713':'Пряная морковь по-корейски.',
 'dish-48aed1f0':'Любимый салат к общему столу.', 'dish-8b416a9d':'Хрустящий салат с курицей и соусом.',
 'dish-fd1bce16':'Румяный картофель с золотистой корочкой.', 'dish-6504efb6':'Простой гарнир к любимому горячему.',
 'dish-f87f7c64':'Классическая кола к горячему обеду.', 'dish-63be8fcf':'Освежающая кола с яблочным вкусом.',
 'dish-4e3f5a20':'Холодный газированный напиток.', 'dish-f2204b67':'Газированная или негазированная.',
 'dish-f6134623':'Классический газированный напиток.', 'dish-85539fcf':'Домашний компот из сухофруктов.',
 'dish-875c60c8':'Виноградный лимонад к любимым блюдам.', 'dish-2f230a05':'Фруктовый сок мультифрукт.',
 'dish-1d097760':'Любимый вкус сока на выбор.',
}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mapping',type=Path);parser.add_argument('--plan',action='store_true');args=parser.parse_args()
    source=(ROOT/'menu-data.js').read_text();data=json.loads(source.split('window.TEBURASI_MENU = ',1)[1].strip().rstrip(';'));items={i['id']:i for i in data['items']}
    old_ids={i for p in data['pages'][:7] for i in p['itemIds']};new_ids=set(items)-old_ids
    planned=[i for _,_,ids in PAGES for i in ids]
    assert len(planned)==45 and len(set(planned))==45 and set(planned)==new_ids
    if args.plan:
        for n,(title,note,ids) in enumerate(PAGES,8):print(n,title,[(items[i]['name'],ART[i]) for i in ids])
        print('New art types:',len(set(ART.values())));return
    if not args.mapping:raise SystemExit('--mapping is required (or use --plan)')
    mapping=json.loads(args.mapping.read_text())
    missing=set(ART.values())-set(mapping['art'])
    if missing:raise SystemExit('Missing art mapping: '+', '.join(sorted(missing)))
    protected={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.stem in [f'{n:02}' for n in range(1,8)]}
    atlases={int(n):BASE.embedded_atlas(ROOT/a['file']) for n,a in mapping['atlases'].items()}
    BASE.ATLAS_MAP={i:tuple(mapping['art'][art]) for i,art in ART.items()}
    BASE.DEMO_PRICES={i:items[i]['price'] for i in planned}
    BASE.CAPTIONS.update(CAPTIONS)
    def roi(atlas,cell):
        spec=mapping['atlases'][str(atlas)]
        with Image.open(ROOT/spec['file']) as im:
            cols,rows=spec['columns'],spec['rows']
            xs=spec.get('columnBounds',[round(n*im.width/cols) for n in range(cols+1)])
            ys=spec.get('rowBounds',[round(n*im.height/rows) for n in range(rows+1)])
            left,right=xs[cell%cols:cell%cols+2];top,bottom=ys[cell//cols:cell//cols+2]
            bbox=im.convert('RGBA').getchannel('A').crop((left,top,right,bottom)).point(lambda v:255 if v>80 else 0).getbbox()
            if not bbox:return left,top,right-left,bottom-top
            x0,y0,x1,y1=bbox;pad=round(max(x1-x0,y1-y0)*.03)
            x0=max(left,left+x0-pad);y0=max(top,top+y0-pad);x1=min(right,left+x1+pad);y1=min(bottom,top+y1+pad)
            return x0,y0,x1-x0,y1-y0
    BASE.cell_roi=roi
    # Extend only the in-memory renderer to use the six-slot layout for five
    # dishes. No original builder, page, or artwork is written or modified.
    render_source=(ROOT/'scripts/build-illustrated-menu.py').read_text()
    render_source=render_source[render_source.index('def render_page('):render_source.index('\ndef main():')]
    render_source=render_source.replace('if count==6:', 'if count in (5,6):')
    exec(render_source,BASE.__dict__)
    metadata=[]
    for number,(title,note,ids) in enumerate(PAGES,8):
        svg=BASE.render_page(number,title,note,ids,items,atlases)
        path=OUT/f'{number:02}.svg';path.write_text(svg)
        metadata.append({'src':str(path.relative_to(ROOT)),'title':title,'width':480,'height':853,'itemIds':ids,'actualPrices':{i:items[i]['price'] for i in ids},'priceSource':'shar-shara.ru','fullSrc':str(path.relative_to(ROOT))})
        print(path.relative_to(ROOT))
    (OUT/'extension-manifest.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==checksum for p,checksum in protected.items())
    print('Original seven sheets preserved byte for byte.')

if __name__=='__main__':main()
