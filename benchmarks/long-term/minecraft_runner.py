"""LT07 artifact checks; the shared command recorder stays unchanged."""
import json
import os
import sys

import recorder

BASE,RUN=recorder.BASE,recorder.RUN
_environment=recorder.environment


def environment():
    facts=_environment()
    facts.update(prefix=sys.prefix,base_prefix=sys.base_prefix,
                 portable_output_setting=os.environ.get('PIXELART_PORTABLE_OUTPUT'))
    return facts


def check():
    recorder.integrity()
    checks=[]
    def add(name,passed,**facts):checks.append(dict(check=name,passed=bool(passed),**facts))
    def image(path):
        from PIL import Image
        with Image.open(path) as opened:return opened.convert('RGBA')
    def same(a,b):return a.size==b.size and a.tobytes()==b.tobytes()
    try:
        sys.path.insert(0,str(BASE/'deterministic-pixel-art/scripts'))
        from pixelart import render,make_preview
        from pixelart.compat import pixels,require_pillow
        from pixelart.metadata import layout_record
        from pixelart.assembly import load_project,assemble,seam_sheet
        require_pillow()
        brief=recorder.read(BASE/'inputs/brief.json')
        assets={}
        for name,size in [('panel/body',brief['body_size']),('panel/footer',brief['footer_size']),
                          ('buttons',[brief['button_size'][0]*len(brief['states']),brief['button_size'][1]])]:
            actual=image(RUN/(name+'.png'));expected=render(recorder.read(RUN/(name+'.json')))
            assets[name]=actual
            add(name+'-editable-rerenders',same(actual,expected))
            add(name+'-size',list(actual.size)==size)
            alpha=actual.getchannel('A').tobytes()
            add(name+'-alpha',set(alpha)<={0,255} and (name=='buttons' or set(alpha)=={255}))
            if name=='buttons':
                add('fresh-layout',recorder.read(RUN/'layout.json')==json.loads(json.dumps(layout_record(expected))))
                w,h=brief['button_size']
                wanted=dict(cell_size=[w,h],columns=len(brief['states']),rows=1,
                    cells=[dict(name=state,x=i*w,y=0,w=w,h=h) for i,state in enumerate(brief['states'])])
                add('named-states',expected.info.get('pixelart')==wanted)
                visible=[]
                for i,state in enumerate(brief['states']):
                    cell=actual.crop((i*w,0,(i+1)*w,h))
                    add(state+'-nonempty',bool(cell.getchannel('A').getbbox()))
                    visible.append(b''.join(bytes(p if p[3] else (0,0,0,0)) for p in pixels(cell)))
                add('distinct-visible-states',len(set(visible))==len(brief['states']))
        project,sources,_=load_project(RUN/'scene.json')
        add('consumer-project',project.get('version',1)==1 and project['size']==brief['scene_size'] and
            project.get('require_coverage') is True and project['parts']==brief['parts'])
        scene,report=assemble(project,sources)
        seams=seam_sheet(scene,report)
        actual_scene=image(RUN/'scene.png')
        add('scene-assembled-exactly',same(scene,actual_scene))
        add('fresh-assembly-report',recorder.read(RUN/'assembly.json')==json.loads(json.dumps(report)))
        add('seam-view-exact',same(seams.convert('RGBA'),image(RUN/'seams.png')))
        add('scene-coverage',report['uncovered_pixels']==0 and actual_scene.size==tuple(brief['scene_size']))
        preview_files=[]
        for asset,actual in [('scene',actual_scene),('buttons',assets['buttons'])]:
            for theme,background in brief['backgrounds'].items():
                for scale in brief['view_scales']:
                    name=f'views/{asset}-{theme}-{scale}x.png'
                    add(name+'-exact-preview',same(image(RUN/name),make_preview(actual,scale,background)))
                    preview_files.append(name)
        records=[json.loads(line) for line in (RUN/'commands.jsonl').read_text(encoding='utf-8').splitlines()]
        session=recorder.read(RUN/'session.json')
        add('consistent-recorded-interpreter',bool(records) and all(
            row['environment']['executable']==session['environment']['executable'] and
            row['environment'].get('prefix')==session['environment'].get('prefix') for row in records))
        def recorded(command,names):
            return any(row['kind']=='tool' and row['arguments'][1:2]==[command] and row['exit_code']==0 and
                all(row['outputs_after'].get(name)==recorder.sha(RUN/name) and
                    row['outputs_before'].get(name)!=recorder.sha(RUN/name) for name in names) for row in records)
        add('component-renders-recorded',all(recorded('render',[name+'.png']) for name in assets))
        add('layout-render-recorded',recorded('render',['buttons.png','layout.json']))
        add('assembly-recorded',recorded('assemble',['scene.png','assembly.json','seams.png']))
        add('final-previews-recorded',all(recorded('preview',[name]) for name in preview_files))
    except (ImportError,OSError,ValueError,KeyError,TypeError,IndexError,RecursionError) as exc:
        add('required-artifacts',False,error=str(exc))
    feedback=RUN/'feedback.md'
    add('feedback-present',feedback.is_file() and bool(feedback.read_text(encoding='utf-8').strip()))
    result=dict(task='LT07',passed=bool(checks) and all(item['passed'] for item in checks),checks=checks,
        checked_utc=recorder.now(),scope='Artifact geometry, pixels and recorded calls only. Slot shape, bevel continuity, state meaning, reserved content, aesthetics and game/font integration require separate review.')
    recorder.save(RUN/'checks.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['passed'] else 1


def main():
    recorder.check=check;recorder.environment=environment
    code=recorder.main()
    if sys.argv[1:2]==['start']:
        session=recorder.read(RUN/'session.json');session['cohort']='minecraft-composition-dev-20261030'
        recorder.save(RUN/'session.json',session)
    return code


if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,ImportError) as exc:
        print(json.dumps(dict(error=str(exc)),ensure_ascii=False),file=sys.stderr)
        raise SystemExit(2)
