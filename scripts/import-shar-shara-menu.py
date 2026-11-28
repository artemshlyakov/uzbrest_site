#!/usr/bin/env python3
"""Import the complete public Shar-Shara branch menus, preserving drawn pages.

python3 scripts/import-shar-shara-menu.py             # refresh public source + import
python3 scripts/import-shar-shara-menu.py --snapshot  # rebuild from saved snapshot

Uses Pillow to optimise newly downloaded photos. Existing photo crops and stable
catalogue IDs are preserved. Source prices vary by branch: the default is the
Pyatiletok branch, then Kollontay, then Cafe Kudrovo, then Mangal-Kebab. Every
source occurrence with its exact prices and portions remains in item.source.
"""
import argparse
import concurrent.futures
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import re
import urllib.request
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SNAPSHOT=ROOT/'scripts/data/shar-shara-menu.json'
BASE='https://api.shar-shara.ru/api'
PRIORITY=['seed-branch-center','seed-branch-north','seed-branch-mangal','seed-branch-kudrovo']
SPECIAL={'9c611de3':'plov','17987958':'manty','f0ad3b13':'kazan-kebab','502d20bf':'shurpa','c05e54c0':'mastava','82e17db7':'lagman','bc0cb18b':'lyulya','49078e1a':'shashlik','090db844':'lepeshka','342c9718':'samsa','a8cfeb76':'shakarop'}
ORDER=['Горячие блюда','Супы','Мангал','Шаверма','Котлеты','Гарниры','Выпечка','Салаты','Соусы','Десерты','Напитки']


def get(path):
    with urllib.request.urlopen(BASE+path,timeout=45) as response:return json.load(response)


