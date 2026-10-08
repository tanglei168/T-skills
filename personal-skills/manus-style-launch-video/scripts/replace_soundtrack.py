"""Replace a finished film's soundtrack while proving its picture is unchanged."""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('video', type=Path)
p.add_argument('audio', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--ffmpeg', default=shutil.which('ffmpeg'))
p.add_argument('--ffprobe', default=shutil.which('ffprobe'))
p.add_argument('--report', type=Path)
p.add_argument('--overwrite', action='store_true')
a = p.parse_args()
video, audio, output = (x.resolve() for x in (a.video, a.audio, a.output))
report = (a.report or output.with_suffix('.qa.json')).resolve()

for file in (video, audio):
    if not file.is_file():
        p.error('input does not exist: ' + str(file))
if output.suffix.lower() != '.mp4':
    p.error('output must be an MP4 file')
if output in (video, audio) or report in (video, audio, output):
    p.error('input, output, and report paths must not collide')
for file in (output, report):
    if file.exists() and not a.overwrite:
        p.error('output already exists; choose a new path or use --overwrite: ' + str(file))
for name in ('ffmpeg', 'ffprobe'):
    value = getattr(a, name)
    resolved = (shutil.which(value) or str(Path(value).resolve())) if value else None
    if not resolved or not Path(resolved).is_file():
        p.error('provide an available --' + name)
    setattr(a, name, resolved)

def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)

def probe(file):
    return json.loads(run([a.ffprobe, '-v', 'error', '-show_format', '-show_streams',
                           '-of', 'json', str(file)]).stdout)

def first(meta, kind):
    streams = [s for s in meta['streams'] if s['codec_type'] == kind]
    if not streams:
        raise ValueError('input contains no ' + kind + ' stream')
    return streams[0]

def duration(meta, stream):
    value = stream.get('duration') or meta.get('format', {}).get('duration')
    if value is None or not math.isfinite(float(value)) or float(value) <= 0:
        raise ValueError('input has no positive duration')
    return float(value)

def picture_hash(file):
    return run([a.ffmpeg, '-v', 'error', '-i', str(file), '-map', '0:v:0',
                '-c', 'copy', '-f', 'hash', '-hash', 'sha256', '-']).stdout.strip().split('=', 1)[-1]

def finite(value):
    value = float(value)
    return value if math.isfinite(value) else None

scratch = None
try:
    original, sound = probe(video), probe(audio)
    v, s = first(original, 'video'), first(sound, 'audio')
    seconds = duration(original, v)
    fps = 0
    for rate in (v.get('avg_frame_rate'), v.get('r_frame_rate')):
        try:
            fps = float(Fraction(rate))
        except (TypeError, ValueError, ZeroDivisionError):
            continue
        if fps > 0:
            break
    if fps <= 0:
        raise ValueError('input has no positive frame rate')
    if duration(sound, s) < seconds - 1 / fps:
        raise ValueError('soundtrack is shorter than the picture; finish its tail before replacing')
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.soundtrack-', suffix='.mp4', dir=output.parent)
    os.close(fd)
    scratch = Path(name)
    codec = ['-c:a', 'copy'] if s['codec_name'] == 'aac' else ['-c:a', 'aac', '-b:a', '320k', '-ar', '48000']
    run([a.ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(video),
         '-i', str(audio), '-map', '0:v:0', '-map', '1:a:0', '-map_metadata', '-1',
         '-c:v', 'copy', *codec, '-t', str(seconds), '-movflags', '+faststart', str(scratch)])
    result = probe(scratch)
    rv, rs = first(result, 'video'), first(result, 'audio')
    before, after = picture_hash(video), picture_hash(scratch)
    if before != after:
        raise ValueError('picture stream changed during replacement')
    if abs(duration(result, rv) - seconds) > max(.1, 2 / fps):
        raise ValueError('output picture duration changed')
    if (rv['width'], rv['height']) != (v['width'], v['height']):
        raise ValueError('output dimensions changed')
    if rs['channels'] != s['channels']:
        raise ValueError('output audio channel count changed')
    run([a.ffmpeg, '-v', 'error', '-xerror', '-i', str(scratch), '-f', 'null', '-'])
    measured = run([a.ffmpeg, '-hide_banner', '-i', str(scratch), '-vn', '-af',
                    'loudnorm=I=-17:TP=-1:LRA=11:print_format=json', '-f', 'null', '-'])
    reading = json.loads(re.findall(r'\{[^{}]*\}', measured.stderr)[-1])
    summary = dict(passed=True, sourceVideo=str(video), sourceAudio=str(audio),
                   output=str(output), durationSeconds=seconds, width=rv['width'],
                   height=rv['height'], fps=fps, audioCodec=rs['codec_name'],
                   audioChannels=rs['channels'], pictureUnchanged=True,
                   pictureSHA256=after, fullDecodePassed=True,
                   integratedLUFS=finite(reading['input_i']),
                   truePeakDBFS=finite(reading['input_tp']),
                   loudnessRangeLU=finite(reading['input_lra']),
                   note='Measurements describe the saved soundtrack; no loudness filter is written to the movie.')
    os.replace(scratch, output)
    scratch = None
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False))
except (ValueError, KeyError, IndexError, subprocess.CalledProcessError) as exc:
    detail = exc.stderr[-2000:] if isinstance(exc, subprocess.CalledProcessError) else str(exc)
    p.exit(1, 'Soundtrack replacement failed: ' + detail + '\n')
finally:
    if scratch and scratch.exists():
        scratch.unlink()
