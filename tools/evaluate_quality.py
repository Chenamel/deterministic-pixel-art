"""Verify frozen evidence and assemble paired art studies; subjective verdicts stay explicit."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from pixelart import render,validate


def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def sheet(group,names,images):
    scales={'directions-12':8,'functions-16':8,'ship-32':8,'materials-32':4,
            'ui-states':4,'ui-panel':4,'minecraft-states':5,'minecraft-panel':4}
    heights=[images[n][0].height*scales[n]+images[n][0].height+64 for n in names]
    canvas=Image.new('RGB',(1020,sum(heights)+72),'#E9EDF2');pen=ImageDraw.Draw(canvas)
    font=ImageFont.load_default(size=14);small=ImageFont.load_default(size=12)
    pen.text((18,12),f'ORIGINAL STUDIES / {group} / author self-review',font=font,fill='#172033')
    pen.text((18,38),'Frozen v1.0.0 guidance',font=font,fill='#172033')
    pen.text((526,38),'Reference-informed candidate (not independent model trials)',font=small,fill='#172033')
    y=72
    for name,height in zip(names,heights):
        for side,im in enumerate(images[name]):
            x=18+side*508;scale=scales[name]
            bg=Image.new('RGBA',im.size,'#C6C6C6' if name.startswith('minecraft') else '#1D293D');bg.alpha_composite(im)
            pen.text((x,y),name,font=small,fill='#172033')
            canvas.paste(bg.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST).convert('RGB'),(x,y+22))
            canvas.paste(bg.convert('RGB'),(x,y+30+im.height*scale))
            pen.text((x+im.width+8,y+30+im.height*scale),'1:1',font=small,fill='#172033')
        y+=height
    target=ROOT/'docs/quality'/f'{group}.png';target.parent.mkdir(parents=True,exist_ok=True);canvas.save(target)


def evaluate(prepare=False):
    tasks=read(ROOT/'quality/tasks.json')['tasks'];frozen=read(ROOT/'quality/baseline/manifest.json')
    baseline={r['task']:r for r in frozen['records']}
    images={};records=[]
    for task in tasks:
        name=task['id'];old_spec=ROOT/'quality/baseline'/f'{name}.json';old_png=old_spec.with_suffix('.png')
        assert sha(old_spec)==baseline[name]['spec_sha256'],f'Frozen spec changed: {name}'
        assert sha(old_png)==baseline[name]['png_sha256'],f'Frozen PNG changed: {name}'
        with Image.open(old_png) as opened:old=opened.convert('RGBA')
        new_spec=ROOT/'examples/quality'/f'{name}.json';context=ROOT/'examples/quality/contexts'/f'{name}.json'
        new=render(read(new_spec));old_render=render(read(old_spec))
        assert old_render.tobytes()==old.tobytes(),f'Old recipe drift: {name}'
        assert validate(new,{'size':list(old.size),'mode':'RGBA','alpha':[0,255],'nonempty':True})['valid']
        png=ROOT/'output/quality'/f'{name}.png';png.parent.mkdir(parents=True,exist_ok=True);new.save(png)
        start=time.perf_counter()
        run=subprocess.run([sys.executable,'-B',str(ROOT/'src/pixel_art.py'),'review','--image',str(png),
            '--context',str(context),'--compare',str(old_png),'--out-dir',str(ROOT/'output/quality/reviews'/name),'--force'],
            capture_output=True,text=True,encoding='utf-8',timeout=30)
        elapsed=time.perf_counter()-start
        if run.returncode:raise RuntimeError(run.stderr)
        report=read(ROOT/'output/quality/reviews'/name/'report.json')
        images[name]=(old,new)
        records.append(dict(task=name,spec_sha256=sha(new_spec),context_sha256=sha(context),
             rgba_sha256=hashlib.sha256(new.tobytes()).hexdigest(),
             changed_pixels=report['comparison']['changed_visible_pixels'],
             warnings=report['warnings'],review_command_seconds=elapsed,
             time_scope='Source CLI startup, PNG/context loading, diagnostics and report writes; not authoring time.'))
    for group,names in [('icons',['directions-12','functions-16']),('art',['ship-32','materials-32']),
                        ('ui',['ui-states','ui-panel']),('minecraft',['minecraft-states','minecraft-panel'])]:
        sheet(group,names,images)
    compatibility=read(ROOT/'quality/compatibility-v1.0.0.json')
    for entry in compatibility:
        image=render(read(ROOT/entry['spec']))
        assert list(image.size)==entry['size'] and hashlib.sha256(image.tobytes()).hexdigest()==entry['rgba_sha256'],entry['spec']
    result=dict(technical_checks_passed=True,stable_outputs_unchanged=len(compatibility),cases=records,
        evidence='Authored paired study, same author/evaluator, not independent blind review or causal model evaluation.',
        in_game_tested=False,text_layout_tested=False,workflow_speed_measured=False)
    if not prepare:
        review=read(ROOT/'quality/agent-review.json')
        assert review['type']=='author_self_review'
        decisions={r['task']:r for r in review['cases']}
        assert set(decisions)==set(images)
        preferred=0
        for case in records:
            decision=decisions[case['task']]
            assert decision['spec_sha256']==case['spec_sha256'] and decision['context_sha256']==case['context_sha256'],'Review stale; inspect edited artwork again'
            assert decision['verdict'] in ('improved','unchanged') and decision['semantic_regression'] is False
            assert decision['basis'] and decision['tradeoffs'] is not None
            preferred+=decision['verdict']=='improved'
        assert preferred>=6,'Candidate does not meet the agreed self-review threshold'
        result.update(agent_review_passed=True,agent_preferred=preferred,agent_unchanged=8-preferred,
                      aesthetic_improvement_independently_proven=False)
    save(ROOT/'evaluation/quality-results.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='cases'}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
    evaluate(args.prepare)
