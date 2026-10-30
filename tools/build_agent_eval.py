"""Build fixed-input agent/evaluator bundles without running or grading agents."""
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from pixelart import render
from pixelart.compat import pixels
from pixelart.metadata import layout_record

BASELINE='f6a75287182e16ecd9d6d0a1613bd0360ade51a8'


def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')


def zip_files(target,files):
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as bundle:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.create_system=3
            info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED
            bundle.writestr(info,data)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def fixtures():
    cases=[]
    tasks=json.loads((ROOT/'quality/tasks.json').read_text(encoding='utf-8'))['tasks']
    for index,task in enumerate(tasks):
        name=task['id'];ctx=json.loads((ROOT/'examples/quality/contexts'/f'{name}.json').read_text(encoding='utf-8'))
        original=render(json.loads((ROOT/'examples/quality'/f'{name}.json').read_text(encoding='utf-8')))
        expected=original.copy()
        # A fixed held-out value variation prevents simply rerendering the bundled demo.
        expected.putdata([(r*9//10+9,g*9//10+9,b*9//10+9,a) if a else (r,g,b,a) for r,g,b,a in pixels(original)])
        image=expected.copy();reference=None;reference_rect=None
        if name=='directions-12':
            assert not image.getpixel((0,0))[3]
            image.putpixel((0,0),(255,0,255,255));box=[0,0,1,1]
            prompt='清除画布边缘不属于四个方向图形的散点；保留方向、配色、间距和其余像素。'
        elif name=='ship-32':
            found=None
            for y in range(image.height):
                for x in range(image.width-1):
                    if all(not image.getpixel((nx,ny))[3] for ny in range(max(0,y-1),min(image.height,y+2))
                           for nx in range(max(0,x-1),min(image.width,x+3))):found=(x,y);break
                if found:break
            x,y=found;image.putpixel((x,y),(255,0,255,255));image.putpixel((x+1,y),(255,0,255,255));box=[x,y,2,1]
            prompt='移除与船体和尾焰分离的小残片；保持原船头方向、非对称形体和合法尾焰，其余像素不变。'
        elif name=='materials-32':
            x,y=next((x,y) for y in range(image.height) for x in range(image.width) if image.getpixel((x,y))[3]==255)
            r,g,b,_=image.getpixel((x,y));image.putpixel((x,y),(r,g,b,128));box=[x,y,1,1]
            prompt='材质图集契约为二元透明度。将意外的半透明像素恢复为完全不透明，保持其 RGB、各材质形体和其余像素。'
        elif name=='ui-states':
            atlas=image.info['pixelart'];normal=next(c for c in atlas['cells'] if c['name']=='normal')
            hover=next(c for c in atlas['cells'] if c['name']=='hover')
            box=[hover[k] for k in ('x','y','w','h')];x,y,w,h=box
            reference=expected.crop((x,y,x+w,y+h));reference_rect=box
            source=expected.crop((normal['x'],normal['y'],normal['x']+w,normal['y']+h));image.paste(source,(x,y))
            prompt='图集的 hover 槽位被普通状态替换。将 reference.png 恢复到名为 hover 的单元，保留其他状态及布局。'
        elif name in ('functions-16','ui-panel'):
            if name=='ui-panel':
                region=next(r['rect'] for r in ctx['regions'] if r['role']=='reserved_text')
                x,y=region[0]+region[2]//2,region[1]+region[3]//2
            else:x,y=next((x,y) for y in range(image.height) for x in range(image.width) if image.getpixel((x,y))[3])
            correct=image.getpixel((x,y));image.putpixel((x,y),(255,0,255,255));box=[x,y,1,1]
            color=bytes(correct).hex().upper()
            prompt=f'清除不属于风格色板的品红错误像素，用 #{color} 恢复。保持其余像素、状态与内容预留区，不增加文字。'
        else:
            if name=='minecraft-states':
                x,y=next((x,y) for y in range(1,image.height-1) for x in range(1,15)
                    if image.getpixel((x,y))[3] and all(image.getpixel((x+dx,y+dy))==image.getpixel((x,y))
                       for dx,dy in ((-1,0),(1,0),(0,-1),(0,1))))
                prompt='修补第一枚控件纯色区域内的意外透明缺口；继承周围颜色，不改变状态图形、边缘和其他单元。'
            else:
                x,y=next((x,y) for y in range(3) for x in range(5,image.width-5) if image.getpixel((x,y))[3])
                prompt='修补面板上边缘的一个意外透明缺口，按相邻边缘延续浮雕；保留槽位、按钮和其他像素。'
            image.putpixel((x,y),(0,0,0,0));box=[x,y,1,1]
        cases.append(dict(id=name,brief=task['prompt'],prompt=prompt,image=image,expected=expected,
                          context=ctx,box=box,reference=reference,reference_rect=reference_rect))
    return cases


def main():
    folder=ROOT/'evaluation/agent-eval';folder.mkdir(parents=True,exist_ok=True)
    agent=folder/'agent';judge=folder/'evaluator';agent.mkdir(exist_ok=True);judge.mkdir(exist_ok=True)
    old={}
    paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASELINE,'skill/deterministic-pixel-art'],cwd=ROOT,text=True).splitlines()
    for path in paths:
        old[path.removeprefix('skill/')]=subprocess.check_output(['git','show',BASELINE+':'+path],cwd=ROOT)
    baseline=folder/'baseline.zip';zip_files(baseline,old)
    candidate=ROOT/'deterministic-pixel-art.zip'
    keypath=folder/'version-key.json';key=json.loads(keypath.read_text(encoding='utf-8')) if keypath.exists() else {}
    if key.get('candidate_sha256')!=sha(candidate):
        candidate_label=secrets.choice(['A','B'])
        key=dict(candidate_label=candidate_label,baseline_label='B' if candidate_label=='A' else 'A',
                 candidate_sha256=sha(candidate),baseline_sha256=sha(baseline),baseline_commit=BASELINE)
        save(keypath,key)
    for label,source in [(key['baseline_label'],baseline),(key['candidate_label'],candidate)]:
        target=agent/'packages'/f'{label}.zip';target.parent.mkdir(exist_ok=True);shutil.copyfile(source,target)
    shutil.copyfile(ROOT/'benchmarks/runner.py',agent/'runner.py')
    shutil.copyfile(ROOT/'benchmarks/PROTOCOL.md',agent/'README.md')
    manifest=[]
    for case in fixtures():
        name=case['id'];task=agent/'tasks'/name;task.mkdir(parents=True,exist_ok=True)
        case['image'].save(task/'input.png');save(task/'context.json',case['context'])
        save(task/'layout.json',layout_record(case['image']))
        if case['reference'] is not None:case['reference'].save(task/'reference.png')
        (task/'request.md').write_text('# '+name+'\n\n'+case['prompt']+'\n\n先保存初次定位，再修改。只对 input.png 做上述局部修改，生成 final.json 与 final.png，保留原尺寸和其余像素。\n',encoding='utf-8')
        truth=judge/'expected'/f'{name}.png';truth.parent.mkdir(exist_ok=True);case['expected'].save(truth)
        manifest.append(dict(id=name,localization_rect=case['box'],input_sha256=sha(task/'input.png'),expected_sha256=sha(truth),
                             creation_brief=case['brief']))
    save(judge/'manifest.json',dict(version=1,tasks=manifest,key=key))
    save(judge/'visual-review-template.json',dict(reviewer=None,type='independent_agent',
        cases=[dict(environment=environment,task=t['id'],final_sha256=None,critical_regression=None,notes='')
               for environment in ('TEXT_ENV_ID','VISUAL_ENV_ID') for t in manifest]))
    shutil.copyfile(ROOT/'tools/evaluate_agent_results.py',judge/'evaluate_agent_results.py')
    runtime=judge/'runtime';runtime.mkdir(exist_ok=True)
    for p in (ROOT/'src').rglob('*.py'):
        target=runtime/p.relative_to(ROOT/'src');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    (judge/'README.md').write_text('Run with Python and Pillow: `python evaluate_agent_results.py --manifest manifest.json --runs RUNS --out result.json [--visual-review review.json]`. Exit 1 means the gate has not passed. Fill visual-review-template.json with the actual reviewer, environment IDs, candidate PNG SHA-256 and specific direction/state/content/seam observations; null is not a pass. Human and independent visual-agent review are accepted. Do not give this directory to evaluated agents. This is the external evidence gate; engineering CI must also pass before a stable release.\n\n验收包不交给被测模型。模板空值不是通过；核对实际环境、PNG 哈希及方向/状态/内容遮挡/边缘，并保留独立复检记录。\n',encoding='utf-8')
    for source,name in [(agent,'agent-evaluation-v1.2.0-rc.1.zip'),(judge,'agent-evaluator-v1.2.0-rc.1.zip')]:
        files={p.relative_to(source).as_posix():p.read_bytes() for p in source.rglob('*') if p.is_file()}
        checks={name:hashlib.sha256(data).hexdigest() for name,data in files.items()}
        files['checksums.json']=json.dumps(checks,sort_keys=True,indent=2).encode()
        zip_files(folder/name,files)
    print(json.dumps(dict(tasks=len(manifest),external_results=0,agent_bundle=str(folder/'agent-evaluation-v1.2.0-rc.1.zip'))))


if __name__=='__main__':main()
