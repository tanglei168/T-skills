#!/usr/bin/env python3
"""Render an original, fully arranged launch cue, not a tiled audio loop.

Requires numpy and scipy. Outputs 48 kHz float premaster, stems and an event
ledger. Master with fixed gain after measuring; do not flatten the breakdown.
All instruments are synthesized here. No samples, model or third-party music.
"""
import argparse, json
from pathlib import Path
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io.wavfile import write as wavwrite

SR = 48000
BPM = 122
BEAT = 60 / BPM
LENGTH = 110.0
N = round(LENGTH * SR)
RNG = np.random.default_rng(12220261008)

def freq(note):
    return 440 * 2 ** ((note - 69) / 12)

def smooth(x):
    x = np.clip(x, 0, 1)
    return x*x*(3-2*x)

def lowpass(x, hz, order=2):
    return sosfilt(butter(order, hz, fs=SR, output='sos'), x, axis=0).astype(np.float32)

def bandpass(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], btype='bandpass', fs=SR, output='sos'), x, axis=0).astype(np.float32)

def onset(t, seconds=.006):
    return smooth(t / seconds)

def release(t, length, seconds=.06):
    return smooth((length-t) / seconds)

def pluck(note, length=1.35, shade=0):
    t = np.arange(round(length*SR)) / SR
    f = freq(note)
    # A bell-like FM transient settles into a soft fundamental, with no brittle lead.
    mod = (1.10 + .22*shade) * np.exp(-t/.085) * np.sin(2*np.pi*f*2*t)
    y = .73*np.sin(2*np.pi*f*t + mod) * np.exp(-t/.35)
    y += .15*np.sin(2*np.pi*f*2*t)*np.exp(-t/.13)
    y += .07*np.sin(2*np.pi*f*3*t)*np.exp(-t/.06)
    return (lowpass(y, 6000)*onset(t,.004)*release(t,length)).astype(np.float32)

def bass(note, length):
    t = np.arange(round(length*SR)) / SR
    f = freq(note)
    phase = 2*np.pi*f*t
    y = .84*np.sin(phase) + .10*np.sin(2*phase) + .06*np.sin(3*phase)
    env = onset(t,.009)*np.exp(-t/.50)*release(t,length,.045)
    return (y*env).astype(np.float32)

def pad(notes, length, brightness=0):
    t = np.arange(round(length*SR))/SR
    left = np.zeros(t.size);right = left.copy()
    for ni,note in enumerate(notes):
        f = freq(note)
        ph = RNG.uniform(0,2*np.pi)
        for h in range(1,9):
            amp = np.exp(-h/(2.1+.35*brightness))/(h**.75)
            left += amp*np.sin(2*np.pi*f*h*2**(-3.5/1200)*t+ph+.04*np.sin(2*np.pi*.17*t))
            right += amp*np.sin(2*np.pi*f*h*2**(3.5/1200)*t+ph+.04*np.sin(2*np.pi*.19*t+1))
    env = smooth(t/.65)*smooth((length-t)/.85)
    env *= .96+.04*np.sin(2*np.pi*.23*t)
    return np.stack([left*env,right*env],axis=1).astype(np.float32) / len(notes)

def kick():
    t = np.arange(round(.48*SR))/SR
    # Phase-continuous rounded kick, low click, no hard clipping.
    phase = 2*np.pi*(47*t+78*.018*(1-np.exp(-t/.018)))
    y = np.sin(phase)*np.exp(-t/.12)*onset(t,.003)
    noise = lowpass(RNG.normal(size=t.size), 1200)*np.exp(-t/.005)*.017
    return ((y+noise)*release(t,.48)).astype(np.float32)

def clap():
    t = np.arange(round(.20*SR))/SR
    noise = bandpass(RNG.normal(size=t.size), 1100, 7000)
    env = np.zeros_like(t)
    for start,gain in [(0,.7),(.010,.62),(.022,.8)]:
        u=np.maximum(t-start,0)
        env += (t>=start)*gain*np.exp(-u/.012)
    env += .22*np.exp(-t/.053)
    return (noise*env*onset(t,.0015)*release(t,.20,.025)).astype(np.float32)

def hat(opened=False):
    length = .18 if opened else .068
    t = np.arange(round(length*SR))/SR
    y = bandpass(RNG.normal(size=t.size), 6500, 15000)*.65
    for f in [7230,8110,10390]:y += .055*np.sin(2*np.pi*f*t)
    return (y*np.exp(-t/(.046 if opened else .017))*onset(t,.0007)*release(t,length,.013)).astype(np.float32)

def shaker():
    t=np.arange(round(.080*SR))/SR
    y=bandpass(RNG.normal(size=t.size),3000,10500)
    return (y*onset(t,.011)*np.exp(-t/.018)*release(t,.080,.025)).astype(np.float32)

