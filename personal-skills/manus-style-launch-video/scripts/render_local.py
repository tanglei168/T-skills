"""Render an already checked HyperFrames project without cloud services."""
import argparse, json, os, shutil, subprocess
from pathlib import Path

config_file=Path(__file__).resolve().parents[1]/'references'/'local-runtime.json'
local=json.loads(config_file.read_text()) if config_file.exists() else {}
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('project',type=Path)
p.add_argument('--cli',default=local.get('cli','hyperframes'))
p.add_argument('--chrome',default=local.get('chrome'))
p.add_argument('--ffmpeg',default=local.get('ffmpeg'))
p.add_argument('--ffprobe',default=local.get('ffprobe'))
p.add_argument('--output',type=Path)
p.add_argument('--workers',type=int,default=2)
p.add_argument('--quality',choices=['draft','looks','delivery'],default='looks')
a=p.parse_args()
project=a.project.resolve()
if not (project/'index.html').is_file():p.error('project must contain index.html')
env=os.environ.copy();env['HYPERFRAMES_NO_TELEMETRY']='1'
for flag,key in [(a.chrome,'PRODUCER_HEADLESS_SHELL_PATH'),(a.ffmpeg,'HYPERFRAMES_FFMPEG_PATH'),(a.ffprobe,'HYPERFRAMES_FFPROBE_PATH')]:
    if flag:
        file=Path(flag).resolve()
        if not file.is_file():p.error('binary does not exist: '+str(file))
        env[key]=str(file)
cli=shutil.which(a.cli) or str(Path(a.cli).resolve())
out=(a.output or project/'renders'/'launch-1080p.mp4').resolve()
out.parent.mkdir(parents=True,exist_ok=True)
subprocess.run([cli,'render',str(project),'--quality',a.quality,'--workers',str(a.workers),'--strict','--output',str(out)],env=env,check=True)
print(out)
