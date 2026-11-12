#!/usr/bin/env python3
"""Author the standalone, script-free Kinetic Observatory.

Run from any directory: python3 tools/generate_kinetic_observatory.py
Python's standard library is used only at authoring time. The HTML needs no build.
The numerical checks run before writing, and this script only writes its HTML.
"""
from itertools import product
from math import cos, sin, pi, sqrt, isclose
from pathlib import Path

TAU = 2 * pi
FRAMES = 96
VERTICES = list(product((-1, 1), repeat=4))
EDGES = [(a, b) for a in range(16) for b in range(a + 1, 16)
         if sum(x != y for x, y in zip(VERTICES[a], VERTICES[b])) == 1]


def rotate(v, a, b, angle):
    v = list(v)
    v[a], v[b] = v[a] * cos(angle) - v[b] * sin(angle), v[a] * sin(angle) + v[b] * cos(angle)
    return v


def project(vertex, phase):
    """Three coupled, periodic 4D rotations, then a finite 4D→3D projection."""
    t = TAU * phase
    v = rotate(vertex, 0, 3, t + .42)
    v = rotate(v, 1, 2, t + .31)
    v = rotate(v, 2, 3, 2 * t + .18)
    v = rotate(v, 0, 1, .22 * sin(t) - .24)
    scale = 67 * 3.8 / (3.8 - v[3])
    return tuple(x * scale for x in v[:3])


def edge_matrix(a, b):
    """A unit-width strip joins endpoints; matrix interpolation preserves joins.

    The first column is B−A, translation is A. The second column is a
    unit screen-plane perpendicular. No Euler-angle wrap can spin an edge.
    """
    dx, dy, dz = (b[i] - a[i] for i in range(3))
    h = sqrt(dx * dx + dy * dy)
    nx, ny = (-dy / h, dx / h) if h > 1e-9 else (0, 1)
    return (dx, dy, dz, 0, nx, ny, 0, 0, 0, 0, 1, 0, *a, 1)


def knot(t, strand):
    """A (2,3) torus knot, three close strands with different tube phases."""
    phi = strand * TAU / 3
    minor = 62 + 7 * cos(phi)
    radius = 178 + minor * cos(3 * t + .09 * sin(phi))
    return (radius * cos(2 * t), radius * sin(2 * t),
            minor * sin(3 * t + .09 * sin(phi)) + 7 * sin(phi))


def orbit(t, lane):
    xyz = (284 * cos(t), 284 * sin(t), 0)
    return rotate(rotate(xyz, 1, 2, .94 + lane * .56), 0, 1, -.34 + lane * 1.1)


def n(value):
    return f"{value:.4f}".rstrip("0").rstrip(".") if abs(value) > .00005 else "0"


def position(v):
    return "translate3d(" + ",".join(f"{n(x)}px" for x in v) + ")"


def matrix(v):
    return "matrix3d(" + ",".join(n(x) for x in v) + ")"


EDGE_COMPONENTS = (("dx", 0), ("dy", 1), ("dz", 2), ("nx", 4), ("ny", 5), ("ax", 12), ("ay", 13), ("az", 14))


def edge_properties(m):
    return ";".join(f"--k-{key}:{n(m[index])}" for key, index in EDGE_COMPONENTS)


def verify():
    assert len(VERTICES) == 16 and len(EDGES) == 32
    assert all(sum(i in pair for pair in EDGES) == 4 for i in range(16))
    for vertex in VERTICES:
        assert all(isclose(a, b, abs_tol=1e-9) for a, b in zip(project(vertex, 0), project(vertex, 1)))
    for frame in range(FRAMES + 1):
        points = [project(v, frame / FRAMES) for v in VERTICES]
        for ia, ib in EDGES:
            m = edge_matrix(points[ia], points[ib])
            assert all(isclose(m[12 + k], points[ia][k], abs_tol=1e-9) for k in range(3))
            assert all(isclose(m[12 + k] + m[k], points[ib][k], abs_tol=1e-9) for k in range(3))
            # Also validate the authored 4-decimal CSS, not only source precision.
            r = [float(n(x)) for x in m]
            assert max(abs(r[12 + k] + r[k] - points[ib][k]) for k in range(3)) < .00011
    for fn, count in ((knot, 3), (orbit, 2)):
        for lane in range(count):
            assert all(isclose(a, b, abs_tol=1e-9) for a, b in zip(fn(0, lane), fn(TAU, lane)))
    # Linear matrix interpolation joins the same interpolated vertex positions.
    for ia, ib in EDGES:
        p0 = [project(VERTICES[i], .25) for i in (ia, ib)]
        p1 = [project(VERTICES[i], .25 + 1 / FRAMES) for i in (ia, ib)]
        m0, m1 = edge_matrix(*p0), edge_matrix(*p1)
        f = .37
        mm = [x * (1 - f) + y * f for x, y in zip(m0, m1)]
        assert all(isclose(mm[12 + k] + mm[k], p0[1][k] * (1 - f) + p1[1][k] * f, abs_tol=1e-9) for k in range(3))


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

