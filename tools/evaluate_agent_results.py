"""Grade retained paired agent artifacts; missing evidence never becomes a pass."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'runtime' if (HERE/'runtime').exists() else HERE.parent/'src'))
from pixelart import render


def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def pixels_in(rects,size):
    result=set()
    if not isinstance(rects,list) or len(rects)>64:raise ValueError('invalid localization regions')
    for rect in rects:
        if not isinstance(rect,list) or len(rect)!=4 or any(type(v) is not int for v in rect):raise ValueError('invalid localization rect')
        x,y,w,h=rect
        if min(x,y)<0 or min(w,h)<1 or x+w>size[0] or y+h>size[1]:raise ValueError('localization outside image')
        result.update((xx,yy) for yy in range(y,y+h) for xx in range(x,x+w))
    return result


def evaluate(manifest_path,runs,visual_review=None):
    manifest=read(manifest_path);tasks={t['id']:t for t in manifest['tasks']};key=manifest['key']
    cases=[];errors=[]
    for record in sorted(Path(runs).rglob('run.json')):
        try:
            data=read(record);folder=record.parent;task=tasks[data['task']]
            if data.get('finished_at') is None:raise ValueError('unfinished run')
            label=data['package'];expected_hash=key['candidate_sha256'] if label==key['candidate_label'] else key['baseline_sha256']
            if label not in ('A','B') or data.get('package_sha256')!=expected_hash:raise ValueError('package hash mismatch')
            if type(data.get('candidates')) is not int or not 1<=data['candidates']<=2:raise ValueError('candidate budget')
            if type(data.get('revisions')) is not int or not 0<=data['revisions']<=2:raise ValueError('revision budget')
            for name,digest in data.get('artifacts',{}).items():
                path=(folder/name).resolve()
                if not path.is_relative_to(folder.resolve()) or not path.is_file() or sha(path)!=digest:raise ValueError('artifact hash mismatch')
            expected=manifest_path.parent/'expected'/f"{data['task']}.png"
            if sha(expected)!=task['expected_sha256']:raise ValueError('grading fixture hash mismatch')
            with Image.open(expected) as im:truth=im.convert('RGBA')
            local=False;contract=False;spec_matches=False
            if (folder/'localization.json').is_file():
                predicted=pixels_in(read(folder/'localization.json').get('regions'),truth.size)
                target=pixels_in([task['localization_rect']],truth.size)
                local=len(predicted&target)/len(predicted|target)>=.8
            if (folder/'final.png').is_file():
                with Image.open(folder/'final.png') as im:final=im.convert('RGBA')
                contract=final.size==truth.size and final.tobytes()==truth.tobytes()
                if (folder/'final.json').is_file():
                    reconstructed=render(read(folder/'final.json'))
                    spec_matches=reconstructed.size==final.size and reconstructed.tobytes()==final.tobytes()
            commands=[json.loads(line) for line in (folder/'commands.jsonl').read_text(encoding='utf-8').splitlines()]
            frozen=data.get('artifacts',{})
            required=('localization.json','final.json','final.png','commands.jsonl')
            complete=all(name in frozen for name in required) and bool(commands)
            # At least one recorded command must have seen the frozen initial localization.
            localization_recorded=any(c.get('localization_sha256')==frozen.get('localization.json') for c in commands)
            cases.append(dict(task=data['task'],environment=data['environment'],mode=data['mode'],package=label,
                candidate=label==key['candidate_label'],model=data['model'],python=data['python'],pillow=data['pillow'],
                platform=data['platform'],shim=data['shim'],failure_stage=data.get('failure_stage','none'),
                localization_success=local and localization_recorded,contract_success=contract and spec_matches,
                evidence_complete=complete,commands=len(commands),command_seconds=sum(c['seconds'] for c in commands),
                revisions=data['revisions'],tokens_total=data.get('tokens_total'),
                final_sha256=frozen.get('final.png'),run=str(record)))
        except (KeyError,ValueError,OSError) as exc:errors.append(dict(run=str(record),error=str(exc)))
    grouped=defaultdict(dict)
    for case in cases:
        keypair=(case['environment'],case['task'])
        if case['candidate'] in grouped[keypair]:errors.append(dict(run=case['run'],error='duplicate environment/task/package'))
        grouped[keypair][case['candidate']]=case
    pairs=[]
    for (environment,task),pair in sorted(grouped.items()):
        if set(pair)!={False,True}:continue
        old,new=pair[False],pair[True]
        comparable=all(old[k]==new[k] for k in ('model','python','pillow','platform','mode','shim'))
        comparable=comparable and not new['shim'] and all(c['evidence_complete'] and c['failure_stage']!='environment' for c in (old,new))
        gain=comparable and new['contract_success'] and new['evidence_complete'] and (
            (new['localization_success'] and not old['localization_success']) or
            (old['contract_success'] and new['revisions']<old['revisions']))
        regression=comparable and ((old['localization_success'] and not new['localization_success']) or
            (old['contract_success'] and (not new['contract_success'] or new['revisions']>old['revisions'])))
        pairs.append(dict(environment=environment,task=task,mode=new['mode'],comparable=comparable,
                          candidate_contract_passed=new['contract_success'] and new['evidence_complete'],
                          improved=gain and not regression,regressed=regression))
    complete_modes=set()
    for environment in {p['environment'] for p in pairs}:
        rows=[p for p in pairs if p['environment']==environment]
        if len(rows)==len(tasks) and len({p['mode'] for p in rows})==1 and all(p['comparable'] and p['candidate_contract_passed'] for p in rows):complete_modes.add(rows[0]['mode'])
    improved=[task for task in tasks if any(p['improved'] for p in pairs if p['task']==task)
              and not any(p['regressed'] for p in pairs if p['task']==task)]
    visual=read(visual_review) if visual_review else {}
    reviews=visual.get('cases',[])
    semantic_ok=bool(cases) and bool(visual.get('reviewer')) and visual.get('type') in ('human','independent_agent')
    for case in [c for c in cases if c['candidate']]:
        matches=[r for r in reviews if r.get('task')==case['task'] and r.get('environment')==case['environment']
                 and r.get('final_sha256')==case['final_sha256']]
        semantic_ok=semantic_ok and len(matches)==1 and matches[0].get('critical_regression') is False and bool(matches[0].get('notes'))
    passed=not errors and complete_modes=={'text_only','multimodal'} and len(improved)>=6 and semantic_ok
    return dict(version=1,stable_release_gate_passed=passed,external_runs=len(cases),paired_tasks=len(pairs),
        complete_modes=sorted(complete_modes),improved_task_ids=improved,semantic_review_complete=semantic_ok,
        errors=errors,cases=cases,pairs=pairs,
        limits='Recorded external evidence is not independent proof of general aesthetics or game integration.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--runs',type=Path,required=True)
    parser.add_argument('--visual-review',type=Path);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();result=evaluate(args.manifest,args.runs,args.visual_review)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(stable_release_gate_passed=result['stable_release_gate_passed'],external_runs=result['external_runs'])))
    return 0 if result['stable_release_gate_passed'] else 1


if __name__=='__main__':raise SystemExit(main())
