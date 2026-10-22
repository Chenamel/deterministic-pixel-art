"""Eight artifact-level feedback checks, explicitly not external agent trials."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from pixelart import __version__,image_to_spec,inspect_image,render
from pixelart.review import review


def main():
    out=ROOT/'evaluation/feedback';out.mkdir(parents=True,exist_ok=True)
    cases=[]
    for item in json.loads((ROOT/'quality/tasks.json').read_text(encoding='utf-8'))['tasks']:
        name=item['id'];spec=ROOT/'examples/quality'/f'{name}.json'
        ctx=json.loads((ROOT/'examples/quality/contexts'/f'{name}.json').read_text(encoding='utf-8'))
        image=render(json.loads(spec.read_text(encoding='utf-8')))
        converted=image_to_spec(image);roundtrip=render(converted)
        assert image.size==roundtrip.size and image.tobytes()==roundtrip.tobytes(),name
        facts=inspect_image(image,ctx)
        cells=facts['cells']
        selected=inspect_image(image,ctx,cell=cells[0]['name'],grid=True) if cells else inspect_image(image,ctx,region=[0,0,min(32,image.width),min(32,image.height)],grid=True)
        report,sheet,_=review(image,ctx)
        assert report['analysis']==facts,name
        folder=out/name;folder.mkdir(exist_ok=True)
        image.save(folder/'source.png');roundtrip.save(folder/'roundtrip.png');sheet.save(folder/'review.png')
        (folder/'inspect.json').write_text(json.dumps(facts,indent=2),encoding='utf-8')
        (folder/'grid.json').write_text(json.dumps(selected['grid'],indent=2),encoding='utf-8')
        cases.append(dict(task=name,lossless_rgba=True,shared_review_analysis=True,
                          bounded_grid=True,cells=len(cells),source_sha256=hashlib.sha256(spec.read_bytes()).hexdigest()))
    result=dict(version=__version__,artifact_checks_passed=True,cases=cases,
                external_agent_trials_completed=False,workflow_gain_proven=False,
                aesthetic_improvement_proven=False,
                note='Scripted artifact checks, not model task performance or blind review.')
    target=ROOT/'docs/measurements/feedback-capabilities.json'
    target.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=True,artifact_tasks=len(cases),external_trials=False)))


if __name__=='__main__':main()