INTRO = """<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="544の光点、32本の辺。4次元の回転とトーラス結び目を、HTMLとCSSだけで描く光の構造体。"><title>Kinetic Observatory｜光の構造体</title><style>
/* Generated by tools/generate_kinetic_observatory.py. No runtime JavaScript. */
"""

BODY = """</style></head><body>
<a class="skip" href="#observatory">作品へ移動</a>
<header class="masthead wrap"><a class="brand" href="../index.html">教材ライブラリ</a><nav aria-label="ページの案内"><a href="../css-motion-gallery/index.html">動く作品集 ↗</a><a href="#structure">構造を読む</a></nav></header>
<main class="wrap"><section class="intro" aria-labelledby="title"><div><p class="eyebrow">光と幾何学の観測室　／　特別展示</p><h1 id="title">光の<span>構造体。</span></h1></div><p class="intro-copy"><strong>ほどける立方体。交差する光の流れ。</strong><br>4次元の回転を映した骨格に、結び目の軌道が寄り添う。<br>見えない次元の動きを、ひとつのHTMLに閉じ込めました。</p></section>
<p class="reduced-note">端末の「動きを減らす」設定に合わせて静止表示しています。視点と表示層は切り替えられます。</p>
<section class="observatory" id="observatory" aria-label="光の構造体の観測と操作">
<input class="control-input" type="checkbox" id="pause" aria-label="すべての動きを一時停止">
<input class="control-input" type="radio" name="view" id="view-oblique" aria-label="斜めから見る" checked>
<input class="control-input" type="radio" name="view" id="view-front" aria-label="正面から見る">
<input class="control-input" type="radio" name="layer" id="layer-all" aria-label="すべての層を表示" checked>
<input class="control-input" type="radio" name="layer" id="layer-core" aria-label="4次元の骨格だけを表示">
<input class="control-input" type="radio" name="layer" id="layer-flow" aria-label="結び目と軌道だけを表示">
<input class="control-input" type="checkbox" id="sparse" aria-label="粒子を間引いて表示を軽くする">
<div class="toolbar" aria-label="観測の設定"><div class="control-group" role="group" aria-label="視点"><span class="control-title">視点</span><label for="view-oblique">斜め</label><label for="view-front">正面</label></div><div class="control-group" role="group" aria-label="表示する層"><span class="control-title">表示層</span><label for="layer-all">すべて</label><label for="layer-core">骨格</label><label for="layer-flow">光の流れ</label></div><div class="control-group"><label for="sparse">粒子を間引く</label></div><label for="pause" class="pause-control"><span class="playing">Ⅱ　動きを止める</span><span class="resume">▷　動きを再開</span></label></div>
<div class="stage" role="img" aria-label="16頂点と32辺を持つ4次元超立方体の投影が、ゆっくり折り重なって見える。周囲を青緑と紫の3本の結び目状の光粒子流と、2本の傾いた軌道が巡る立体作品。視点と表示層は上の設定で変更できる。">
<div class="stage-meta" aria-hidden="true"><p>立体観測 01<small>四次元の骨格 × 三葉結び目</small></p><p class="right"><span class="live-mark motion"></span><span class="status-running">観測中</span><span class="status-paused">一時停止</span><span class="status-static">静止表示</span><small>544 光点 / 32 辺</small></p></div>
<div class="graticule" aria-hidden="true"></div>
<div class="viewport" aria-hidden="true"><div class="scale"><div class="camera"><div class="assembly motion">
"""

