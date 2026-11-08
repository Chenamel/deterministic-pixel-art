from pathlib import Path
import shutil

r = Path(__file__).resolve().parent
shutil.copytree(r / 'src', r / 'v1/source')
