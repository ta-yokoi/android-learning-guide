#!/usr/bin/env python3
"""Generate the standalone CSS-only particle sculpture. Python is authoring-only."""
from math import sin, cos, sqrt, pi, isfinite
from pathlib import Path
from functools import lru_cache
from particle_depth import projected, sample_depth
TAU=2*pi
COUNT=1440
LABELS=('球体','六弁花冠','トーラス','三葉結び目','メビウスの帯','二重らせん','星芒','立方体','五重結び目','四次元トーラス','絡み合う二重環','ローレンツ軌道')
@lru_cache(maxsize=1)
def lorenz_points():
    x,y,z=.1,0.,0.; out=[]
    def f(x,y,z): return (10*(y-x),x*(28-z)-y,x*y-8*z/3)
    for j in range(1000+COUNT*5):
        h=.008; a=f(x,y,z); b=f(*(v+h*d/2 for v,d in zip((x,y,z),a))); c=f(*(v+h*d/2 for v,d in zip((x,y,z),b))); d=f(*(v+h*t for v,t in zip((x,y,z),c)))
        x,y,z=(v+h*(aa+2*bb+2*cc+dd)/6 for v,aa,bb,cc,dd in zip((x,y,z),a,b,c,d))
        if j>=1000 and (j-1000)%5==0:out.append((x,y,z))
    centers=[(max(p[k] for p in out)+min(p[k] for p in out))/2 for k in range(3)]
    scale=240/max(sqrt(sum((v-c)**2 for v,c in zip(p,centers))) for p in out)
    return [tuple((v-c)*scale for v,c in zip(p,centers)) for p in out]