END = """</div></div></div></div>
<div class="legend" aria-hidden="true"><span>4次元の骨格</span><span>三葉結び目</span><span>傾斜した軌道</span></div><div class="axis-label" aria-hidden="true">4D → 3D → 2D<br>投影距離　3.8</div><div class="timeline" aria-hidden="true"><span>4次元回転</span><div class="timeline-track"><i class="timeline-cursor motion"></i></div><span>96 秒 / 周期</span></div>
</div><div class="caption"><p>視点を変える。骨格だけを取り出す。動きを止めて、交点の奥行きを眺める。</p><span class="serial">HTML + CSS　/　音声なし</span></div></section>
<section class="notes" id="structure" aria-label="作品をつくる三つの構造"><article><span class="note-number">01 / 骨格</span><h2>立方体の、その先へ。</h2><p>4つの座標がそれぞれ ±1 をとる、<strong>16頂点・32辺の超立方体</strong>。XW・YZ・ZW の平面で回し、4番目の座標 W を遠近法で3次元へ映します。つながりを保ったまま、内と外が入れ替わって見えます。</p><span class="formula">(x′, y′, z′) = 3.8 / (3.8 − w) · (x, y, z)</span></article><article><span class="note-number">02 / 流れ</span><h2>一周では、戻らない。</h2><p>大きく2周しながら、小さく3周。<strong>(2,3) トーラス結び目</strong>の近くを、3本・432点の流れが巡ります。わずかな太さの差と時間差が、撚り合わされた光の束をつくります。</p><span class="formula">r = R + a cos(3t)<br>(x, y, z) = (r cos(2t), r sin(2t), a sin(3t))</span></article><article><span class="note-number">03 / 奥行き</span><h2>異なる周期が、重なる。</h2><p>骨格は96秒、結び目の流れは36秒・42秒・48秒。周囲の96点は2本の軌道を55秒・71秒で巡ります。<strong>限定した角度の揺らぎ</strong>と遠近感を重ね、光が真横を向いて消えにくい視点を保ちます。</p><span class="formula">544 光点 + 32 辺<br>4次元の投影 → CSS の3次元空間 → 画面</span></article></section>
<details><summary>描画のしくみと、観測のヒント</summary><p>これは物理シミュレーションではなく、数式から事前計算した座標を CSS のキーフレームで補間する作品です。4次元の骨格は1周期を96区間に分けて記録しています。各辺は両端の座標から行列をつくるため、補間中も頂点と線の端が一致します。3次元の変形・遠近法・光点の明るさを組み合わせています。</p><p>すべての動きは「動きを止める」でその位置に停止します。Tab キーで操作へ移動し、チェックボックスは Space、視点と表示層のラジオボタンは矢印キーで切り替えられます。「粒子を間引く」は結び目と軌道の点を半分にして描画量を減らします。非表示の層と間引いた粒子も時間は進むため、表示を戻しても位相は途切れません。選択内容は保存しません。</p><p>JavaScript・外部画像・外部フォント・追加パッケージは使いません。この HTML を直接開くだけで鑑賞できます。作成時の数値計算だけに Python の標準ライブラリを使っています。リポジトリから <code>python3 tools/generate_kinetic_observatory.py</code> を実行すると、このページだけを再生成します。端末やブラウザによって動きの滑らかさは異なります。</p></details>
</main><footer class="footer wrap"><span>光の構造体　／　Kinetic Observatory</span><a href="../css-motion-gallery/index.html">9つの動く作品へ戻る ↗</a><a href="../index.html">教材一覧へ ↗</a></footer>
</body></html>
"""


