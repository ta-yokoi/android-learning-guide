#!/usr/bin/env python3
"""Generate local installation icons and manifest using only the standard library.

Assets are committed; this tool is not required to view or install the course.
"""
import json, math, struct, zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent/'android'

def rounded(x,y,rx,ry,w,h,r):
    if not (rx<=x<=rx+w and ry<=y<=ry+h):return False
    cx=min(max(x,rx+r),rx+w-r);cy=min(max(y,ry+r),ry+h-r)
    return (x-cx)**2+(y-cy)**2<=r*r

def color(x,y):
    glow=max(0,1-math.hypot(x-370,y-100)/500)
    c=(int(10+8*glow),int(21+30*glow),int(33+28*glow))
    if rounded(x,y,150,80,212,352,30):c=(183,234,208)
    if rounded(x,y,156,86,200,340,25):c=(10,25,37)
    if rounded(x,y,168,117,176,268,15):c=(25,66,74)
    if rounded(x,y,231,100,50,6,3) or rounded(x,y,222,403,68,6,3):c=(196,243,107)
    if 223<=x<=310 and 196+(x-223)*51/87<=y<=298-(x-223)*51/87:c=(196,243,107)
    return c

def png(size):
    pixels=bytearray()
    for y in range(size):
        pixels.append(0)
        for x in range(size):
            samples=[color((x+dx)*512/size,(y+dy)*512/size) for dx,dy in ((.25,.25),(.75,.25),(.25,.75),(.75,.75))]
            pixels.extend(round(sum(c[i] for c in samples)/4) for i in range(3))
    def chunk(name,data):return struct.pack('>I',len(data))+name+data+struct.pack('>I',zlib.crc32(name+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',size,size,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(pixels,9))+chunk(b'IEND',b'')

def manifest_for(android_relative='.'):
    p=android_relative
    return {
        'id':'/android-learning-guide/android/','name':'Android教材','short_name':'Android教材',
        'description':'通常教材・簡易版スライド・詳細版の深掘り動画を一つの入口から選ぶ。',
        'lang':'ja','start_url':p+'/?source=homescreen','scope':p+'/',
        'display':'standalone','orientation':'any','background_color':'#0a1521','theme_color':'#0a1521',
        'icons':[{'src':p+'/slides/icons/icon-192.png','sizes':'192x192','type':'image/png','purpose':'any'},
                 {'src':p+'/slides/icons/icon-512.png','sizes':'512x512','type':'image/png','purpose':'any maskable'}],
    }

def build():
    icons=ROOT/'slides/icons';icons.mkdir(parents=True,exist_ok=True)
    for size,name in [(180,'apple-touch-icon.png'),(192,'icon-192.png'),(512,'icon-512.png')]:
        (icons/name).write_bytes(png(size))
    (ROOT/'manifest.webmanifest').write_text(json.dumps(manifest_for(),ensure_ascii=False,indent=2)+'\n')
    # Compatibility URLs for old installations; every manifest now describes the same app.
    for folder in ('slides','deep-dives'):
        (ROOT/folder/'manifest.webmanifest').write_text(json.dumps(manifest_for('..'),ensure_ascii=False,indent=2)+'\n')
    print('Generated common Android manifest, compatibility manifests and installation icons.')
if __name__=='__main__':build()
