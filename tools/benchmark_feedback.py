"""Paired local timing versus v1.1.0; no model-workflow or token claims."""
import importlib.util
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from PIL import Image
from pixelart import render


def stats(values):
    values=sorted(values)
    return dict(samples=len(values),median_ms=statistics.median(values),p95_ms=values[int(.95*(len(values)-1))])


def main():
    baseline='f6a75287182e16ecd9d6d0a1613bd0360ade51a8'
    env={**os.environ,'PYTHONIOENCODING':'utf-8','PYTHONUTF8':'1'}
    with tempfile.TemporaryDirectory(prefix='反馈 benchmark space ') as directory:
        folder=Path(directory);oldroot=folder/'old';oldroot.mkdir()
        files=subprocess.check_output(['git','ls-tree','-r','--name-only',baseline,'src'],cwd=ROOT,text=True).splitlines()
        for name in files:
            p=oldroot/Path(name).relative_to('src');p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(subprocess.check_output(['git','show',baseline+':'+name],cwd=ROOT))
        module=importlib.util.spec_from_file_location('old_pixelart',oldroot/'pixelart/__init__.py',submodule_search_locations=[str(oldroot/'pixelart')])
        old=importlib.util.module_from_spec(module);sys.modules[module.name]=old;module.loader.exec_module(old)
        spec=json.loads((ROOT/'examples/quality/ship-32.json').read_text(encoding='utf-8'))
        kernels={}
        for name,fn in [('v1.1.0',old.render),('candidate',render)]:
            fn(spec);values=[]
            for _ in range(200):
                start=time.perf_counter();fn(spec);values.append((time.perf_counter()-start)*1000)
            kernels[name]=stats(values)
        image=folder/'source.png';render(spec).save(image)
        commands={label:{kind:[] for kind in ('render','review')} for label in ('v1.1.0','candidate')}
        for repeat in range(14):
            for label in (('v1.1.0','candidate') if repeat%2 else ('candidate','v1.1.0')):
                cli=oldroot/'pixel_art.py' if label=='v1.1.0' else ROOT/'src/pixel_art.py'
                for kind in ('render','review'):
                    args=([str(cli),'render','--spec',str(ROOT/'examples/quality/ship-32.json'),
                        '--out',str(folder/(label+'.png')),'--force'] if kind=='render' else
                        [str(cli),'review','--image',str(image),'--out-dir',str(folder/label),'--force'])
                    start=time.perf_counter();subprocess.run([sys.executable,'-B',*args],cwd=folder,env=env,check=True,capture_output=True)
                    elapsed=(time.perf_counter()-start)*1000
                    if repeat>=2:commands[label][kind].append(elapsed)
        png_equal=(folder/'v1.1.0.png').read_bytes()==(folder/'candidate.png').read_bytes()
        sizes={label:(folder/label/'report.json').stat().st_size for label in commands}
    result=dict(baseline_commit=baseline,python=sys.version,pillow=Image.__version__,
        environment='one local Windows host; alternating processes, two warmups, 12 measured pairs',
        kernel_render=kernels,cli={label:{kind:stats(v) for kind,v in kinds.items()} for label,kinds in commands.items()},
        review_json_bytes=sizes,default_png_bytes_equal=png_equal,
        workflow_time_measured=False,token_savings_measured=False,
        limits='Process and kernel timings are not agent correction-round or aesthetic evidence.')
    (ROOT/'docs/measurements/feedback-performance.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':main()