def build():
    verify()
    css, core, particles, orbitals = [], [], [], []
    # CSS transform matrix interpolation decomposes into rotations/scales. Instead,
    # animate registered numeric components, then construct the matrix from them.
    # Both endpoint positions and the edge vector now interpolate linearly.
    for key, _ in EDGE_COMPONENTS:
        css.append(f'@property --k-{key}{{syntax:"<number>";inherits:false;initial-value:0}}')
    css.append('.edge{transform:matrix3d(var(--k-dx),var(--k-dy),var(--k-dz),0,var(--k-nx),var(--k-ny),0,0,0,0,1,0,var(--k-ax),var(--k-ay),var(--k-az),1)}')
    for i, (ia, ib) in enumerate(EDGES):
        name = f"edge-{i}"
        frames = []
        for frame in range(FRAMES + 1):
            phase = frame / FRAMES
            m = edge_matrix(project(VERTICES[ia], phase), project(VERTICES[ib], phase))
            frames.append(f"{n(phase * 100)}%{{{edge_properties(m)}}}")
        css.append(f"@keyframes {name}{{{''.join(frames)}}}")
        cls = "fourth" if VERTICES[ia][3] != VERTICES[ib][3] else ("outer" if VERTICES[ia][3] < 0 else "")
        rest = matrix(edge_matrix(project(VERTICES[ia], 0), project(VERTICES[ib], 0)))
        values = edge_properties(edge_matrix(project(VERTICES[ia], 0), project(VERTICES[ib], 0)))
        core.append(f'<i class="edge motion {cls}" style="--path:{name};--rest:{rest};{values}"></i>')
    for i, vertex in enumerate(VERTICES):
        name = f"vertex-{i}"
        frames = [f"{n(frame / FRAMES * 100)}%{{transform:{position(project(vertex, frame / FRAMES))}}}" for frame in range(FRAMES + 1)]
        css.append(f"@keyframes {name}{{{''.join(frames)}}}")
        core.append(f'<i class="vertex motion" style="--path:{name};--rest:{position(project(vertex, 0))}"></i>')
    for lane in range(3):
        name = f"knot-{lane}"
        duration = (36, 42, 48)[lane]
        color = ("#adf6d6", "#c5b0ff", "#80cbd5")[lane]
        frames = []
        for frame in range(145):
            p = frame / 144
            xyz = knot(TAU * p, lane)
            scale = .82 + .25 * (.5 + .5 * sin(TAU * p * 3))
            alpha = .40 + .48 * (.5 + .5 * cos(TAU * p * 2 - .8))
            frames.append(f"{n(p * 100)}%{{transform:{position(xyz)} scale({n(scale)});opacity:{n(alpha)}}}")
        css.append(f"@keyframes {name}{{{''.join(frames)}}}")
        for i in range(144):
            phase = i / 144
            size = 1.6 + ((i * 13 + lane * 7) % 19) / 12
            kind = "spark" if i % 18 == 0 else "fine" if i % 3 else ""
            extra = " secondary" if i % 2 else ""
            particles.append(f'<i class="particle motion {kind}{extra}" style="--path:{name};--duration:{duration}s;--delay:{n(-duration * phase)}s;--size:{n(size)}px;--color:{color};--rest:{position(knot(TAU * phase, lane))}"></i>')
    for lane in range(2):
        name = f"orbit-{lane}"
        duration = (55, 71)[lane]
        frames = []
        for frame in range(97):
            phase = frame / 96
            xyz = orbit(TAU * phase, lane)
            frames.append(f"{n(phase * 100)}%{{transform:{position(xyz)}}}")
        css.append(f"@keyframes {name}{{{''.join(frames)}}}")
        for i in range(48):
            phase = i / 48
            beacon = i % 24 == 0
            cls = "beacon" if beacon else "orbit-point"
            extra = " secondary" if i % 2 else ""
            orbitals.append(f'<i class="particle motion {cls}{extra}" style="--path:{name};--duration:{duration}s;--delay:{n(-duration * phase)}s;--size:{3.4 if beacon else 1.5}px;--color:{"#d9edce" if beacon else "#7199b4"};--alpha:{1 if beacon else .45};--rest:{position(orbit(TAU * phase, lane))}"></i>')
    html = (INTRO + BASE_CSS + "\n".join(css) + BODY +
            '<div class="core motion">\n' + "\n".join(core) + '</div>\n<div class="sheath motion">\n' +
            "\n".join(particles) + '</div>\n<div class="orbital">\n' + "\n".join(orbitals) + "</div>\n" + END)
    assert len(particles) + len(orbitals) + len(VERTICES) == 544
    assert "<script" not in html and "https://" not in html and "http://" not in html
    assert len(html.encode()) < 1_500_000
    target = Path(__file__).resolve().parent.parent / "kinetic-observatory" / "index.html"
    target.parent.mkdir(exist_ok=True)
    target.write_text(html, encoding="utf-8")
    print(f"Verified 16 vertices, 32 edges, exact joins, and periodic endpoints. Wrote {target} ({len(html.encode()):,} bytes).")


if __name__ == "__main__":
    build()