def poses(i):
    a=TAU*(i%80)/80; b=TAU*(i//80)/18
    y=1-2*(i+.5)/COUNT; phi=i*pi*(3-sqrt(5)); r=sqrt(1-y*y)
    sphere=(215*r*cos(phi),215*y,215*r*sin(phi))
    radius=153+68*cos(6*a)+22*cos(b)
    flower=(radius*cos(a),radius*sin(a),48*sin(b)+30*sin(6*a))
    radius=164+64*cos(b)
    torus=(radius*cos(a),radius*sin(a),64*sin(b))
    t=TAU*(i//6)/240; v=TAU*(i%6)/6
    radius=138+46*cos(3*t)+9*cos(v)
    knot=(radius*cos(2*t),radius*sin(2*t),46*sin(3*t)+9*sin(v))
    t=TAU*(i%240)/240; w=((i//240)/5-.5)*105
    mobius=((170+w*cos(t/2))*cos(t),(170+w*cos(t/2))*sin(t),w*sin(t/2))
    t=(i//2)/719; angle=t*TAU*3+(i%2)*pi
    helix=(100*cos(angle),(t-.5)*420,100*sin(angle))
    radius=115+115*((.5+.5*cos(8*a))**3)+18*cos(b)
    star=(radius*cos(a),radius*sin(a),60*sin(b)+30*cos(4*a))
    face=i//240; j=i%240; u=((j%20+.5)/20-.5)*290;v=((j//20+.5)/12-.5)*290
    cube=((145,u,v),(-145,u,v),(u,145,v),(u,-145,v),(u,v,145),(u,v,-145))[face]
    t=TAU*(i//6)/240; v=TAU*(i%6)/6
    radius=143+50*cos(5*t)+10*cos(v)
    cinquefoil=(radius*cos(2*t),radius*sin(2*t),50*sin(5*t)+10*sin(v))
    factor=100/(1-.60*sin(b))
    clifford=(factor*cos(a),factor*sin(a),factor*cos(b))
    lane=i%2; t=TAU*((i//2)%120)/120; v=TAU*(i//240)/6
    radius=139+12*cos(v)
    linked=((radius*cos(t)-65,radius*sin(t),12*sin(v)),(12*sin(v)+65,radius*cos(t),radius*sin(t)))[lane]
    return (sphere,flower,torus,knot,mobius,helix,star,cube,cinquefoil,clifford,linked,lorenz_points()[i])
def verify():
    pts=[poses(i) for i in range(COUNT)]
    for k in range(len(LABELS)):
        assert len({tuple(round(v,4) for v in p[k]) for p in pts})==COUNT
    assert all(isfinite(v) for p in pts for xyz in p for v in xyz)
    assert max(sqrt(sum(v*v for v in xyz)) for p in pts for xyz in p)<310
    return pts

BASE_CSS = r"""
:root{color-scheme:dark;--bg:#090f13;--ink:#edf2ee;--muted:#a1b2b2;--mint:#bef5d6;--lilac:#d1bbff;--line:#2b3a40;--mono:ui-monospace,SFMono-Regular,Consolas,monospace}
*{box-sizing:border-box}html{scroll-padding-top:24px}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.85 -apple-system,BlinkMacSystemFont,"Hiragino Kaku Gothic ProN","Yu Gothic",Meiryo,sans-serif}a{color:inherit;text-underline-offset:5px}a:hover{color:var(--mint)}:focus-visible{outline:3px solid var(--mint);outline-offset:5px}::selection{background:var(--mint);color:#102721}.wrap{width:min(1200px,calc(100% - 72px));margin:auto}.skip{position:absolute;top:-90px;left:20px;background:var(--mint);color:#102721;padding:12px;z-index:10}.skip:focus{top:12px}.masthead{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:24px 0;border-bottom:1px solid var(--line)}.brand{font-size:12px;text-decoration:none;display:flex;gap:12px;align-items:center}.brand:before{content:'';display:block;width:17px;height:17px;border:1px solid var(--mint);transform:rotate(45deg);box-shadow:inset 0 0 0 4px var(--bg);background:var(--mint)}nav{display:flex;gap:24px;font-size:11px;color:var(--muted)}nav a{text-decoration:none}.intro{display:grid;grid-template-columns:1.3fr 1fr;align-items:end;gap:40px;padding:52px 0 34px}.eyebrow{margin:0 0 13px;color:var(--mint);letter-spacing:.16em;font-size:10px}.eyebrow:before{content:'●';font-size:7px;margin-right:10px}h1{font-weight:500;font-size:clamp(38px,5vw,64px);letter-spacing:-.04em;line-height:1.25;margin:0}h1 span{color:var(--mint)}.intro-copy{max-width:390px;justify-self:end;color:var(--muted);font-size:12px;line-height:2.05;margin:0}.intro-copy strong{color:var(--ink);font-weight:500}.observatory{position:relative;border:1px solid var(--line);border-radius:16px;background:#0c151c;overflow:hidden}.control-input{position:absolute;width:1px;height:1px;margin:-1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}.toolbar{display:flex;flex-wrap:wrap;align-items:center;gap:16px 24px;padding:17px 23px;border-bottom:1px solid var(--line);background:#101b20}.control-group{display:flex;flex-wrap:wrap;align-items:center;gap:6px}.control-title{font-size:10px;color:var(--muted);margin-right:5px}.toolbar label{cursor:pointer;font-size:11px;line-height:1.5;padding:8px 11px;border:1px solid #3a4a50;border-radius:5px;color:#b6c6c9;user-select:none}.toolbar label:hover{border-color:#b8d9ce;color:#edf2ee}.toolbar .pause-control{margin-left:auto;color:var(--mint);border-color:#5c7c74;min-width:113px;text-align:center}.resume{display:none}#pause:checked~.toolbar .playing{display:none}#pause:checked~.toolbar .resume{display:inline}#pause:checked~.toolbar .pause-control{background:var(--mint);color:#15251f}#view-oblique:checked~.toolbar label[for=view-oblique],#view-front:checked~.toolbar label[for=view-front],#layer-all:checked~.toolbar label[for=layer-all],#layer-core:checked~.toolbar label[for=layer-core],#layer-flow:checked~.toolbar label[for=layer-flow],#sparse:checked~.toolbar label[for=sparse]{background:#d1ebdf;color:#142920;border-color:#d1ebdf}.control-input:focus-visible~.toolbar label{outline:none}#pause:focus-visible~.toolbar label[for=pause],#view-oblique:focus-visible~.toolbar label[for=view-oblique],#view-front:focus-visible~.toolbar label[for=view-front],#layer-all:focus-visible~.toolbar label[for=layer-all],#layer-core:focus-visible~.toolbar label[for=layer-core],#layer-flow:focus-visible~.toolbar label[for=layer-flow],#sparse:focus-visible~.toolbar label[for=sparse]{outline:3px solid var(--mint);outline-offset:4px}
.stage{position:relative;height:680px;overflow:hidden;isolation:isolate;background:radial-gradient(ellipse at 48% 47%,#18333b70,transparent 52%),radial-gradient(ellipse at 69% 40%,#37284b45,transparent 52%),#080f17}.stage:before{content:'';position:absolute;inset:0;background-image:linear-gradient(#aacad908 1px,transparent 1px),linear-gradient(90deg,#aacad908 1px,transparent 1px);background-size:56px 56px;mask-image:radial-gradient(ellipse,#000,transparent 75%)}.stage:after{content:'';position:absolute;width:380px;height:90px;left:calc(50% - 190px);bottom:45px;border-radius:50%;background:radial-gradient(ellipse,#8cf6db16,transparent 70%);animation:ground-light 12s ease-in-out infinite;pointer-events:none}.stage-meta{position:absolute;top:25px;left:27px;right:27px;display:flex;justify-content:space-between;gap:18px;z-index:2;pointer-events:none}.stage-meta p{margin:0;font:10px/1.8 var(--mono);letter-spacing:.12em;color:#b8cbc9}.stage-meta small{display:block;font:10px/1.8 -apple-system,BlinkMacSystemFont,"Yu Gothic",sans-serif;letter-spacing:.03em;color:#839a9f}.live-mark{display:inline-block;width:5px;height:5px;margin-right:8px;border-radius:50%;background:var(--mint);box-shadow:0 0 9px #a1ffc9;animation:signal 5s ease-in-out infinite}.stage-meta .right{text-align:right}.graticule{position:absolute;width:588px;height:588px;left:calc(50% - 294px);top:calc(48% - 294px);border:1px solid #b0d0da14;border-radius:50%;pointer-events:none}.graticule:before{content:'';position:absolute;inset:23px;border:1px dashed #b0d0da15;border-radius:50%}.graticule:after{content:'';position:absolute;inset:-17px;background:linear-gradient(#9db5c63d,#9db5c63d) center top/1px 8px no-repeat,linear-gradient(#9db5c63d,#9db5c63d) center bottom/1px 8px no-repeat,linear-gradient(#9db5c63d,#9db5c63d) left center/8px 1px no-repeat,linear-gradient(#9db5c63d,#9db5c63d) right center/8px 1px no-repeat}.viewport{position:absolute;left:50%;top:48%;width:0;height:0;perspective:1100px;perspective-origin:0 0;transform-style:preserve-3d}.scale,.camera,.assembly,.core,.sheath,.orbital{position:absolute;left:0;top:0;width:0;height:0;transform-style:preserve-3d}.scale{transform:scale(.97)}.camera{transform:rotateX(-17deg) rotateY(-17deg)}#view-front:checked~.stage .camera{transform:rotateX(0deg) rotateY(0deg)}.assembly{animation:precession 48s ease-in-out infinite}.core{animation:core-breathe 24s ease-in-out infinite}.sheath{transform:rotateZ(-24deg) rotateX(26deg);animation:sheath-tilt 48s ease-in-out infinite}.orbital{transform:rotateZ(8deg)}.particle,.vertex,.edge{position:absolute;left:0;top:0;display:block;backface-visibility:visible}.particle{width:var(--size,2.5px);height:var(--size,2.5px);margin:calc(var(--size,2.5px) / -2);border-radius:50%;background:currentColor;color:var(--color,#a4eddb);box-shadow:0 0 5px currentColor;animation:var(--path) var(--duration) linear infinite;animation-delay:var(--delay);transform:var(--rest);opacity:var(--alpha,.75)}.particle.fine{box-shadow:none}.particle.spark{border-radius:1px;box-shadow:0 0 9px currentColor,0 0 2px #fff}.particle.orbit-point{box-shadow:none;opacity:.45}.particle.beacon{box-shadow:0 0 12px currentColor;background:#f0fffa;opacity:1}.vertex{width:4px;height:4px;margin:-2px;border-radius:50%;background:#effff4;color:#e8fff6;box-shadow:0 0 8px #b9f5de;transform:var(--rest);animation:var(--path) 96s linear infinite}.vertex:nth-child(3n){width:5px;height:5px;margin:-2.5px;background:#e8dfff;box-shadow:0 0 10px #b6a8fa}.edge{width:1px;height:1.4px;margin-top:-.7px;transform-origin:0 50%;background:#ccffe6;opacity:.65;transform:var(--rest);animation:var(--path) 96s linear infinite}.edge.fourth{background:#c8a7ff;opacity:.8}.edge.outer{opacity:.42}.legend{position:absolute;left:27px;bottom:73px;display:grid;gap:8px;z-index:2;font-size:10px;color:#a7bcc0}.legend span:before{content:'';display:inline-block;width:15px;height:1px;vertical-align:middle;margin-right:8px;background:#a5f4d3}.legend span:nth-child(2):before{background:#d0adff}.legend span:nth-child(3):before{background:#7196b4}.axis-label{position:absolute;right:28px;bottom:75px;color:#789298;font:9px/2 var(--mono);text-align:right;letter-spacing:.08em}.timeline{position:absolute;left:27px;right:27px;bottom:22px;display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:16px;font:9px/1.7 var(--mono);color:#92a9ae}.timeline-track{height:1px;background:#46616d5e;position:relative}.timeline-track:before{content:'';position:absolute;inset:-3px 0;background:repeating-linear-gradient(90deg,#63838d88 0 1px,transparent 1px calc(100% / 24));pointer-events:none}.timeline-cursor{display:block;width:5px;height:5px;margin-top:-2px;border-radius:50%;background:#d0f4e2;box-shadow:0 0 8px #a6ffce;animation:timeline 96s linear infinite}.status-paused,.status-static{display:none}#pause:checked~.stage .status-running{display:none}#pause:checked~.stage .status-paused{display:inline}#pause:checked~.stage *,#pause:checked~.stage:before,#pause:checked~.stage:after,#pause:checked~.stage *:before,#pause:checked~.stage *:after{animation-play-state:paused!important}#layer-core:checked~.stage .sheath,#layer-core:checked~.stage .orbital,#layer-flow:checked~.stage .core{visibility:hidden}#layer-core:checked~.stage .legend span:not(:first-child),#layer-flow:checked~.stage .legend span:first-child{display:none}#sparse:checked~.stage .secondary{visibility:hidden}
@keyframes precession{0%,100%{transform:rotateZ(-8deg) rotateY(-8deg)}50%{transform:rotateZ(8deg) rotateY(13deg)}}@keyframes core-breathe{0%,100%{transform:scale3d(1,1,1)}50%{transform:scale3d(1.06,1.06,1.06)}}@keyframes sheath-tilt{0%,100%{transform:rotateZ(-24deg) rotateX(26deg)}50%{transform:rotateZ(-5deg) rotateX(40deg)}}@keyframes ground-light{50%{transform:scaleX(.74);opacity:.5}}@keyframes signal{50%{opacity:.35}}@keyframes timeline{to{transform:translateX(0);margin-left:calc(100% - 5px)}}
.caption{display:flex;justify-content:space-between;gap:20px;align-items:center;padding:17px 23px;border-top:1px solid var(--line)}.caption p{margin:0;color:var(--muted);font-size:11px}.caption .serial{font:10px/1.7 var(--mono);color:var(--mint);letter-spacing:.07em;white-space:nowrap}.reduced-note{display:none;padding:15px 20px;border:1px solid #57756e;border-radius:8px;font-size:12px;color:var(--mint)}.notes{display:grid;grid-template-columns:1.15fr 1fr 1fr;gap:35px;margin:44px 0}.notes article{border-top:1px solid var(--line);padding-top:18px;min-width:0}.note-number{font:10px/1.5 var(--mono);color:var(--mint)}h2{font-size:16px;font-weight:500;margin:9px 0 13px}.notes p{font-size:12px;color:var(--muted);line-height:2.05;margin:0}.notes strong{color:#d3e2de;font-weight:500}.formula{display:block;font:10px/1.9 var(--mono);color:#c5bedf;margin-top:14px;overflow-wrap:anywhere}details{border:1px solid var(--line);border-radius:9px;padding:16px 20px;margin:0 0 36px}summary{cursor:pointer;font-size:12px;color:#cfe0db}details p{font-size:12px;color:var(--muted);line-height:2}details code{font:11px/1.6 var(--mono);color:var(--mint);overflow-wrap:anywhere}.footer{display:flex;justify-content:space-between;gap:24px;flex-wrap:wrap;border-top:1px solid var(--line);padding:23px 0 32px;color:#8fa4a7;font-size:10px}.footer a{text-decoration:none}
@media(max-width:1000px){.toolbar{gap:12px}.toolbar .pause-control{margin-left:0}.stage{height:610px}.scale{transform:scale(.84)}.graticule{transform:scale(.87)}.legend{bottom:65px}.axis-label{bottom:65px}.notes{gap:24px}.wrap{width:calc(100% - 48px)}}
@media(max-width:650px){.particle{width:calc(var(--size,2.5px) * 1.3);height:calc(var(--size,2.5px) * 1.3);margin:calc(var(--size,2.5px) * -.65)}.wrap{width:calc(100% - 30px)}.masthead{padding:20px 0;align-items:flex-start;gap:15px}.brand{font-size:11px}nav{font-size:10px;gap:15px}.intro{grid-template-columns:1fr;gap:20px;padding:35px 0 27px}.intro-copy{justify-self:start;max-width:100%;font-size:12px}.intro-copy br{display:none}h1{font-size:44px}.eyebrow{font-size:9px}.toolbar{padding:15px 13px;gap:12px 14px}.control-title{width:100%;margin-bottom:2px}.toolbar label{padding:7px 9px;font-size:10px}.toolbar .pause-control{margin-left:auto;align-self:flex-end;min-width:106px}.stage{height:500px}.scale{transform:scale(.60)}.graticule{transform:scale(.63)}.stage-meta{left:16px;right:16px;top:19px}.stage-meta p{font-size:9px}.stage-meta small{font-size:9px}.stage-meta .right{max-width:110px}.legend{left:16px;bottom:62px;font-size:9px;gap:4px}.axis-label{right:16px;bottom:62px;font-size:8px}.timeline{left:16px;right:16px;gap:12px;font-size:8px}.caption{padding:14px 16px;align-items:flex-start}.caption p{font-size:10px}.caption .serial{font-size:8px}.notes{grid-template-columns:1fr;gap:22px;margin:30px 0}.notes h2{margin:5px 0 8px}.notes p{font-size:12px}.formula{margin-top:10px}.footer{padding-bottom:25px}.stage:after{width:240px;left:calc(50% - 120px);bottom:60px}}
@media(max-width:420px){.stage{height:440px}.scale{transform:scale(.48)}.graticule{transform:scale(.50)}.stage-meta .right{max-width:96px}.axis-label{display:none}.legend{grid-template-columns:auto auto;column-gap:14px;bottom:62px}.legend span:last-child{display:none}.caption{gap:12px}.caption .serial{display:none}.toolbar .pause-control{margin-left:0}.toolbar{gap:12px 10px}.control-group{gap:4px}.intro h1{font-size:40px}}
@media(max-width:350px){.scale{transform:scale(.405)}.graticule{transform:scale(.43)}.stage{height:410px}.stage-meta small{max-width:130px}.stage-meta .right small{max-width:80px}.toolbar{gap:11px 14px}.toolbar .pause-control{margin-left:auto}.toolbar label{padding:7px 8px}.intro h1{font-size:36px}.masthead{gap:10px}nav{gap:10px}.brand{font-size:10px}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}.assembly{transform:rotateZ(-8deg) rotateY(-8deg)}.reduced-note{display:block}.pause-control,#pause{display:none}.status-running,.status-paused{display:none!important}.status-static{display:inline}.timeline-cursor{display:none}.particle{transform:var(--rest);opacity:var(--alpha,.75)}.vertex,.edge{transform:var(--rest)}}
@media print{:root{color-scheme:light;--bg:white;--ink:#1b3032;--muted:#42595e;--line:#aab9b8;--mint:#275f4d}body{background:white;color:#1b3032}.wrap{width:100%}.masthead,.toolbar,.skip,.footer,.reduced-note{display:none}.intro{padding:10px 0 20px;gap:20px}.intro h1{font-size:36px}.intro-copy{font-size:10px}.observatory{border:1px solid #abb9bc;border-radius:0;break-inside:avoid;background:#f5f9fa}.stage{height:450px;background:#eef4f5!important;print-color-adjust:exact;-webkit-print-color-adjust:exact}.stage:before,.stage:after,.graticule{display:none}.scale{transform:scale(.64)}*,*:before,*:after{animation:none!important;transition:none!important}.assembly{transform:rotateZ(-8deg) rotateY(-8deg)}.particle{transform:var(--rest);color:#396f6b!important;box-shadow:none;opacity:.65}.vertex{transform:var(--rest);background:#213e52;box-shadow:none}.edge{transform:var(--rest);background:#38666b;opacity:.7}.edge.fourth{background:#795991}.stage-meta p,.stage-meta small,.legend,.axis-label,.timeline{color:#42606a}.legend span:before{background:#38666b!important}.status-running,.status-paused{display:none!important}.status-static{display:inline}.live-mark,.timeline-cursor{display:none}.caption{background:white;padding:10px 14px}.caption p,.caption .serial{color:#36574f}.notes{margin:20px 0;gap:22px;break-inside:avoid}.notes strong{color:#274c43}.formula{color:#5b457b}.notes p{font-size:10px}details{display:none}}
"""
PARTICLE_CSS = r"""
/* The sculpture contains only circular light particles. */
.stage{height:680px;background:radial-gradient(ellipse at center,#14243d,#060b15 72%)}
.stage:before,.stage:after{display:none!important}.viewport{top:46%}.assembly{animation:particle-camera 12s linear infinite}.sheath{animation:none;transform:none}
.particle{width:var(--size);height:var(--size);margin:calc(var(--size) / -2);border-radius:50%;background:radial-gradient(circle at 35% 30%,#fff 0 12%,currentColor 52%,transparent 80%);color:hsl(var(--hue) 95% 75%);box-shadow:0 0 6px currentColor;opacity:var(--alpha);animation:particle-morph 96s linear infinite;animation-delay:0s;transform:var(--rest)}
.particle.fine{box-shadow:0 0 3px currentColor}.particle.spark{border-radius:50%;box-shadow:0 0 9px currentColor}.phase-list{position:absolute;left:20px;right:20px;bottom:23px;display:grid;grid-template-columns:repeat(6,1fr);gap:8px;padding:0;margin:0;list-style:none}.phase-list li{text-align:center;font-size:10px;padding-top:8px;border-top:1px solid #34495e;color:#8096ac;animation:phase-active 96s linear infinite;animation-delay:var(--delay)}
@keyframes phase-active{0%,8.332%{color:#e0fff2;border-color:#9ef1d8}8.333333%,100%{color:#8096ac;border-color:#34495e}}
@keyframes particle-camera{0%{transform:rotateZ(0deg)}100%{transform:rotateZ(360deg)}}
@media(max-width:650px){.intro{padding:22px 0 18px;gap:10px}.intro-copy{font-size:11px;line-height:1.8}.masthead{padding:13px 0}.toolbar{padding:11px 12px;gap:8px}.control-title{width:auto}.stage{height:480px}.scale{transform:scale(.65)}.particle{width:calc(var(--size)*1.25);height:calc(var(--size)*1.25);margin:calc(var(--size)*-.625)}.phase-list{grid-template-columns:repeat(4,1fr);font-size:9px;row-gap:10px}.phase-list li{font-size:9px;padding-top:5px}.viewport{top:40%}}
@media(max-width:420px){.stage{height:450px}.scale{transform:scale(.54)}.intro h1{font-size:34px}.intro-copy{font-size:10px}.toolbar .pause-control{margin-left:auto}}
@media(max-width:350px){.scale{transform:scale(.44)}.stage{height:420px}.toolbar label{font-size:9px;padding:6px 7px}.control-title{display:none}}
@media(prefers-reduced-motion:reduce){.assembly{transform:rotateX(-8deg) rotateY(-20deg)}.particle{transform:var(--rest);opacity:var(--alpha)}.phase-list li{color:#8096ac;border-color:#34495e}.phase-list li:first-child{color:#e0fff2;border-color:#9ef1d8}}
@media print{.stage{height:450px}.scale{transform:scale(.65)}.assembly{transform:rotateX(-8deg) rotateY(-20deg)}.particle{transform:var(--rest);color:#335e75!important;box-shadow:none;background:currentColor}.phase-list li{color:#335e75!important;border-color:#aab9b8!important}.viewport{top:40%}}
"""
BODY = r"""<body><a class="skip" href="#observatory">作品へ移動</a>
<header class="masthead wrap"><a class="brand" href="../index.html">作品一覧</a><nav aria-label="ページの案内"><a href="../css-motion-gallery/index.html">動く作品集 ↗</a><a href="#structure">構造を読む</a></nav></header>
<main class="wrap"><section class="intro" aria-labelledby="title"><div><p class="eyebrow">PARTICLE MORPH / 光の粒子だけで描く</p><h1 id="title">光が、<span>かたちになる。</span></h1></div><p class="intro-copy">360個の光が、球から花冠へ、結び目かららせんへ。<br>回転する12の立体が、滑らかにつながる光の彫刻。</p></section>
<p class="reduced-note">「動きを減らす」設定に合わせて球体を静止表示しています。視点と粒子密度は切り替えられます。</p>
<section class="observatory" id="observatory" aria-label="光の粒子の観察と操作">
<input class="control-input" type="checkbox" id="pause" aria-label="すべての動きを一時停止">
<input class="control-input" type="radio" name="view" id="view-oblique" aria-label="斜めから見る" checked>
<input class="control-input" type="radio" name="view" id="view-front" aria-label="正面から見る">
<input class="control-input" type="checkbox" id="sparse" checked aria-label="軽量表示、180粒にする">
<div class="toolbar"><div class="control-group" role="group" aria-label="視点"><span class="control-title">視点</span><label for="view-oblique">斜め</label><label for="view-front">正面</label></div><label for="sparse">軽量表示（180粒）</label><label for="pause" class="pause-control"><span class="playing">Ⅱ 動きを止める</span><span class="resume">▷ 動きを再開</span></label></div>
<div class="stage" role="img" aria-label="360個の丸い光粒子が、球体、六弁花冠、トーラス、三葉結び目、メビウスの帯、二重らせん、星芒、立方体、五重結び目、四次元トーラス、絡み合う二重環、ローレンツ軌道へ96秒で変形する立体作品。">
<div class="stage-meta" aria-hidden="true"><p>PARTICLE SCULPTURE<small><span class="full-count">360 LIGHTS</span><span class="light-count">180 LIGHTS / LITE</span> / 12 FORMATIONS</small></p><p class="right"><span class="status-running">再生中</span><span class="status-paused">一時停止</span><span class="status-static">静止表示</span></p></div>
<div class="viewport" aria-hidden="true"><div class="scale"><div class="camera"><div class="assembly motion"><div class="sheath">__POINTS__</div></div></div></div></div>
<ol class="phase-list" aria-label="変形する12の形">__PHASES__</ol></div>
<div class="caption"><p>形を保つ間も12秒で1回転。約4秒ごとに、保持と滑らかな変形を交互に繰り返します。</p><span class="serial">HTML + CSS / 音声なし</span></div></section>
<section class="notes" id="structure" aria-label="動きのしくみ"><article><span class="note-number">01 / 形</span><h2>粒子だけで、12の立体。</h2><p>球体、六弁花冠、トーラス、三葉結び目、メビウスの帯、二重らせん、星芒、立方体。同じ360粒が、それぞれの数式で求めた位置へ移ります。メビウスの帯は半ひねりした曲面、結び目は太さを持つ閉じた軌道です。</p></article><article><span class="note-number">02 / 色と奥行き</span><h2>光の密度が、面をつくる。</h2><p>粒ごとの大きさ・色・明るさの違いと、前後の距離による遠近感で立体を見せます。全体は12秒で1回転し、奥行きの計算はHTML生成時に行います。視点からの奥行きに合わせて、手前は大きく濃く、奥は小さく薄く描きます。形どうしの粒子の対応を空間的に近づけ、加速と減速を滑らかにつなぎます。画面の前後への小さな揺れも重ねています。</p></article><article><span class="note-number">03 / 操作</span><h2>止めて、かたちを観察する。</h2><p>Tabで操作を選び、Spaceで停止や粒子密度を切り替えます。視点の選択は矢印キーでも操作できます。視点を切り替えると粒子は初期位相から再開します。間引いた粒子のアニメーションは停止し、戻すと初期位相から再開します。設定は保存しません。</p></article></section>
<details><summary>座標とアニメーションのしくみ</summary><p>12種類のXYZ座標を空間位置が近い粒どうしで対応づけ、形の保持と変形を滑らかな加減速で接続します。CSSの移動・拡縮・不透明度をアニメーションします。数式の計算は作成時にPython標準ライブラリで行い、閲覧時はHTML内のCSSだけで動作します。生成コマンドは <code>python3 tools/generate_kinetic_observatory.py</code> です。</p><p>端末の「動きを減らす」設定と印刷では球体を静止表示します。JavaScript・外部素材・追加パッケージは不要です。滑らかさは端末により異なります。</p></details>
</main><footer class="footer wrap"><span>Kinetic Observatory / Particle Morph</span><a href="../css-motion-gallery/index.html">9つの作品へ戻る ↗</a><a href="../index.html">作品一覧へ ↗</a></footer></body></html>"""
def matched_tracks(points):
    reference=[p[0] for p in points]; tracks=[[p] for p in reference];count=len(points)
    for stage in range(1,len(LABELS)):
        targets=[p[stage] for p in points]
        costs=[[sum((a-b)**2 for a,b in zip(source,target)) for target in targets] for source in reference]
        edges=sorted((costs[i][j],i,j) for i in range(count) for j in range(count))
        assignment=[-1]*count;used=set()
        for _,i,j in edges:
            if assignment[i]<0 and j not in used:assignment[i]=j;used.add(j)
        for _ in range(2):
            for i in range(count):
                for j in range(i):
                    a,b=assignment[i],assignment[j]
                    if costs[i][b]+costs[j][a]<costs[i][a]+costs[j][b]:assignment[i],assignment[j]=b,a
        assert len(set(assignment))==count
        for i,j in enumerate(assignment):tracks[i].append(targets[j])
    return tracks

def build():
    pts=matched_tracks(verify()[::4]);dots=[];css=[]
    for j,p in enumerate(pts):
        timeline=[]
        for k in range(len(LABELS)):
            timeline.extend([(k*100/len(LABELS),p[k],False),((k+.5)*100/len(LABELS),p[k],True)])
        timeline.append((100,p[0],False))
        rests=[]
        for suffix,front in (('',False),('-front',True)):
            frames=[]
            for percent,xyz,transition in timeline:
                x,y,z=projected(xyz,front);size,alpha=sample_depth(z)
                frames.append(f'{percent:.6f}%{{transform:translate3d({x:.3f}px,{y:.3f}px,{z:.3f}px) scale({size:.4f});opacity:{alpha:.4f};animation-timing-function:{"cubic-bezier(.45,0,.55,1)" if transition else "linear"}}}')
            assert frames[0].split('{',1)[1] == frames[-1].split('{',1)[1], 'Loop seam must match'
            css.append(f'@keyframes point-{j}{suffix}'+ '{'+''.join(frames)+'}')
            x,y,z=projected(p[0],front);size,alpha=sample_depth(z)
            rests.append(f'translate3d({x:.3f}px,{y:.3f}px,{z:.3f}px) scale({size:.4f})')
        dots.append(f'<i class="particle motion {"secondary" if j%2 else "fine"}" style="--path:point-{j};--front-path:point-{j}-front;--size:{3+(j%5)*.3}px;--hue:{175+j%60*1.4};--alpha:.7;--rest:{rests[0]};--front-rest:{rests[1]}"></i>')
    phases=''.join(f'<li class="motion" style="--delay:{-96+k*8 if k else 0}s">{name}</li>' for k,name in enumerate(LABELS))
    light='.camera{transform:none;animation:camera-sway 16s ease-in-out infinite}#view-front:checked~.stage .camera{animation:none;transform:none!important}.particle{animation-name:var(--path);width:calc(var(--size)*2.6);height:calc(var(--size)*2.6);margin:calc(var(--size)*-1.3);background:radial-gradient(circle,#fff 0 8%,currentColor 16% 27%,transparent 72%);box-shadow:none!important}#view-front:checked~.stage .particle{animation-name:var(--front-path);--rest:var(--front-rest)!important}#sparse:checked~.stage .secondary{display:none}'
    import re
    for original,alias in [('phase-active','phase-front'),('particle-camera','particle-camera-front')]:
        match=re.search(r'@keyframes '+original+r'\{.*?\}\}',PARTICLE_CSS)
        assert match
        css.append(match.group(0).replace('@keyframes '+original,'@keyframes '+alias))
    light+='#view-front:checked~.stage .phase-list li{animation-name:phase-front}#view-front:checked~.stage .assembly{animation-name:particle-camera-front}'
    light+='.light-count{display:none}#sparse:checked~.stage .light-count{display:inline}#sparse:checked~.stage .full-count{display:none}'
    light+='@keyframes camera-sway{0%,100%{transform:rotateY(-14deg) rotateX(-5deg)}50%{transform:rotateY(14deg) rotateX(5deg)}}@media(prefers-reduced-motion:reduce){.camera{transform:none}}@media print{.camera{transform:none}.particle{background:currentColor}}'
    html='<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Kinetic Observatory｜光の粒子の立体変形</title><style>'+BASE_CSS+PARTICLE_CSS+light+'\n'.join(css)+'</style></head>'+BODY.replace('__POINTS__','\n'.join(dots)).replace('__PHASES__',phases)
    target=Path(__file__).resolve().parent.parent/'works/kinetic-observatory/index.html';target.write_text(html)
    assert '@property' not in html and '<script' not in html
    print(f'Wrote {len(dots)} particles with literal native keyframes; {len(html.encode()):,} bytes.')
if __name__=='__main__': build()
