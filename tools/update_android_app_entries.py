#!/usr/bin/env python3
"""Apply shared app metadata to hand-authored Android entry and normal guide pages."""
from pathlib import Path
import re
from android_slide_home_app import head_for,guide_for,CSS
from android_progress_transfer import HTML,JS
ROOT=Path(__file__).resolve().parent.parent

def strip_managed_head(text):
    return re.sub(r'<!-- android-home-app-assets -->.*?<!-- /android-home-app-assets -->','',text,flags=re.S)

def upsert(text,name,content,before):
    block='<!-- '+name+' -->'+content+'<!-- /'+name+' -->'
    pattern=r'<!-- '+re.escape(name)+r' -->.*?<!-- /'+re.escape(name)+r' -->'
    if re.search(pattern,text,re.S):return re.sub(pattern,lambda _:block,text,flags=re.S)
    assert before in text,(name,before)
    return text.replace(before,block+before,1)

def build():
    hub=ROOT/'android/index.html';s=hub.read_text().replace('<h3 id="android-slides-title">概要版スライド</h3>','<h3 id="android-slides-title">簡易版スライド</h3>').replace('<h3 id="android-deep-title">項目別・深掘り動画</h3>','<h3 id="android-deep-title">詳細版・深掘り動画</h3>')
    s=upsert(s,'android-home-app-assets',head_for('.',False)+'<style>'+CSS+'</style>','</head>')
    s=upsert(s,'android-home-install-guide',guide_for('.'),'<section aria-labelledby="formats-title">')
    s=upsert(s,'android-progress-transfer',HTML,'</main>')
    s=upsert(s,'android-progress-transfer-script','<script>'+JS+'</script>','</body>')
    # Legacy chapter links still work, but new page anchors such as home-install stay here.
    ids=re.findall(r'<section class="chapter" id="([^"]+)"',(ROOT/'android/guide/index.html').read_text())
    assert len(ids)>=30
    import json
    legacy='<script>if('+json.dumps(ids,separators=(',',':'))+'.includes(location.hash.slice(1))){const target=new URL("./guide/index.html",location.href);target.search=location.search;target.hash=location.hash;location.replace(target.href)}</script>'
    s=re.sub(r'<script>if\(location.hash\)\{const target=new URL\(\x27\./guide/index.html\x27,location.href\);.*?</script>',lambda _:legacy,s,flags=re.S)
    s=re.sub(r'<script>if\(\[.*?\.includes\(location.hash.slice\(1\)\)\).*?</script>',lambda _:legacy,s,flags=re.S)
    hub.write_text(s)
    guide=ROOT/'android/guide/index.html';g=guide.read_text()
    guide.write_text(upsert(g,'android-home-app-assets',head_for('..',False),'</head>'))
    print('Updated common Android entry, normal-guide metadata and legacy chapter handling.')
if __name__=='__main__':build()
