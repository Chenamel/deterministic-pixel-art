"""LT08 artifact contracts over the unchanged shared recorder."""
import json
import os
import sys
import recorder
BASE,RUN=recorder.BASE,recorder.RUN
_environment=recorder.environment

def environment():
    facts=_environment()
    facts.update(prefix=sys.prefix,base_prefix=sys.base_prefix,portable_output_setting=os.environ.get('PIXELART_PORTABLE_OUTPUT'))
    return facts

def check():
    recorder.integrity();checks=[]
    def add(name,passed,**facts):checks.append(dict(check=name,passed=bool(passed),**facts))
    def image(path):
        from PIL import Image
        with Image.open(path) as im:return im.convert('RGBA')
    def same(a,b):return a.size==b.size and a.tobytes()==b.tobytes()
    try:
        sys.path.insert(0,str(BASE/'deterministic-pixel-art/scripts'))
        from pixelart import render,make_preview,verify_edit,color
        from pixelart.compat import require_pillow
        from pixelart.assembly import load_project,assemble,seam_sheet
        require_pillow()
        brief=recorder.read(BASE/'inputs/brief.json');contract=recorder.read(RUN/'contract.json')
        colors={role:color(contract['palette'][role]) for role in brief['palette_roles']}
        add('shared-contract',contract.get('version')==1 and contract['size']==brief['size'] and contract['owners']==brief['owners'] and
            len(set(colors.values()))==5 and all(c[3]==255 for c in colors.values()))
        scenes={}
        for version in ('v1','v2'):
            for owner in brief['owners']:
                name=owner['name'];w,h=owner['rect'][2:];stem=f'{version}/chunks/{name}'
                actual=image(RUN/(stem+'.png'));rebuilt=render(recorder.read(RUN/(stem+'.json')))
                add(stem+'-editable',same(actual,rebuilt))
                add(stem+'-size',actual.size==(w,h))
                add(stem+'-opaque',set(actual.getchannel('A').tobytes())=={255})
            project,sources,_=load_project(RUN/version/'project.json')
            wanted=[dict(name=o['name'],image='chunks/'+o['name']+'.png',at=o['rect'][:2],mode='copy') for o in brief['owners']]
            add(version+'-project',project['size']==brief['size'] and project.get('require_coverage') is True and project['parts']==wanted)
            expected,report=assemble(project,sources);seams=seam_sheet(expected,report);scene=image(RUN/version/'scene.png');scenes[version]=scene
            add(version+'-assembled',same(scene,expected))
            add(version+'-assembly-report',recorder.read(RUN/version/'assembly.json')==json.loads(json.dumps(report)))
            add(version+'-seam-view',same(image(RUN/version/'seams.png'),seams.convert('RGBA')))
            add(version+'-preview',same(image(RUN/version/'scene-2x.png'),make_preview(scene,brief['preview_scale'])))
            add(version+'-coverage',report['uncovered_pixels']==0 and scene.size==tuple(brief['size']))
            add(version+'-plank-phase',all(scene.getpixel((x,y))==colors['joint' if x%brief['plank_period']==0 else 'plank']
                for y in brief['plank_probe_y'] for x in range(256)))
            add(version+'-water-phase',all(scene.getpixel((x,y))==colors['wave' if y%brief['wave_period']==0 else 'water']
                for x in brief['water_probe_x'] for y in range(256) if not brief['water_exclude_y'][0]<=y<brief['water_exclude_y'][1]))
            add(version+'-rail-crossings',all(scene.getpixel((x,y))==colors['rail'] for x in brief['rail_probe_x'] for y in brief['rail_probe_y']))
            x,y,w,h=brief['flag_rect'];ink=color(brief['flag_before' if version=='v1' else 'flag_after'])
            add(version+'-flag',all(scene.getpixel((xx,yy))==ink for xx in range(x,x+w) for yy in range(y,y+h)))
        for name in ('nw','ne','sw'):
            for suffix in ('.json','.png'):
                add('unchanged-'+name+suffix,(RUN/'v1/chunks'/(name+suffix)).read_bytes()==(RUN/'v2/chunks'/(name+suffix)).read_bytes())
        difference=verify_edit(scenes['v2'],scenes['v1'],regions=[brief['flag_rect']])
        add('only-flag-changed',difference['valid'] and difference['changed_rgba_pixels']==40,**difference)
        add('fresh-change-report',recorder.read(RUN/'change.json')==difference)
        records=[json.loads(line) for line in (RUN/'commands.jsonl').read_text(encoding='utf-8').splitlines()]
        session=recorder.read(RUN/'session.json')
        add('consistent-interpreter',bool(records) and all(r['environment']['executable']==session['environment']['executable'] and
            r['environment'].get('prefix')==session['environment'].get('prefix') for r in records))
        def recorded(command,names):
            return any(r['kind']=='tool' and r['arguments'][1:2]==[command] and r['exit_code']==0 and
                all(r['outputs_after'].get(n)==recorder.sha(RUN/n) and r['outputs_before'].get(n)!=recorder.sha(RUN/n) for n in names) for r in records)
        add('chunk-renders-recorded',all(recorded('render',[f'v1/chunks/{o["name"]}.png']) for o in brief['owners']) and recorded('render',['v2/chunks/se.png']))
        add('assemblies-recorded',all(recorded('assemble',[f'{v}/{n}']) for v in ('v1','v2') for n in ('scene.png','assembly.json','seams.png','scene-2x.png')))
        add('verify-recorded',recorded('verify',['change.json']))
        for owner in brief['owners']:
            name=owner['name'];relative='src/'+name+'.py';source=RUN/'v1/source'/(name+'.py')
            add('owner-source-'+name,source.is_file() and bool(source.read_text(encoding='utf-8').strip()) and any(
                r['kind']=='script' and r['exit_code']==0 and r['arguments'][0].replace('\\','/').endswith('/RUN/'+relative) and
                r['outputs_before'].get(relative)==recorder.sha(source) and
                r['outputs_after'].get(f'v1/chunks/{name}.json')==recorder.sha(RUN/f'v1/chunks/{name}.json') for r in records))
        protected={'contract.json':recorder.sha(RUN/'contract.json')}
        protected.update({p.relative_to(RUN).as_posix():recorder.sha(p) for p in (RUN/'v1').rglob('*') if p.is_file()})
        start=next((i for i,r in enumerate(records) if any(n.startswith('v2/') for n in set(r['outputs_before'])|set(r['outputs_after']))),None)
        add('v1-frozen-before-v2',start is not None and all(all(r[key].get(n)==d for n,d in protected.items())
            for r in records[start:] for key in ('outputs_before','outputs_after')))
    except (ImportError,OSError,ValueError,KeyError,TypeError,IndexError,RecursionError) as exc:
        add('required-artifacts',False,error=str(exc))
    feedback=RUN/'feedback.md';add('feedback-present',feedback.is_file() and bool(feedback.read_text(encoding='utf-8').strip()))
    result=dict(task='LT08',passed=bool(checks) and all(c['passed'] for c in checks),checks=checks,checked_utc=recorder.now(),
        scope='Pixels, sampled phase anchors, recorded calls and observed freeze only. Source independence, native detail, scene meaning, unseen seams and visual quality need separate review.')
    recorder.save(RUN/'checks.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['passed'] else 1

def main():
    recorder.check=check;recorder.environment=environment;code=recorder.main()
    if sys.argv[1:2]==['start']:
        session=recorder.read(RUN/'session.json');session['cohort']='chunks-workflow-dev-20261030';recorder.save(RUN/'session.json',session)
    return code

if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,ImportError) as exc:
        print(json.dumps(dict(error=str(exc)),ensure_ascii=False),file=sys.stderr);raise SystemExit(2)
