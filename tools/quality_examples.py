"""Original editable study recipes. Frozen baseline creation is explicit and one-shot."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from pixelart import render


def rect(x, y, w, h, c):
    return dict(op='rect', x=x, y=y, w=w, h=h, color=c)


def poly(points, c):
    return dict(op='polygon', points=points, color=c)


def line(points, c):
    return dict(op='line', points=points, color=c)


def dots(points, c):
    return dict(op='points', points=points, color=c)


def draw(w, h, ops, bg=None, **extra):
    return dict(version=1, kind='draw', size=[w, h], background=bg, operations=ops, **extra)


def atlas(cells, columns=None):
    return dict(version=1, kind='atlas', columns=columns or len(cells),
                cells=[dict(name=n, spec=s) for n, s in cells])


def arrow(direction, improved=False):
    pts = [[2, 5], [6, 5], [6, 2], [10, 6], [6, 9], [6, 7], [2, 7]]
    transform = dict(right=lambda x,y:(x,y), left=lambda x,y:(11-x,y),
                     down=lambda x,y:(y,x), up=lambda x,y:(y,11-x))[direction]
    pts = [list(transform(x,y)) for x,y in pts]
    return draw(12, 12, [poly(pts, 'E9D8A6')])


def function_icon(name):
    ink = 'D8E3ED'
    ops = {
        'add': [rect(7,3,2,10,ink), rect(3,7,10,2,ink)],
        'remove': [rect(3,7,10,2,ink)],
        'filter': [poly([[3,3],[12,3],[9,7],[9,12],[6,13],[6,7]],ink)],
        'refresh': [line([[11,5],[9,3],[5,3],[3,5],[3,10],[5,12],[10,12],[12,10]],ink),
                    poly([[10,3],[13,3],[13,7],[9,7]],ink)],
        'transfer': [rect(3,5,8,2,ink),poly([[10,3],[13,6],[10,8]],ink),
                     rect(5,10,8,2,ink),poly([[5,8],[2,11],[5,13]],ink)],
        'lock': [rect(4,7,8,6,ink),line([[5,7],[5,4],[6,3],[9,3],[10,4],[10,7]],ink),
                 rect(7,9,2,2,'1D293D')],
    }[name]
    return draw(16,16,ops)


def materials():
    cells=[]
    shape=[[10,5],[21,5],[27,11],[27,21],[21,27],[10,27],[4,21],[4,11]]
    for name, dark, base, light in [('crystal','204953','48B5C4','B9EAE7'),
                                    ('metal','384152','7E91AA','DBE5EF'),
                                    ('stone','484C46','8F9685','C5C7B2')]:
        ops=[poly(shape,dark),poly([[10,7],[20,7],[25,12],[25,20],[20,25],[11,25],[6,20],[6,12]],base),
             rect(10,8,11,4,light),rect(8,12,3,6,light),rect(13,22,9,3,dark)]
        cells.append((name,draw(32,32,ops)))
    return atlas(cells)


STATES=['normal','hover','focus','pressed','selected','disabled']


def ui_buttons():
    cells=[]
    for state in STATES:
        fill={'hover':'335A78','pressed':'182B40','selected':'2E5960','disabled':'3B4552'}.get(state,'263E56')
        edge='7FCECF' if state in ('focus','selected') else '75899A'
        ink='89939D' if state=='disabled' else 'E5ECEE'
        ops=[rect(0,0,32,18,edge),rect(1,1,30,16,fill),
             poly([[12,5],[19,9],[12,13]],ink)]
        if state=='selected': ops += [rect(2,2,2,14,'7FCECF')]
        cells.append((state,draw(32,18,ops)))
    return atlas(cells,3)


def panel():
    return draw(96,64,[rect(0,0,96,64,'718191'),rect(1,1,94,62,'1D293D'),
        rect(5,5,86,9,'35465C'),rect(5,19,28,36,'35465C'),rect(37,19,54,12,'35465C'),
        rect(37,35,54,20,'35465C'),rect(64,44,22,7,'65B6B5'),rect(8,58,80,1,'53647A')])


def mc_small():
    cells=[]
    for name in ('off','on','input','output','both'):
        ops=[dict(op='button',x=0,y=0,w=16,h=16,state='SELECTED' if name=='on' else 'NORMAL')]
        c='85BD72' if name=='on' else '303030'
        if name in ('off','on'):
            ops += [line([[5,5],[5,10],[10,10],[10,5]],c),rect(7,3,2,5,c)]
        else:
            if name in ('input','both'): ops += [poly([[3,6],[7,6],[7,4],[10,8],[7,11],[7,9],[3,9]],'2C4D69')]
            if name in ('output','both'): ops += [poly([[12,6],[9,6],[9,4],[6,8],[9,11],[9,9],[12,9]],'6E3434')]
        cells.append((name,draw(16,16,ops,preset='minecraft')))
    return atlas(cells)


def mc_panel():
    ops=[dict(op='bevel',x=0,y=0,w=96,h=54,tl='FFFFFF',br='555555')]
    for x in (6,26,46): ops += [dict(op='slot',x=x,y=8)]
    ops += [dict(op='button',x=6,y=32,w=38,h=16,state='NORMAL'),
            dict(op='button',x=50,y=32,w=38,h=16,state='HOVER'),
            poly([[22,36],[29,40],[22,44]],'202020'),rect(62,38,13,3,'202020')]
    return draw(96,54,ops,'C6C6C6',preset='minecraft')


def baseline_specs():
    return {
        'directions-12':atlas([(n,arrow(n)) for n in ('right','left','down','up')]),
        'functions-16':atlas([(n,function_icon(n)) for n in ('add','remove','filter','refresh','transfer','lock')],3),
        'ship-32':json.loads((ROOT/'examples/asymmetric-ship-32.json').read_text(encoding='utf-8')),
        'materials-32':materials(), 'ui-states':ui_buttons(), 'ui-panel':panel(),
        'minecraft-states':mc_small(), 'minecraft-panel':mc_panel(),
    }


def refined_function(name):
    ink='D8E3ED'
    replacements={
      'filter':[poly([[3,3],[12,3],[12,5],[9,8],[9,12],[6,13],[6,8],[3,5]],ink)],
      'refresh':[poly([[5,3],[10,3],[12,5],[10,6],[9,5],[6,5],[5,6],[5,9],
                      [6,10],[9,10],[10,9],[10,8],[12,8],[12,10],[10,12],[5,12],[3,10],[3,5]],ink),
                 poly([[9,5],[14,5],[12,7]],ink)],
      'lock':[rect(4,7,8,6,ink),rect(5,4,2,4,ink),rect(9,4,2,4,ink),
              rect(6,3,4,2,ink),rect(7,9,2,2,'1D293D')],
    }
    return draw(16,16,replacements[name]) if name in replacements else function_icon(name)


def refined_ship(wide=False):
    hull=[[5,17],[11,15],[15,10],[27,3],[26,15],[28,20],[21,22],[16,28],[11,24],[8,23]]
    if wide: hull=[[3,18],[11,14],[15,10],[27,3],[26,15],[29,22],[21,22],[16,28],[11,24],[8,23]]
    ops=[poly(hull,'16223D'),
         poly([[8,17],[13,16],[17,10],[25,6],[24,16],[25,19],[19,20],[15,25],[12,22],[10,21]],'218390'),
         poly([[10,17],[17,11],[25,6],[23,15],[17,20],[13,21]],'36CFC9'),
         poly([[15,14],[21,9],[22,10],[21,15],[17,18],[14,17]],'162F4A'),
         poly([[16,14],[20,11],[20,14],[17,16],[15,16]],'DCFFF4'),
         line([[10,18],[13,20],[16,21]],'70E6DA'),
         poly([[19,21],[24,20],[20,23],[17,26]],'2AA9AE'),
         poly([[7,25],[9,27],[6,30],[3,30],[4,27]],'F07852'),
         poly([[7,26],[8,27],[6,29],[4,29]],'F7B955')]
    return draw(32,32,ops)


def refined_materials():
    shape=[[10,5],[21,5],[27,11],[27,21],[21,27],[10,27],[4,21],[4,11]]
    crystal=[poly(shape,'173A51'),poly([[11,7],[20,7],[25,12],[25,20],[20,25],[11,25],[6,20],[6,12]],'2298AE'),
      poly([[11,7],[20,7],[15,14],[6,12]],'9DEEE3'),poly([[6,12],[15,14],[11,25],[6,20]],'49C6CF'),
      poly([[20,7],[25,12],[15,14]],'DBFFF0'),poly([[15,14],[25,12],[25,20],[20,25]],'20758F'),
      poly([[15,14],[20,25],[11,25]],'2EADC2'),line([[10,10],[16,9]],'DBFFF0')]
    metal=[poly(shape,'28364D'),poly([[11,7],[20,7],[25,12],[25,20],[20,25],[11,25],[6,20],[6,12]],'7188A6'),
      poly([[11,7],[20,7],[24,11],[7,11]],'B5C8D9'),rect(7,12,18,3,'F0F2DC'),
      rect(6,16,20,3,'3B526D'),rect(8,20,16,2,'93AFBF'),rect(11,24,9,1,'475D78')]
    stone=[poly(shape,'45413E'),poly([[11,7],[20,7],[25,12],[25,20],[20,25],[11,25],[6,20],[6,12]],'969584'),
      poly([[11,7],[19,7],[22,11],[17,14],[8,12]],'C5C5AD'),
      poly([[6,16],[12,18],[13,24],[10,24],[6,20]],'747869'),
      poly([[20,14],[25,12],[25,20],[20,25],[15,24],[17,19]],'747869'),
      line([[15,9],[14,12],[17,15]],'747869'),line([[21,20],[18,21],[18,23]],'45413E')]
    return atlas([(n,draw(32,32,ops)) for n,ops in [('crystal',crystal),('metal',metal),('stone',stone)]])


def refined_buttons():
    cells=[]
    for state in STATES:
        fill={'hover':'345D78','pressed':'192D43','selected':'244F58','disabled':'334151'}.get(state,'263E56')
        border='D9B56C' if state=='focus' else '111E30'
        top='142337' if state=='pressed' else ('586879' if state=='disabled' else '66859B')
        bottom='66859B' if state=='pressed' else '15283D'
        ink='8997A5' if state=='disabled' else 'E5ECEE'
        ops=[rect(0,1,32,16,border),rect(1,0,30,18,border),rect(1,2,30,14,fill),
             rect(2,1,28,1,top),rect(2,16,28,1,bottom)]
        if state=='focus':ops += [rect(2,3,28,1,'D9B56C'),rect(2,14,28,1,'D9B56C')]
        if state=='selected':ops += [rect(2,14,28,2,'72CCC6'),line([[4,8],[6,10],[9,6]],'A4E2C8')]
        offset=1 if state=='pressed' else 0
        ops += [poly([[13,5+offset],[20,9+offset],[13,13+offset]],ink)]
        cells.append((state,draw(32,18,ops)))
    return atlas(cells,3)


def refined_panel(alternate=False):
    ops=[rect(0,0,96,64,'111E30'),rect(1,1,94,62,'1D293D'),rect(2,2,92,1,'596F86'),
      rect(5,5,86,10,'2F425A'),rect(5,5,3,10,'D9B56C'),
      rect(5,20,26,36,'26374D'),rect(7,22,22,9,'3A5368'),rect(7,29,22,2,'72CCC6'),
      rect(8,37,4,4,'9AAEC1'),rect(8,48,4,4,'9AAEC1'),
      rect(36,20,55,1,'51637A'),rect(36,38,55,1,'51637A'),
      rect(36,25,3,7,'72CCC6'),rect(36,43,3,7,'D9B56C'),
      rect(62,53,29,8,'162337'),rect(63,53,27,7,'72CCC6'),
      poly([[75,55],[79,57],[75,59]],'173642'),rect(5,59,27,1,'51637A')]
    if alternate: ops[3]=rect(5,5,86,10,'3A5368')
    return draw(96,64,ops)


def refined_mc_small():
    cells=[]
    for name in ('off','on','input','output','both'):
        ops=[dict(op='button',x=0,y=0,w=16,h=16,state='SELECTED' if name=='on' else 'NORMAL')]
        if name in ('off','on'):
            ink='234326' if name=='on' else '303030'
            ops += [line([[5,5],[4,6],[4,10],[6,12],[10,12],[12,10],[12,6],[11,5]],ink),
                    rect(7,3,2,6,ink)]
            if name=='on':ops += [rect(6,13,5,1,'234326')]
        else:
            if name=='both':
                ops += [poly([[3,4],[9,4],[9,3],[12,5],[9,7],[9,6],[3,6]],'193E5C'),
                        poly([[12,10],[6,10],[6,8],[3,11],[6,13],[6,12],[12,12]],'632D2D')]
            elif name=='input':
                ops += [poly([[3,7],[9,7],[9,4],[13,8],[9,12],[9,9],[3,9]],'193E5C')]
            else:
                ops += [poly([[12,7],[6,7],[6,4],[2,8],[6,12],[6,9],[12,9]],'632D2D')]
        cells.append((name,draw(16,16,ops,preset='minecraft')))
    return atlas(cells)


def candidate_specs():
    # Flat directional symbols and the accepted MC panel already meet this brief.
    return {'directions-12':baseline_specs()['directions-12'],
        'functions-16':atlas([(n,refined_function(n)) for n in ('add','remove','filter','refresh','transfer','lock')],3),
        'ship-32':refined_ship(), 'materials-32':refined_materials(), 'ui-states':refined_buttons(),
        'ui-panel':refined_panel(), 'minecraft-states':refined_mc_small(), 'minecraft-panel':mc_panel()}


def candidates():
    records=[]
    for name,spec in candidate_specs().items():
        path=ROOT/'examples/quality'/f'{name}.json';dump(path,spec)
        start=time.perf_counter_ns();image=render(spec);ms=(time.perf_counter_ns()-start)/1e6
        folder=ROOT/'output/quality';folder.mkdir(parents=True,exist_ok=True)
        image.save(folder/f'{name}.png')
        context=dict(version=1,asset_type='sprite' if name in ('directions-12','functions-16','ship-32','materials-32') else 'ui',
                     backgrounds=[dict(name='target',color='C6C6C6' if name.startswith('minecraft') else '1D293D')])
        if 'pixelart' in image.info:context['atlas']=image.info['pixelart']
        if name=='ui-panel':
            context['regions']=[dict(name=n,rect=box,role='reserved_text') for n,box in
                [('header',[11,7,76,6]),('navigation',[14,23,13,5]),('detail',[42,25,46,8]),('secondary',[42,43,46,7])]]
        if name=='minecraft-states':
            context['contrast_pairs']=[dict(name='input indicator',foreground='193E5C',background='8B8B8B'),
                                       dict(name='output indicator',foreground='632D2D',background='8B8B8B')]
        dump(ROOT/'examples/quality/contexts'/f'{name}.json',context)
        records.append(dict(task=name,render_ms=ms,candidates_used=2 if name in ('ship-32','ui-panel') else 1,
            revision_rounds=1 if name in ('functions-16','ship-32') else 0,authoring_time_seconds=None,
            timing_note='Render time only. Model authoring/token cost was not instrumented; no workflow speed claim.'))
    for name,spec in [('ship-wide',refined_ship(True)),('panel-brighter-header',refined_panel(True))]:
        dump(ROOT/'quality/drafts'/f'{name}.json',spec); render(spec).save(ROOT/'output/quality'/f'{name}.png')
    dump(ROOT/'quality/process.json',dict(created_at=datetime.now(timezone.utc).isoformat(),records=records,
        evaluation='Same author and evaluator; source-inspired authored studies, not randomized model trials.',
        decisions={'ship':'Narrow wing preserves clearer nose-to-engine axis; wide variant crowds silhouette.',
                   'panel':'Quieter header keeps action and selection emphasis; brighter alternate competes for attention.',
                   'functions_revision_1':'Initial rectangular refresh looked too square; use a curved ring with an arrowhead.',
                   'ship_revision_1':'Separate exhaust from hull alpha silhouette with a two-pixel offset.',
                   'contact_sheet_revision':'Increase row height to show the complete native-size panels; source art unchanged.'}))
    print('Rendered eight candidates and two draft alternatives')


TASKS = [
 ('directions-12','Four 12x12 directional icons on a dark blue UI; equal visual weight and safe margins.'),
 ('functions-16','Six 16x16 icons: add, remove, filter, refresh, transfer, lock; a coherent dark UI set.'),
 ('ship-32','A 32x32 asymmetric cyan ship, pointing upper-right, visible cockpit and separated exhaust.'),
 ('materials-32','The same 32x32 octagonal object in crystal, metal and stone; retain silhouette, show material.'),
 ('ui-states','32x18 buttons in normal, hover, focus, pressed, selected and disabled states, with a play icon.'),
 ('ui-panel','96x64 dark UI: header, navigation, grouped detail content, primary action; reserve runtime text areas.'),
 ('minecraft-states','16x16 Minecraft-like off, on, input, output, both controls; readable on a grey panel.'),
 ('minecraft-panel','96x54 Minecraft-like panel with three 18x18 slots and two distinct action buttons; seamless bevels.'),
]


def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def freeze():
    folder=ROOT/'quality/baseline'
    if folder.exists(): raise RuntimeError('Frozen baseline already exists; never regenerate it')
    started=datetime.now(timezone.utc).isoformat()
    records=[]
    for name,spec in baseline_specs().items():
        path=folder/f'{name}.json'; dump(path,spec)
        start=time.perf_counter_ns(); image=render(spec); ms=(time.perf_counter_ns()-start)/1e6
        image.save(path.with_suffix('.png'))
        records.append(dict(task=name,render_ms=ms,size=list(image.size),
            spec_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            png_sha256=hashlib.sha256(path.with_suffix('.png').read_bytes()).hexdigest(),
            rgba_sha256=hashlib.sha256(image.tobytes()).hexdigest(),
            candidates_used=1,revision_rounds=0))
    dump(ROOT/'quality/tasks.json',dict(authoring='Same-agent authored paired study, not independent model trials',
        baseline_skill_commit='4fb793962d2f489f1c32486f65dbeb5a032284f5',
        candidate_budget=2,max_revision_rounds=2,tasks=[dict(id=n,prompt=p) for n,p in TASKS]))
    dump(folder/'manifest.json',dict(frozen_at=started,records=records,
        guidance='Installed v1.0.0 SKILL and references, before quality workflow changes; no deliberate defects added.',
        limitations='Author already discussed improvement directions; this is not an unbiased causal experiment.'))
    # Freeze the current renderer output, including its three previously declared repairs.
    migrated=json.loads((ROOT/'specs/manifest.json').read_text(encoding='utf-8'))
    dump(ROOT/'quality/compatibility-v1.0.0.json',[
        dict(spec=e['spec'],size=list((im:=render(json.loads((ROOT/e['spec']).read_text(encoding='utf-8')))).size),
             rgba_sha256=hashlib.sha256(im.tobytes()).hexdigest()) for e in migrated])
    print('Frozen eight study baselines and 43 stable-version RGBA hashes')


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--freeze-baseline',action='store_true'); p.add_argument('--candidates',action='store_true'); args=p.parse_args()
    if args.freeze_baseline: freeze()
    if args.candidates: candidates()
