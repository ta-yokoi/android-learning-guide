#!/usr/bin/env python3
"""Author the standalone, script-free Kinetic Observatory.

Run from any directory: python3 tools/generate_kinetic_observatory.py
Python's standard library is used only at authoring time. The HTML needs no build.
The numerical checks run before writing, and this script only writes its HTML.
"""
from itertools import product
from math import cos, sin, pi, sqrt, isclose, isfinite
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


def shell_points(index):
    """Same material coordinates on a sphere, six-lobed tube, torus, star tube."""
    u = TAU * (index % 60) / 60
    v = TAU * (index // 60) / 12
    latitude = -pi * .46 + (index // 60 + .5) / 12 * pi * .92
    sphere = (204 * cos(latitude) * cos(u), 222 * cos(latitude) * sin(u), 204 * sin(latitude))
    radius = 152 + 73 * cos(6 * u) + 19 * cos(v)
    bloom = (radius * cos(u), radius * sin(u), 42 * sin(v) + 30 * sin(6 * u))
    radius = 194 + 44 * cos(v)
    torus = (radius * cos(u), radius * sin(u), 84 * sin(v))
    radius = 107 + 143 * ((.5 + .5 * cos(12 * u)) ** 3) + 18 * cos(v)
    star = (radius * cos(u), radius * sin(u), 64 * sin(v) + 32 * cos(6 * u))
    return sphere, bloom, torus, star


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
    shell = [shell_points(i) for i in range(720)]
    assert len(shell) == 720
    for phase in range(4):
        rounded = {tuple(n(x) for x in particle[phase]) for particle in shell}
        assert len(rounded) == 720, "Each authored point must remain individually placed."
    for particle in shell:
        for xyz in particle:
            assert all(isfinite(value) for value in xyz)
            assert sqrt(sum(value * value for value in xyz)) < 310
    # The CSS shares the same declaration block for 0%, 10%, and 100%:
    # position, hue, scale, and opacity cannot diverge at the loop boundary.
    assert '0%,10%,100%{transform:translate3d(var(--x0),var(--y0),var(--z0)) scale(.95);color:hsl(var(--hue) 100% 75%);opacity:.9}' in CINEMATIC_CSS
    assert 'animation:shell-morph 48s ease-in-out infinite;animation-delay:0s' in CINEMATIC_CSS
    assert all(max(sqrt(sum((a - b) ** 2 for a, b in zip(particle[phase], particle[(phase + 1) % 4]))) for particle in shell) > 100 for phase in range(4))


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

CINEMATIC_CSS = r"""
/* A luminous sculpture: planar leaves are siblings in a preserved 3D space. */
.intro{padding:34px 0 27px}.eyebrow{color:#8ef5e7}.stage{height:690px;background:radial-gradient(ellipse at 50% 46%,#235a6345,transparent 45%),radial-gradient(ellipse at 67% 51%,#b12e9d24,transparent 48%),radial-gradient(ellipse at 32% 48%,#156a982e,transparent 48%),#060b15}.stage:after{width:520px;left:calc(50% - 260px);height:130px;bottom:36px;background:radial-gradient(ellipse,#42eac32e,transparent 70%)}.stage-meta p{color:#d0e1e0}.stage-meta small{color:#92adb6}.graticule{border-color:#9acbdc16}.viewport{top:47%}.assembly{animation:sculpture-pose 48s ease-in-out infinite}.sheath{transform:none;animation:none}.core{animation:core-sculpture 48s ease-in-out infinite}.edge{height:1.7px;margin-top:-.85px;background:#93ffe4;opacity:.86;box-shadow:none}.edge.fourth{background:#f39aff;opacity:.92}.edge.outer{opacity:.58}.vertex{width:5px;height:5px;margin:-2.5px;background:#fff;box-shadow:0 0 5px #fff,0 0 15px #74fff3}.particle.shell-point{width:var(--size);height:var(--size);margin:calc(var(--size) / -2);background:radial-gradient(circle at 35% 30%,#fff 0 10%,currentColor 48%,transparent 75%);color:hsl(var(--hue) 100% 73%);box-shadow:0 0 6px currentColor;animation:shell-morph 48s ease-in-out infinite;animation-delay:0s;transform:var(--rest);opacity:.88}.particle.shell-point.fine{box-shadow:0 0 4px currentColor}.particle.shell-point.spark{box-shadow:0 0 8px currentColor,0 0 15px currentColor;border-radius:1px}.particle.orbit-point{opacity:.65;box-shadow:0 0 3px currentColor}.particle.beacon{box-shadow:0 0 8px #fff,0 0 22px currentColor}.petal-arm,.ribbon-set{position:absolute;left:0;top:0;width:0;height:0;transform-style:preserve-3d}.petal-arm{transform:rotateZ(var(--angle)) rotateY(var(--tilt)) translateZ(var(--depth));animation:petal-open 48s ease-in-out infinite}.petal{position:absolute;left:31px;top:-48px;width:221px;height:96px;border-radius:8% 85% 12% 85%;border:1.6px solid currentColor;color:var(--petal-color);background:radial-gradient(ellipse at 8% 50%,#fff7,transparent 26%),linear-gradient(155deg,transparent 12%,var(--wash) 45%,transparent 76%);box-shadow:0 0 13px var(--wash),inset 0 0 21px var(--wash);transform:rotateZ(-12deg);animation:petal-skin 48s ease-in-out infinite}.petal:before{content:'';position:absolute;inset:14px 20px;border-top:1px solid currentColor;border-radius:50%;transform:rotate(7deg);box-shadow:0 -3px 10px var(--wash)}.petal:after{content:'';position:absolute;inset:5px 15px;border-bottom:1px solid currentColor;border-radius:15% 80%;transform:rotate(-7deg);opacity:.62}.petal-arm:nth-child(2n) .petal{border-radius:85% 8% 85% 12%;transform:rotateZ(12deg)}.nucleus{position:absolute;left:-100px;top:-100px;width:200px;height:200px;border-radius:50%;background:radial-gradient(circle,#fff 0 2%,#c8fff5 3%,#73ffeeaa 6%,#29e5e44a 15%,#3379f42e 28%,#bb46e510 45%,transparent 65%);transform:translateZ(10px);animation:nucleus-breathe 48s ease-in-out infinite}.nucleus:before{content:'';position:absolute;inset:67px;border:1px solid #c9fff7ad;border-radius:50%;box-shadow:0 0 15px #4dffe88c,inset 0 0 13px #4dffe85c}.nucleus:after{content:'';position:absolute;left:10%;right:10%;top:49.5%;height:1px;background:linear-gradient(90deg,transparent,#9fffee,#fff,#e29aff,transparent);box-shadow:0 0 7px #9fffee;transform:rotate(-28deg)}.ribbon{position:absolute;left:-274px;top:-274px;width:548px;height:548px;border-radius:50%;border:1.5px solid #6fefe872;border-top:3px solid #caffed;border-bottom:2px solid #ff98e9;box-shadow:0 0 11px #39ffe830,inset 0 0 12px #49f1df20;background:conic-gradient(from 30deg,transparent 10%,#66ffe655 20%,transparent 31%,#ef74e744 57%,transparent 68%);mask-image:radial-gradient(circle,transparent 66%,#000 67%);transform:rotateX(var(--rx)) rotateY(var(--ry)) rotateZ(var(--rz));animation:ribbon-orbit 48s ease-in-out infinite}.ribbon:nth-child(2){width:570px;height:570px;left:-285px;top:-285px;border-top-color:#f7b9ff;border-bottom-color:#85faff}.ribbon:nth-child(3){width:590px;height:590px;left:-295px;top:-295px;border-top-color:#ffe4a2;border-bottom-color:#f19bc5;opacity:.7}.phase-list{position:absolute;bottom:49px;left:50%;transform:translateX(-50%);width:min(560px,calc(100% - 44px));display:grid;grid-template-columns:repeat(4,1fr);gap:10px;list-style:none;padding:0;margin:0;z-index:3}.phase-list li{padding:8px 0;border-top:1px solid #4c687b66;color:#8499ac;font-size:10px;letter-spacing:.07em;text-align:center;animation:phase-active 48s linear infinite;animation-delay:var(--phase-delay)}.phase-list b{font:9px/1 var(--mono);margin-right:7px;font-weight:400}.legend{bottom:112px;font-size:9px}.axis-label{bottom:112px}.timeline{bottom:22px}.timeline-cursor{animation-duration:48s}.caption p{font-size:11px}
@keyframes sculpture-pose{0%,100%{transform:rotateZ(-9deg) rotateY(-6deg)}25%,35%{transform:rotateZ(7deg) rotateY(12deg)}50%,60%{transform:rotateZ(-17deg) rotateY(-13deg) rotateX(21deg)}75%,85%{transform:rotateZ(9deg) rotateY(6deg)}}
@keyframes core-sculpture{0%,100%{transform:scale3d(.83,.83,.83)}25%,35%{transform:scale3d(.95,.95,.95)}50%,60%{transform:scale3d(.79,.79,.79)}75%,85%{transform:scale3d(.88,.88,.88)}}
@keyframes shell-morph{0%,10%,100%{transform:translate3d(var(--x0),var(--y0),var(--z0)) scale(.95);color:hsl(var(--hue) 100% 75%);opacity:.9}25%,35%{transform:translate3d(var(--x1),var(--y1),var(--z1)) scale(1.2);color:hsl(calc(var(--hue) + 24) 100% 77%);opacity:1}50%,60%{transform:translate3d(var(--x2),var(--y2),var(--z2)) scale(1.1);color:hsl(calc(var(--hue) - 18) 100% 75%);opacity:.88}75%,85%{transform:translate3d(var(--x3),var(--y3),var(--z3)) scale(.9);color:hsl(calc(var(--hue) + 42) 100% 79%);opacity:.8}}
@keyframes petal-open{0%,10%,100%{transform:rotateZ(var(--angle)) rotateY(var(--tilt)) translateZ(var(--depth)) scale(.84)}25%,35%{transform:rotateZ(calc(var(--angle) + 9deg)) rotateY(12deg) translateZ(var(--depth)) scale(1.06)}50%,60%{transform:rotateZ(calc(var(--angle) - 18deg)) rotateY(67deg) translateZ(calc(var(--depth) * .5)) scale(.94)}75%,85%{transform:rotateZ(var(--angle)) rotateY(-9deg) translateZ(var(--depth)) scale(1.12)}}
@keyframes petal-skin{0%,10%,100%{height:96px;top:-48px;opacity:.86}25%,35%{height:108px;top:-54px;opacity:.95}50%,60%{height:70px;top:-35px;opacity:.65}75%,85%{height:37px;top:-18.5px;opacity:.82}}
@keyframes nucleus-breathe{0%,100%{transform:translateZ(10px) scale(1)}25%,35%{transform:translateZ(10px) scale(1.3)}50%,60%{transform:translateZ(10px) scale(.85)}75%,85%{transform:translateZ(10px) scale(1.1)}}
@keyframes ribbon-orbit{0%,100%{transform:rotateX(var(--rx)) rotateY(var(--ry)) rotateZ(var(--rz))}50%{transform:rotateX(calc(var(--rx) - 14deg)) rotateY(calc(var(--ry) + 10deg)) rotateZ(calc(var(--rz) + 180deg))}}
@keyframes phase-active{0%,24.999%{color:#e2fff2;border-color:#8effdd;text-shadow:0 0 14px #64ffd35c}25%,100%{color:#8499ac;border-color:#4c687b66;text-shadow:none}}
@media(max-width:1000px){.stage{height:620px}.scale{transform:scale(.87)}}
@media(max-width:650px){.masthead{padding:13px 0}.intro{padding:22px 0 18px;gap:10px}.intro-copy{font-size:11px;line-height:1.8;max-width:350px}.eyebrow{margin-bottom:8px}.intro h1{font-size:36px}.toolbar{gap:8px 12px;padding:11px 12px}.control-title{width:auto;margin:0 4px 0 0}.toolbar label{padding:6px 8px}.toolbar .pause-control{min-width:102px}.stage{height:500px}.scale{transform:scale(.65)}.particle.shell-point{width:calc(var(--size) * 1.22);height:calc(var(--size) * 1.22);margin:calc(var(--size) * -.61)}.edge{height:2px;margin-top:-1px}.petal{border-width:2px}.ribbon{border-top-width:3.5px}.stage-meta{top:16px}.legend,.axis-label{display:none}.phase-list{bottom:48px;gap:7px;width:calc(100% - 32px)}.phase-list li{font-size:9px;letter-spacing:0}.phase-list b{display:block;margin:0 0 6px}.caption{padding:12px 14px}.caption p{font-size:10px}.stage:after{width:280px;left:calc(50% - 140px);bottom:55px}}
@media(max-width:420px){.stage{height:458px}.scale{transform:scale(.535)}.graticule{transform:scale(.55)}.intro-copy{font-size:10px}.intro h1{font-size:34px}.toolbar{gap:7px 10px}.control-group{gap:4px}.control-title{font-size:9px}.toolbar .pause-control{margin-left:auto}.stage-meta small{font-size:8px}.stage-meta p{font-size:8px}.particle.shell-point{width:calc(var(--size) * 1.3);height:calc(var(--size) * 1.3);margin:calc(var(--size) * -.65)}}
@media(max-width:350px){.scale{transform:scale(.445)}.stage{height:420px}.intro{padding-top:18px}.intro h1{font-size:32px}.toolbar{gap:7px 8px}.toolbar label{font-size:9px;padding:6px 7px}.control-title{display:none}.phase-list{gap:5px}.phase-list li{font-size:8px}.intro-copy{font-size:10px}}
@media(prefers-reduced-motion:reduce){.assembly{transform:rotateZ(-9deg) rotateY(-6deg)}.core{transform:scale3d(.83,.83,.83)}.petal-arm{transform:rotateZ(var(--angle)) rotateY(var(--tilt)) translateZ(var(--depth)) scale(.84)}.particle.shell-point{transform:var(--rest);opacity:.9}.phase-list li{color:#8499ac;border-color:#4c687b66}.phase-list li:first-child{color:#e2fff2;border-color:#8effdd}}
@media print{.stage{height:470px}.scale{transform:scale(.64)}.assembly{transform:rotateZ(-9deg) rotateY(-6deg)}.core{transform:scale3d(.83,.83,.83)}.particle.shell-point{transform:var(--rest);color:#336c74!important;box-shadow:none}.petal-arm{transform:rotateZ(var(--angle)) rotateY(var(--tilt)) translateZ(var(--depth)) scale(.84)}.petal{color:#666aa2;border-color:#666aa2;background:#bfcbef33;box-shadow:none}.nucleus{background:radial-gradient(circle,#81bcb944,transparent 55%)}.ribbon{border-color:#648d9c;box-shadow:none;background:none}.phase-list li{color:#42606a!important;border-color:#aab9b8!important;text-shadow:none!important}.phase-list li:first-child{border-color:#38666b!important}.edge{box-shadow:none}.intro{padding:10px 0 20px}.stage-meta p,.stage-meta small{color:#42606a}}
"""

INTRO = """<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="832の光点、12枚の結晶リブ、3本の光環。球殻・花冠・トーラス・星芒へ変わる、HTMLとCSSだけの立体彫刻。"><title>Kinetic Observatory｜光の構造体</title><style>
/* Generated by tools/generate_kinetic_observatory.py. No runtime JavaScript. */
"""

BODY = """</style></head><body>
<a class="skip" href="#observatory">作品へ移動</a>
<header class="masthead wrap"><a class="brand" href="../index.html">教材ライブラリ</a><nav aria-label="ページの案内"><a href="../css-motion-gallery/index.html">動く作品集 ↗</a><a href="#structure">構造を読む</a></nav></header>
<main class="wrap"><section class="intro" aria-labelledby="title"><div><p class="eyebrow">光と幾何学の観測室　／　特別展示</p><h1 id="title">光の<span>構造体。</span></h1></div><p class="intro-copy"><strong>結晶が咲く。光が、ほどける。</strong><br>4次元の骨格を包む、虹色の結晶と光の軌道。<br>48秒で姿を変える、ひとつのHTMLの光彫刻。</p></section>
<p class="reduced-note">端末の「動きを減らす」設定に合わせて静止表示しています。視点と表示層は切り替えられます。</p>
<section class="observatory" id="observatory" aria-label="光の構造体の観測と操作">
<input class="control-input" type="checkbox" id="pause" aria-label="すべての動きを一時停止">
<input class="control-input" type="radio" name="view" id="view-oblique" aria-label="斜めから見る" checked>
<input class="control-input" type="radio" name="view" id="view-front" aria-label="正面から見る">
<input class="control-input" type="radio" name="layer" id="layer-all" aria-label="すべての層を表示" checked>
<input class="control-input" type="radio" name="layer" id="layer-core" aria-label="4次元の骨格だけを表示">
<input class="control-input" type="radio" name="layer" id="layer-flow" aria-label="結晶と光の軌道だけを表示">
<input class="control-input" type="checkbox" id="sparse" aria-label="粒子を間引いて表示を軽くする">
<div class="toolbar" aria-label="観測の設定"><div class="control-group" role="group" aria-label="視点"><span class="control-title">視点</span><label for="view-oblique">斜め</label><label for="view-front">正面</label></div><div class="control-group" role="group" aria-label="表示する層"><span class="control-title">表示層</span><label for="layer-all">すべて</label><label for="layer-core">骨格</label><label for="layer-flow">光の流れ</label></div><div class="control-group"><label for="sparse">粒子を間引く</label></div><label for="pause" class="pause-control"><span class="playing">Ⅱ　動きを止める</span><span class="resume">▷　動きを再開</span></label></div>
<div class="stage" role="img" aria-label="4次元超立方体の骨格を、青緑・マゼンタ・琥珀色の720点の外殻と12枚の半透明の結晶リブが包む。球殻から六弁の花冠、トーラス、十二方向の星芒へ48秒で変形し、3本の光環と96点の軌道が重なる立体彫刻。視点と表示層は上の設定で変更できる。">
<div class="stage-meta" aria-hidden="true"><p>立体観測 01<small>四次元の骨格 × 光の結晶</small></p><p class="right"><span class="live-mark motion"></span><span class="status-running">観測中</span><span class="status-paused">一時停止</span><span class="status-static">静止表示</span><small>832 光点 / 12 結晶リブ</small></p></div>
<div class="graticule" aria-hidden="true"></div>
<div class="viewport" aria-hidden="true"><div class="scale"><div class="camera"><div class="assembly motion">
"""

END = """</div></div></div></div>
<div class="legend" aria-hidden="true"><span>4次元の骨格</span><span>結晶の外殻</span><span>3本の光環</span></div><div class="axis-label" aria-hidden="true">4D → 3D → 2D<br>投影距離　3.8</div><ol class="phase-list" aria-label="48秒の変形順序"><li class="motion" style="--phase-delay:0s"><b>01</b>結晶の蕾</li><li class="motion" style="--phase-delay:-36s"><b>02</b>光の花冠</li><li class="motion" style="--phase-delay:-24s"><b>03</b>環状の渦</li><li class="motion" style="--phase-delay:-12s"><b>04</b>星芒へほどける</li></ol><div class="timeline" aria-hidden="true"><span>変形の周期</span><div class="timeline-track"><i class="timeline-cursor motion"></i></div><span>48 秒 / 周期</span></div>
</div><div class="caption"><p>48秒の変奏。結晶が開き、光の環へほどけ、星芒を描いて再び集まる。</p><span class="serial">HTML + CSS　/　音声なし</span></div></section>
<section class="notes" id="structure" aria-label="作品をつくる三つの構造"><article><span class="note-number">01 / 骨格</span><h2>立方体の、その先へ。</h2><p>4つの座標がそれぞれ ±1 をとる、<strong>16頂点・32辺の超立方体</strong>。XW・YZ・ZW の平面で回し、4番目の座標 W を遠近法で3次元へ映します。つながりを保ったまま、内と外が入れ替わって見えます。</p><span class="formula">(x′, y′, z′) = 3.8 / (3.8 − w) · (x, y, z)</span></article><article><span class="note-number">02 / 外殻</span><h2>結晶から、花冠へ。</h2><p><strong>720点の曲面と12枚の結晶リブ</strong>が、球殻・六弁の花冠・トーラス・十二方向の星芒へ変形します。同じ光点を4つの数式上の位置に対応させ、形を約5秒ずつ保ちながら、48秒で巡ります。</p><span class="formula">花冠の半径：r = 152 + 73 cos(6u) + 19 cos(v)<br>トーラスの半径：r = 194 + 44 cos(v)</span></article><article><span class="note-number">03 / 光の層</span><h2>面と輪郭が、重なる。</h2><p>青緑、マゼンタ、琥珀。<strong>半透明の結晶面、発光する輪郭、3本の光環</strong>で奥行きを描きます。周囲の96点は55秒・71秒、中心の4次元骨格は96秒の独立した周期で動きます。全体の視点は限られた角度で揺れます。</p><span class="formula">832 光点 + 32 辺 + 12 結晶リブ + 3 光環<br>48秒の変形 × 異なる周期の軌道</span></article></section>
<details><summary>描画のしくみと、観測のヒント</summary><p>これは物理シミュレーションではなく、数式から事前計算した座標を CSS のキーフレームで補間する作品です。4次元の骨格は1周期を96区間に分けて記録しています。各辺は両端の座標から行列をつくるため、補間中も頂点と線の端が一致します。外殻の4形状は座標を事前計算し、結晶リブと光環はCSSの面・輪郭・静的グラデーションで描きます。3次元の変形・遠近法・光点の明るさを組み合わせています。</p><p>すべての動きは「動きを止める」でその位置に停止します。Tab キーで操作へ移動し、チェックボックスは Space、視点と表示層のラジオボタンは矢印キーで切り替えられます。「粒子を間引く」は外殻と軌道の点を半分にして描画量を減らします。非表示の層と間引いた粒子も時間は進むため、表示を戻しても位相は途切れません。選択内容は保存しません。</p><p>JavaScript・外部画像・外部フォント・追加パッケージは使いません。この HTML を直接開くだけで鑑賞できます。作成時の数値計算だけに Python の標準ライブラリを使っています。リポジトリから <code>python3 tools/generate_kinetic_observatory.py</code> を実行すると、このページだけを再生成します。端末やブラウザによって動きの滑らかさは異なります。</p></details>
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
    for i in range(720):
        formations = shell_points(i)
        coords = ';'.join(f'--{axis}{j}:{n(value)}px' for j, xyz in enumerate(formations) for axis, value in zip('xyz', xyz))
        size = 2.7 + ((i * 17) % 23) / 11
        hue = (168, 184, 200, 282, 310, 38)[(i % 60) // 10] + (i // 60) * 1.1
        kind = 'spark' if i % 19 == 0 else 'fine' if i % 3 else ''
        extra = ' secondary' if i % 2 else ''
        particles.append(f'<i class="particle shell-point motion {kind}{extra}" data-point="{i}" style="{coords};--size:{n(size)}px;--hue:{n(hue)};--rest:{position(formations[0])}"></i>')
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
            orbitals.append(f'<i class="particle motion {cls}{extra}" style="--path:{name};--duration:{duration}s;--delay:{n(-duration * phase)}s;--size:{4.8 if beacon else 2.1}px;--color:{"#fff0bb" if beacon else "#8de5ef"};--alpha:{1 if beacon else .45};--rest:{position(orbit(TAU * phase, lane))}"></i>')
    petals = []
    for i in range(12):
        color, wash = (("#78ffe4", "#3df5d83d"), ("#efa0ff", "#df57e43d"), ("#a2dfff", "#54bfff38"), ("#ffe0a5", "#ffc26b33"))[i % 4]
        petals.append(f'<div class="petal-arm motion" style="--angle:{i * 30}deg;--tilt:{22 + i % 3 * 14}deg;--depth:{(i % 3 - 1) * 48}px;--petal-color:{color};--wash:{wash}"><i class="petal motion"></i></div>')
    ribbons = ''.join(f'<i class="ribbon motion" style="--rx:{rx}deg;--ry:{ry}deg;--rz:{rz}deg"></i>' for rx, ry, rz in ((62, 12, -22), (-56, 32, 40), (28, -42, 20)))
    html = (INTRO + BASE_CSS + CINEMATIC_CSS + "\n".join(css) + BODY +
            '<div class="core motion"><i class="nucleus motion"></i>\n' + "\n".join(core) + '</div>\n<div class="sheath motion">\n' +
            "\n".join(petals) + "\n".join(particles) + '</div>\n<div class="orbital"><div class="ribbon-set">' + ribbons + '</div>\n' + "\n".join(orbitals) + "</div>\n" + END)
    assert len(particles) + len(orbitals) + len(VERTICES) == 832
    assert len(petals) == 12
    assert "<script" not in html and "https://" not in html and "http://" not in html
    assert len(html.encode()) < 1_500_000
    target = Path(__file__).resolve().parent.parent / "kinetic-observatory" / "index.html"
    target.parent.mkdir(exist_ok=True)
    target.write_text(html, encoding="utf-8")
    print(f"Verified 16 vertices, 32 edges, exact joins, and periodic endpoints. Wrote {target} ({len(html.encode()):,} bytes).")


if __name__ == "__main__":
    build()