def room_ir(seconds=1.25):
    size=round(seconds*SR);ir=np.zeros((size,2),np.float32)
    # Diffuse short stereo room, band-limited and with a finite, intentional tail.
    t=np.arange(size)/SR
    for channel in range(2):
        noise=lowpass(RNG.normal(size=size),6800)
        noise=bandpass(noise,350,6400)
        ir[:,channel]=noise*np.exp(-6.9*t/seconds)*smooth(t/.035)*smooth((seconds-t)/.08)
        for delay,g in [(.037,.09),(.063,.064),(.091,.043)]:
            ir[round((delay+channel*.006)*SR),channel]+=g
        ir[:,channel] /= max(1,np.sqrt(np.sum(ir[:,channel]**2))*5)
    return ir

def run(out, overwrite=False):
    names=['motif.wav','chords.wav','bass.wav','drums.wav','percussion.wav','premaster.wav','composition.json']
    existing=[name for name in names if (out/name).exists() or (out/name).is_symlink()]
    if existing and not overwrite:
        raise FileExistsError('Refusing to overwrite existing score files; choose a new output directory or pass --overwrite: '+', '.join(existing))
    out.mkdir(parents=True,exist_ok=True)
    stems={name:np.zeros((N,2),np.float32) for name in ['motif','chords','bass','drums','percussion']}
    events=[]
    def add(name, t, sound, gain, pan=0, **meta):
        if t>=LENGTH:return
        at=round(t*SR);l=min(len(sound),N-at)
        if sound.ndim==1:
            sound=np.stack([sound*np.sqrt((1-pan)/2),sound*np.sqrt((1+pan)/2)],axis=1)
        stems[name][at:at+l]+=sound[:l]*gain
        events.append({'stem':name,'time':round(t,6),'beat':round(t/BEAT,4),'gain':round(gain,5),**meta})

    # Smooth, closely voiced D major: colour from add9 and major7, never a big drop.
    harmony=[('Dmaj9',38,[62,66,69,73,76]),('Bm9',35,[62,66,69,73,78]),
             ('Gmaj9',31,[62,66,69,71,74]),('A6add9',33,[61,64,66,69,71])]
    for block in range(28):
        t=block*8*BEAT
        if t>=104:break
        name,root,notes=harmony[block%4]
        if t>=100:name,root,notes=harmony[3]
        if t<8:gain=.09
        elif t<54:gain=.145
        elif t<80:gain=.19
        elif t<87:gain=.155
        else:gain=.225
        length=min(8*BEAT+.8,212*BEAT-t+.35)
        add('chords',t,pad(notes,length,brightness=t>=54),gain,harmony=name)

    # Single two-bar hook. Changes are timbre/voicing/answer, not replacement melodies.
    hook=[(.5,78,.82),(1.25,81,.65),(2.5,76,.62),(3.25,78,.72),
          (4.5,74,.76),(6.25,76,.56),(7.0,69,.47)]
    for phrase in range(27):
        t=phrase*8*BEAT
        if t>=104:break
        for pos,note,velocity in hook:
            start=t+pos*BEAT
            if start>=104:continue
            g=.115 if start<8 else .145 if start<54 else .161 if start<80 else .090 if start<87 else .180
            pan=(-.08 if phrase%2==0 else .08)
            add('motif',start,pluck(note,shade=int(start>=54)),g*velocity,pan,note=note,motif='main')
            # Occasional lower octave colour, sparse and deliberately quieter.
            if 54<=start<80 and pos in [.5,4.5] or 87<=start<104 and pos in [.5,3.25,4.5]:
                add('motif',start,pluck(note-12,shade=-1),g*velocity*.28,-pan,note=note-12,motif='octave colour')

    kicks=kick();claps=clap();closed=hat();opened=hat(True);shakes=shaker()
    for b in range(212):
        t=b*BEAT;bar=b//4;pos=b%4
        if t<8:
            if pos in [0,2]:add('bass',t,bass(38,.16),.045,note=38,role='light pulse')
            continue
        if 80<=t<87:continue
        if t>=104:continue
        full=t>=87;warm=54<=t<80
        progression=(bar//2)%4;name,root,_=harmony[progression]
        if t>=100:name,root,_=harmony[3]
        k_gain=.25 if full else .218 if warm else .190
        add('drums',t,kicks,k_gain,instrument='rounded kick')
        if pos in [1,3] and t>=12:
            add('drums',t+.002,claps,.078 if full else .068 if warm else .057,instrument='restrained clap')
        if t>=10:
            # Subtle syncopation and tiny rests retain kick space. Fifth at phrase end.
            pitches=[root,root,root+12,root]
            if bar%4==3 and pos==3:pitches[pos]=root+7
            offsets=[.12,.5,.12,.5]
            add('bass',t+offsets[pos]*BEAT,bass(pitches[pos],(.56 if pos%2==0 else .34)*BEAT),
                .172 if full else .151 if warm else .132,note=pitches[pos],harmony=name)
        if t>=16:
            add('percussion',t+.5*BEAT,opened if pos==3 and warm or full and pos==3 else closed,
                .036 if full else .028 if warm else .020,pan=.20 if pos%2==0 else -.16,instrument='delicate hat')
        if warm or full:
            for sub in [.25,.75]:
                add('percussion',t+sub*BEAT,shakes,.020 if full else .016,
                    pan=-.30 if sub==.25 else .30,instrument='light shaker')
        # An occasional restrained ghost clap, no roll or riser.
        if (warm or full) and bar%4==3 and pos==3:
            add('percussion',t+.75*BEAT,claps,.018,pan=-.12,instrument='ghost clap')

    # True anticipation section: rhythmic motif and airy chord remain; drums/bass absent.
    # Final cadence lands at the first beat >=104 seconds, with 5.74 seconds to resolve.
    cadence=212*BEAT
    add('chords',cadence,pad([62,66,69,73,76],4.7),.24,harmony='Dmaj9 resolve')
    add('bass',cadence,bass(38,1.10),.12,note=38,role='cadence')
    add('motif',cadence,pluck(74,1.8),.17,note=74,motif='resolution D')
    add('motif',cadence+BEAT,pluck(78,1.8),.092,note=78,motif='resolution F#')

    axis=np.arange(N,dtype=np.float64)/SR
    # Every eight bars of the established groove: a half-bar thinning, then return.
    thins=[]
    for startbeat in [46,78]:
        start=startbeat*BEAT;end=(startbeat+2)*BEAT
        env=1-.67*smooth((axis-start)/.10)*(1-smooth((axis-(end-.12))/.24))
        for name in ['drums','bass','percussion']:stems[name]*=env[:,None]
        thins.append({'start':start,'end':end,'barsFromGrooveStart':(startbeat+2-16)/4})
    # Drum and bass pullback starts exactly at 80; reveal returns on beat177=87.049s.
    anticipation=1-smooth((axis-79.55)/.45)*(1-smooth((axis-87)/.05))
    for name in ['drums','bass','percussion']:stems[name]*=anticipation[:,None]
    # Bass / chord sidechain is gentle; never pump the entire music bed.
    phase=(axis/BEAT)%1
    duck=1-.11*np.exp(-phase/.15)
    stems['bass']*=duck[:,None];stems['chords']*=(.96+.04*(1-np.exp(-phase/.20)))[:,None]
    # Dotted-eighth stereo taps and a small diffuse room glue the motif to the pads.
    motif=stems['motif'].copy()
    for delay,g,swap in [(BEAT*.75,.20,True),(BEAT*1.5,.09,False)]:
        d=round(delay*SR)
        stems['motif'][d:]+=lowpass(motif[:-d,::-1] if swap else motif[:-d],5200)*g
    ir=room_ir()
    for name,send in [('motif',.38),('chords',.22),('percussion',.08)]:
        for c in range(2):stems[name][:,c]+=fftconvolve(stems[name][:,c],ir[:,c])[:N].astype(np.float32)*send
    # DC removal and a graceful final tail, not a fade over an ongoing groove.
    ending=1-smooth((axis-108.8)/1.2)
    beginning=smooth(axis/.025)
    mix=np.zeros((N,2),np.float32)
    stempaths=[]
    for name,y in stems.items():
        y=sosfilt(butter(2,22,fs=SR,btype='highpass',output='sos'),y,axis=0).astype(np.float32)
        y*=beginning[:,None]*ending[:,None]
        wavwrite(out/f'{name}.wav',SR,y);stempaths.append(f'{name}.wav');mix+=y
    wavwrite(out/'premaster.wav',SR,mix)
    manifest={'title':'Clear Space','creator':'Original local composition; authored and synthesized by Codex',
        'method':'deterministic note/event composition and synthesis; no model, samples or stock music',
        'bpm':BPM,'timeSignature':'4/4','durationSeconds':LENGTH,'sampleRate':SR,'key':'D major',
        'motif':hook,'harmony':[h[0] for h in harmony],'stems':stempaths,'events':events,
        'sections':[{'start':a,'end':b,'role':r} for a,b,r in [(0,8,'sparse opening'),(8,54,'steady groove'),
            (54,80,'warm layered development'),(80,87,'anticipation'),(87,104,'fullest same-theme reveal'),(104,110,'resolving cadence and tail')]],
        'phraseThinning':thins,'cadenceSeconds':cadence,'fullRevealBeatSeconds':177*BEAT,
        'premasterPeakDBFS':float(20*np.log10(np.max(np.abs(mix)))),'instrumental':True}
    (out/'composition.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k not in ['events','motif']},indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--overwrite',action='store_true',help='Replace existing generated score files deliberately');args=ap.parse_args();run(args.out,args.overwrite)
