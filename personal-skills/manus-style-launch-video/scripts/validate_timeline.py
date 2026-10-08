"""Validate frame continuity, local assets, and cited claim IDs."""
import argparse,json,re
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('timeline',type=Path)
a=p.parse_args();file=a.timeline.resolve();root=file.parent
t=json.loads(file.read_text());errors=[]
def issue(s):errors.append(s)
for name in ['fps','width','height','durationFrames']:
    if type(t.get(name)) is not int or t[name]<=0:issue(name+' must be a positive integer')
facts=(root/'facts.md').read_text() if (root/'facts.md').exists() else ''
ids=set();cursor=0
for s in t.get('scenes',[]):
    sid=s.get('id','')
    if not sid or sid in ids:issue('missing or duplicate scene ID: '+sid)
    ids.add(sid)
    start=s.get('startFrame');duration=s.get('durationFrames')
    if type(start) is not int or start<0 or type(duration) is not int or duration<=0:
        issue('invalid frame range: '+sid);continue
    if start!=cursor:issue('gap or overlap before '+sid)
    cursor=start+duration
    for asset in s.get('assets',[]):
        if not (root/asset).is_file():issue('missing asset: '+asset)
    for source in s.get('sourceIds',[]):
        if not re.search(r'\b'+re.escape(source)+r'\b',facts):issue('unknown source ID: '+source)
if cursor!=t.get('durationFrames'):issue('final scene does not end at durationFrames')
music=t.get('music')
if music and not (root/music['path']).is_file():issue('missing soundtrack')
if errors:p.exit(1,'\n'.join(errors)+'\n')
print(f"Timeline valid: {len(ids)} scenes, {cursor} frames, {cursor/t['fps']:.1f}s")