def fetch_snapshot():
    config=get('/public/restaurants/shar-shara')
    branches=get('/public/restaurants/shar-shara/branches')
    def menu(branch):return branch['id'],get('/restaurants/'+config['id']+'/menu?branch_id='+branch['id'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:menus=dict(pool.map(menu,branches))
    snapshot={'source':'https://shar-shara.ru/','apiBase':BASE,'fetchedAt':datetime.now(timezone.utc).isoformat(),'restaurant':{'id':config['id'],'slug':config['slug'],'name':config['name']},'branches':branches,'menus':menus}
    SNAPSHOT.parent.mkdir(exist_ok=True,parents=True)
    SNAPSHOT.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n')
    return snapshot


def normal_name(value):return re.sub(r'\s+',' ',value.lower().replace('ё','е')).strip()


def group_items(snapshot):
    occurrences=[]
    for branch_id,groups in snapshot['menus'].items():
        for category in groups:
            for dish in category['dishes']:occurrences.append({'branchId':branch_id,'category':category['name'],**dish})
    # Union by source dish ID or exactly matching names. Similar but different
    # products (e.g. chicken in lavash vs generic lavash) deliberately stay separate.
    parent=list(range(len(occurrences)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    seen_ids={};seen_names={}
    for i,item in enumerate(occurrences):
        for key,seen in [(item['id'],seen_ids),(normal_name(item['name']),seen_names)]:
            if key in seen:parent[find(i)]=find(seen[key])
            else:seen[key]=i
    groups={}
    for i,item in enumerate(occurrences):groups.setdefault(find(i),[]).append(item)
    return list(groups.values())


def source_variants(dish):
    return [{'portion':v.get('label',''),'price':float(v['price']) if '.' in str(v['price']) else int(v['price'])} for v in dish.get('variants',[])]


def save_photo(url,path):
    with urllib.request.urlopen(url,timeout=60) as response:body=response.read()
    im=Image.open(io.BytesIO(body)).convert('RGBA');im.thumbnail((900,900))
    path.parent.mkdir(exist_ok=True,parents=True);im.save(path,'WEBP',quality=88)
    return im.size


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--snapshot',action='store_true');args=parser.parse_args()
    snapshot=json.loads(SNAPSHOT.read_text()) if args.snapshot else fetch_snapshot()
    path=ROOT/'menu-data.js';text=path.read_text();prefix,body=text.split('window.TEBURASI_MENU = ',1);data=json.loads(body.strip().rstrip(';'))
    pages_before=json.dumps(data['pages'],ensure_ascii=False,sort_keys=True)
    old={item['id']:item for item in data['items']}
    old_by_source={source_id:item for item in old.values() for source_id in item.get('source',{}).get('dishIds',[])}
    branch_names={b['id']:b['name'] for b in snapshot['branches']}
    items=[];photo_tasks=[];differences=[];no_photo=[]
    for group in group_items(snapshot):
        group.sort(key=lambda d:PRIORITY.index(d['branchId']) if d['branchId'] in PRIORITY else 99)
        default=group[0];source_ids=list(dict.fromkeys(d['id'] for d in group))
        old_item=next((old_by_source[i] for i in source_ids if i in old_by_source),None)
        ident=next((SPECIAL[i[:8]] for i in source_ids if i[:8] in SPECIAL),None) or 'dish-'+source_ids[0][:8]
        old_item=old_item or old.get(ident)
        if old_item:ident=old_item['id']
        name=old_item['name'] if old_item else default['name']
        category=old_item['category'] if old_item else default['category']
        if category=='Шашлык' or name.lower().startswith(('шашлык','люля')):category='Мангал'
        variants=source_variants(default)
        primary=variants[0] if variants else {'portion':'','price':None}
        # Retain every distinct serving size; current default-branch prices win
        # where the same serving has different branch prices.
        options=list(variants)
        for d in group:
            for variant in source_variants(d):
                if not any(normal_name(v['portion']).replace(' ','')==normal_name(variant['portion']).replace(' ','') for v in options):options.append(variant)
        item={'id':ident,'name':name,'category':category,'description':default.get('description') or default.get('ingredients') or '', 'price':primary['price'],'portion':primary['portion'],'variants':options[1:],'food':category!='Напитки'}
        if old_item and 'photo' in old_item:item['photo']=old_item['photo']
        else:
            url=next((d.get('photoUrl') for d in group if d.get('photoUrl')),None)
            if url:
                photo_path=ROOT/'assets/menu-food'/f'{ident}.webp'
                item['photo']={'src':str(photo_path.relative_to(ROOT))}
                photo_tasks.append((item,url,photo_path))
            else:no_photo.append(name)
        branch_menus=[{'branchId':d['branchId'],'branchName':branch_names[d['branchId']],'dishId':d['id'],'name':d['name'],'category':d['category'],'description':d.get('description') or '', 'ingredients':d.get('ingredients') or '', 'photoUrl':d.get('photoUrl'),'variants':source_variants(d)} for d in group]
        item['source']={'site':snapshot['source'],'fetchedAt':snapshot['fetchedAt'],'dishIds':source_ids,'defaultBranchId':default['branchId'],'aliases':list(dict.fromkeys(d['name'] for d in group)),'branchMenus':branch_menus}
        prices={tuple((v['portion'],v['price']) for v in source_variants(d)) for d in group}
        if len(prices)>1:differences.append(name)
        items.append(item)
    def photo(task):
        item,url,path=task
        if path.exists():
            with Image.open(path) as im:size=im.size
        else:size=save_photo(url,path)
        item['photo'].update(width=size[0],height=size[1])
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(photo,photo_tasks))
    old_order={ident:i for i,ident in enumerate(old)}
    items.sort(key=lambda item:(ORDER.index(item['category']) if item['category'] in ORDER else 99,old_order.get(item['id'],999),item['name']))
    data['items']=items;data['foodCategories']=[category for category in ORDER if category!='Напитки' and any(item['category']==category for item in items)]
    assert json.dumps(data['pages'],ensure_ascii=False,sort_keys=True)==pages_before
    assert set(old).issubset({item['id'] for item in items})
    assert all(item['price'] is not None for item in items)
    assert all((ROOT/item['photo']['src']).is_file() for item in items if 'photo' in item)
    path.write_text(prefix+'window.TEBURASI_MENU = '+json.dumps(data,ensure_ascii=False,indent=2)+';\n')
    print('Unique catalogue items:',len(items),'food:',sum(item['food'] for item in items),'drinks:',sum(not item['food'] for item in items))
    print('Added:',len(set(item['id'] for item in items)-set(old)))
    print('Different branch variants/prices:',len(differences),differences)
    print('Source has no photo:',no_photo)
    for b in snapshot['branches']:print(b['name'],sum(len(g['dishes']) for g in snapshot['menus'][b['id']]))

if __name__=='__main__':main()
