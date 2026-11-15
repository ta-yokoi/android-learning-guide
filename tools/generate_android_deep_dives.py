#!/usr/bin/env python3
"""Generate 30 separate, self-contained deep-dive players without modifying the overview."""
import html,json
from pathlib import Path
import generate_android_slides as base
from android_deep_courses import COURSES
from android_slide_diagrams import SVG
from android_slide_presentation import CASE_HTML,OPENING,RECAP,JS as DIRECTION_JS
from android_slide_fullscreen import JS as FULLSCREEN_JS
from android_slide_home_app import HEAD,GUIDE,JS as HOME_JS
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'android/deep-dives'
E=lambda s:html.escape(str(s),quote=True)
NAMES=['課題と前提','内部の仕組み','実装の焦点','失敗からの改善','観測と切り分け','理解度・総合演習']
ACCENTS=['#74d9ff','#c4f36b','#c6a5ff','#f7bd7b','#6de0c3','#c4f36b']
LAYERS={'layers','boot','overview'}
MATRICES={'power','network-security','aaos-detail','data-practice','test-lab','os-integration','capstone'}
SEQUENCES={'ipc','binder-practice','hardware-control'}
PIPELINES={'graphics','microphone','ethernet','adb-detail','build'}

EXTRA_CSS=r'''
.deep-course .opening-title{font-size:clamp(16px,4cqw,48px);max-width:90%}.deep-course .opening{gap:clamp(4px,1cqw,12px)}
.spotlight-story{width:100%;height:100%;display:block;position:relative;overflow:auto;border:1px solid #557783;border-radius:10px;background:#0b1d2a;padding:clamp(5px,1.3cqw,16px)}.spotlight-story .story-part{display:block;width:100%;margin:0 0 8px;padding:6px 9px;border-left:2px solid #3f5d6c;opacity:.62}.spotlight-story .story-part.focus{display:block;border-left-color:#c4ef9b;background:#203b4244;opacity:1}.story-heading{font-size:clamp(8px,1.1cqw,14px);color:#b5e8c8;margin:0 0 6px}.story-code{font:clamp(8px,1.45cqw,19px)/1.65 ui-monospace,SFMono-Regular,Consolas,monospace;color:#e8f4ed;white-space:pre-wrap;overflow-wrap:anywhere;margin:0;padding:0;background:transparent}.deep-detail{border-top:1px solid var(--line);padding-top:16px;margin-top:20px}.deep-detail h3{font-size:16px;margin:15px 0 8px}.deep-detail p,.deep-detail li{font-size:13px}.deep-detail pre{overflow:auto;padding:17px;background:#102433;border:1px solid #52717e;border-radius:8px;color:#e4f0eb;font:12px/1.7 ui-monospace,SFMono-Regular,Consolas,monospace;tab-size:4}.deep-detail code{white-space:pre}.deep-detail details{border-top:1px solid var(--line);padding:12px 0}.course-links{display:flex;gap:16px;flex-wrap:wrap}.static-diagram:has(.spotlight-story){height:auto;min-height:145px}.static-diagram .spotlight-story{display:grid;grid-template-columns:1fr 1fr;gap:12px}.static-diagram .story-part{display:block;opacity:1}.static-diagram .story-heading{font-size:11px}.static-diagram .story-code{font-size:10px}.deep-scope{border-left:3px solid var(--accent);padding-left:13px}.deep-scope p{margin:8px 0}.deep-exercise{border:1px solid var(--line);padding:12px;border-radius:8px}
@container(max-width:719px){.case-expanded .case-detail{display:none}}
@media print{.deep-detail pre{font-size:9px;line-height:1.4;white-space:pre-wrap;background:#f1f5f2;color:#183b30;padding:10px}.deep-detail code{white-space:pre-wrap;overflow-wrap:anywhere}.deep-detail p,.deep-detail li{font-size:10px}.deep-detail h3{font-size:13px;margin:7px 0}.deep-detail{margin-top:6px;padding-top:6px}.static-diagram .spotlight-story{background:#f6f9f6;border-color:#79968a;padding:8px}.static-diagram .story-code{color:#15362b;font-size:9px}.static-diagram .story-heading{color:#285c42}.fallback article{break-inside:auto}.deep-detail details{break-inside:avoid}.course-links{display:none}}
'''

def figure(c,unit,static=False):
    p=('static' if static else 'live')+'-'+c['id']+'-'+str(unit)
    if unit in (2,4):
        parts=[]
        for i,(label,value,_) in enumerate(c['code'] if unit==2 else c['observe']):
            parts.append(f'<section class="story-part role" data-step="{i}"><p class="story-heading">{i+1:02d} / {E(label)}</p><pre class="story-code">{E(value)}</pre></section>')
        return '<div class="spotlight-story" tabindex="0">'+''.join(parts)+'</div>','コードを段階ごとに追う' if unit==2 else '観測の手掛かりを段階ごとに追う'
    s=SVG(p)
    if unit==3:
        for i,(x,y) in enumerate([(25,22),(535,22),(25,151),(535,151)]):s.node(i,x,y,340,65,c['failure'][i][0],'state' if i>=2 else 'box')
        s.edge(0,'M365 55 H535','短絡した判断',450,42);s.edge(2,'M365 184 H535','根拠を確認',450,171)
        s.text(450,127,'上：失敗例 / 下：改善して再確認','region-label')
        return s.finish(),'比較図：失敗と改善の判断を対照する'
    if unit in (0,5):
        labels=['症状','前提','分ける軸','到達点'] if unit==0 else ['構造を説明','実装を判断','失敗を分類','証拠で検証']
        for i,(x,y) in enumerate([(25,20),(475,20),(25,145),(475,145)]):s.node(i,x,y,400,72,labels[i],'component')
        return s.finish(),'課題の整理' if unit==0 else '四つの問いで理解を確認する'
    labels=[x[0] for x in c['mechanism']]
    if c['id']=='lifecycle':
        for i,label in enumerate(labels):s.node(i,25,8+i*57,300,46,label,'component')
        for x,label in [(430,'構成変更'),(610,'プロセス終了'),(800,'再起動')]:s.text(x,25,label,'region-label')
        rows=[['×','×','×'],['○','×','×'],['△','△','△'],['○','○','○']]
        for i,row in enumerate(rows):
            for x,v in zip([430,610,800],row):s.text(x,60+i*48,v,'node-label')
        s.text(610,232,'○保持 / △条件付きで復元 / ×寿命を失う','region-label')
        return s.finish(),'寿命の対応表：保存データが残る前提、復元の条件は本文で確認'
    if c['id']=='audio':
        s.region(12,3,876,76,'CONTROL / 制御条件')
        s.node(0,240,30,420,46,'Focus・再生制御','component')
        for i,(x,label) in enumerate(zip([20,345,670],labels[1:]),1):s.node(i,x,144,210,74,label,'component')
        s.edge(0,'M450 77 V144','条件',506,118,True);s.edge(1,'M230 181 H345','PCM',284,168);s.edge(2,'M555 181 H670','出力',612,168)
        return s.finish(),'制御面と音声データの経路を分離する'
    if c['id'] in MATRICES:
        for i,(x,y) in enumerate([(25,22),(475,22),(25,147),(475,147)]):s.node(i,x,y,400,72,labels[i],'component')
        s.raw('<path class="divider" d="M450 25V220 M30 130H870"/>')
        return s.finish(),'別々に確認する責任・条件（番号は説明の順）'
    if c['id'] in LAYERS:
        for i,label in enumerate(labels):
            s.node(i,220,6+i*57,460,46,label,'component')
            if i<3:s.edge(i,f'M715 {29+i*57} V{86+i*57}')
        return s.finish(),'層と準備の境界を、役割ごとに追う'
    if c['id'] in SEQUENCES:
        for x,t in [(125,'呼出側'),(450,'契約・接続'),(775,'受け手')]:
            s.text(x,36,t,'node-label');s.raw(f'<path class="lifeline" d="M{x} 42V232"/>')
        for i,(a,b,y) in enumerate([(125,450,68),(450,775,112),(775,450,163),(775,125,216)]):s.edge(i,f'M{a} {y}H{b}',str(i+1)+' '+labels[i],(a+b)/2,y-10,i==3)
        return s.finish(),'要求・受け手・通知を分けて追う（簡略化）'
    if c['id'] in PIPELINES:
        for i,label in enumerate(labels):
            s.node(i,12+i*225,75,192,90,label,'device' if i==3 else 'component')
            if i<3:s.edge(i,f'M{204+i*225} 120 H{237+i*225}')
        s.text(450,217,'各境界の事実を同じ対象・時刻で照合','region-label')
        return s.finish(),'処理の経路と、それぞれの責任を確認する'
    if c['id'] in {'faults','investigation','first-app','bugreport-detail'}:
        s.region(10,5,875,230,'EVIDENCE / 操作と観測を対応づける')
        for i,(x,y) in enumerate([(30,50),(470,50),(30,153),(470,153)]):s.node(i,x,y,395,62,labels[i],'file')
        s.edge(0,'M425 81H470');s.edge(1,'M667 113V135H227V153','時刻で照合',452,137,True);s.edge(2,'M425 184H470')
        return s.finish(),'操作・対象・状態・時間を証拠で結ぶ'
    for i,(x,y) in enumerate([(20,20),(485,20),(485,153),(20,153)]):s.node(i,x,y,395,68,labels[i],'state')
    s.edge(0,'M415 54H485');s.edge(1,'M682 88V153');s.edge(2,'M485 187H415');s.edge(3,'M217 153V88','見直し',118,125,True)
    return s.finish(),'状態・観測・見直しの関係を追う'

def detail(c,unit,static=False):
    pre=f'<section class="deep-scope"><h3>この例の前提と範囲</h3><p>{E(c["scope"])}</p><p>コード・ログは説明用の断片です。Androidプロジェクトとしての単独実行や、端末での実測を示すものではありません。</p></section>'
    if unit==2:
        src='\n\n'.join(('// ' if not c['language'].startswith('Shell') else '# ')+label+'\n'+code for label,code,_ in c['code'])
        pre+=f'<h3>実装の断片 / {E(c["language"] + (' 1.9以上 / Android SDK・AndroidX等を前提' if c['language']=='Kotlin' else ''))}</h3><pre tabindex="0" role="region" aria-label="実装の断片"><code>{E(src)}</code></pre>'
    if unit==4:
        pre+='<h3>観測結果をどう読むか</h3><ol>'+''.join(f'<li><b>{E(label)}</b><pre tabindex="0"><code>{E(value)}</code></pre><p>{E(reason)}</p></li>' for label,value,reason in c['observe'])+'</ol><p>SERIALとPACKAGEは対象の値へ置き換えます。コマンドはこのページから実行されません。実行可否と出力は端末・権限・ビルドに依存します。</p>'
    if unit==5:
        pre+='<h3>総合演習：根拠を添えて答える</h3>'+''.join((f'<section><h4>Q{i+1}. {E(q)}</h4><p>{E(a)}</p></section>' if static else f'<details><summary>Q{i+1}. {E(q)}</summary><p>{E(a)}</p></details>') for i,(q,a) in enumerate(c['qa']))
        pre+='<p>手元の要件に合わせて状態・入力・期待する証拠を一組書いてください。製品条件を変えた時に何を再確認するかも残します。</p>'
    pre+='<h3>元の章と参考資料</h3><ul><li><a href="../../guide/index.html#'+E(c['id'])+'">通常教材の対応する章</a></li>'+''.join('<li><a href="'+E(url)+'">'+E(label)+'</a></li>' for url,label in c['refs'])+'</ul>'
    return '<div class="deep-detail">'+pre+'</div>'

def slides(c):
    out=[];m=c['mechanism'];co=c['code'];f=c['failure'];o=c['observe'];qa=c['qa']
    payloads=[
        [('症状',c['problem']),('前提','対象のOS・製品・権限をそろえ、本文に示す前提を確認する。'),('分離',m[0][1]),('到達点',c['goal'])],
        m,[(x[0],x[2]) for x in co],f,[(x[0],x[2]) for x in o],[(q,a) for q,a in qa],
    ]
    hooks=[qa[0][0],'役割と境界の違いを説明する','実装で守るべき条件は？',qa[2][0],'証拠から、どこまで言える？','条件が変わっても説明できる？']
    for unit,rows in enumerate(payloads):
        steps=[x[1] if unit!=5 else 'Q'+str(i+1)+'. '+x[0] for i,x in enumerate(rows)]
        nodes=[x[0] if len(x[0])<15 else '問い'+str(i+1) for i,x in enumerate(rows)]
        svg,label=figure(c,unit)
        values=(['症状を固定','前提を固定',m[0][0],'到達点を確認'] if unit==0 else [x[0] for x in rows])
        if unit==4:values=[x[0] for x in o]
        if unit==5:values=['Q'+str(i+1) for i in range(4)]
        frames=[dict(status=(['状況','前提','分離','目標'][i] if unit==0 else str(i+1)+'の観点'),value=v,detail=steps[i]) for i,v in enumerate(values)]
        q,a=qa[{0:0,1:0,2:1,3:2,4:3,5:3}[unit]]
        mod=unit//2+1
        out.append(dict(chapter=c['id'],title=NAMES[unit]+'｜'+c['title'],nodes=nodes,steps=steps,note=c['scope']+' '+c['problem'],question=q,answer=a,svg=svg,diagramLabel=label,diagramType='deep-'+str(unit),detail=detail(c,unit),module=dict(name=c['title'],index=mod,accent=ACCENTS[unit]),direction=dict(hook=hooks[unit],takeaway=(c['goal'] if unit in (0,5) else rows[-1][1]),kind='terminal' if unit in (2,4) else 'check',label=NAMES[unit]+' / 説明用の例',frames=frames)))
    return out

def player(c):
    data=slides(c)
    static=[]
    for i,slide in enumerate(data):
        drawing,label=figure(c,i,True)
        static.append(f'<article id="static-slide-{i+1}"><p class="eyebrow">DEEP DIVE / {i+1} OF 6</p><h2>{E(slide["title"])}</h2><div class="static-diagram" role="img" aria-label="{E(label)}">{drawing}</div><ol>'+''.join('<li>'+E(t)+'</li>' for t in slide['steps'])+f'</ol><p class="lesson-conclusion">要点：{E(slide["direction"]["takeaway"])}</p>'+detail(c,i,True)+'</article>')
    modules=[dict(name=n,first=i*2,last=i*2+1,accent=ACCENTS[i*2]) for i,n in enumerate(['課題と仕組み','実装と失敗','調査と演習'])]
    script=base.JS.replace('STEP=6,DURATION=24','STEP=10,DURATION=40').replace('android-animated-slides-player-v1','android-deep-dive-'+c['id']+'-v1').replace('../guide/index.html#','../../guide/index.html#').replace('prepareCase(slide);','prepareCase(slide);$(\'deep-detail\').innerHTML=slide.detail;')
    script=script.replace('directCase(slide,s);', "directCase(slide,s);const story=$('diagram').querySelector('.spotlight-story');if(story){const part=story.querySelector('.focus');story.scrollTop=part?Math.max(0,part.offsetTop-8):0}")
    script=script.replace(' DATA.forEach', " $('deep-detail').addEventListener('toggle',e=>{if(e.target.tagName==='DETAILS'&&e.target.open)pause()},true);\n DATA.forEach",1)
    script=script.replace('__HOME_JS__',HOME_JS).replace('__FULLSCREEN_JS__',FULLSCREEN_JS).replace('__DIRECTION_JS__',DIRECTION_JS.replace('__MODULES__',json.dumps(modules,ensure_ascii=False))).replace('__DATA__',json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'))
    head=HEAD.replace('href="./manifest','href="../manifest').replace('href="./icons/','href="../../slides/icons/').replace('Android学習','Android深掘り')
    guide=GUIDE.replace('Android学習','Android深掘り').replace('この教材ページ','この講座ページ').replace('アイコンから起動します。','アイコンから起動し、講座を選びます。')
    opening=OPENING.replace('Androidを、<br><em>仕組み</em>で理解する。',E(c['title'])+'<br><em>狭く、深く。</em>').replace('32 LESSONS · 約13分','6 SCENES · 約4分')
    template=base.TEMPLATE.replace('<body>','<body class="deep-course">').replace('../guide/index.html','../../guide/index.html').replace('← Androidの教材一覧','← 深掘り講座一覧').replace('Androidの教材一覧へ戻る','深掘り講座一覧へ戻る').replace('<ol id="explanation"></ol>','<ol id="explanation"></ol><div id="deep-detail"></div>')
    template=template.replace('Androidを動く図で学ぶ｜スライド教材',E(c['title'])+'｜Android深掘り動画').replace('Androidを、<br>動く図で学ぶ。',E(c['title'])).replace('身近な疑問から、図と実例で仕組みを追う32レッスン。',E(c['goal'])).replace('標準速度で約13分','6場面・標準速度で約4分').replace('Android 16の30章を動く図と字幕で振り返る、16:9のスライド教材。全32枚、自動再生とスマートフォン全画面に対応。',E(c['title'])+'を、内部構造・実装・失敗例・調査・演習から深く学ぶ動画風HTML。')
    # Additional excerpt styling is included in the same self-contained document.
    return template.replace('__CSS__',base.CSS+EXTRA_CSS).replace('__FALLBACK__','\n'.join(static)).replace('__STEP_BUTTONS__',''.join(f'<button type="button" data-step="{i}" aria-label="説明{i+1}へ移動" aria-pressed="false">{i+1}</button>' for i in range(4))).replace('__JS__',script).replace('__CASE_HTML__',CASE_HTML).replace('__OPENING__',opening).replace('__RECAP__',RECAP).replace('__HOME_HEAD__',head).replace('__HOME_GUIDE__',guide)

def catalog():
    old=(ROOT/'android/index.html').read_text();head=old.split('<body>')[0].replace('</head>', '<style>'+base.HOME_CSS+'@media(display-mode:standalone){.home-install{display:none}}</style></head>')
    head=head.replace('Androidの教材｜教材ライブラリ','Android 項目別・深掘り動画｜教材ライブラリ').replace('</head>',HEAD.replace('href="./icons/','href="../slides/icons/').replace('Android学習','Android深掘り')+'</head>')
    cards=[]
    for i,c in enumerate(COURSES,1):
        cards.append(f'<article class="card" aria-labelledby="course-{c["id"]}"><div class="card-top"><span class="subject-icon" aria-hidden="true">{i:02d}</span><span class="category">DEEP DIVE / 4 MIN</span></div><h3 id="course-{c["id"]}">{E(c["title"])}</h3><p class="description">{E(c["problem"])}</p><p class="description"><b>到達点：</b>{E(c["goal"])}</p><div class="tags"><span class="tag">内部構造</span><span class="tag">実装と失敗例</span><span class="tag">調査・演習</span></div><div class="facts"><span>6場面・24段階</span><span>約4分・音声なし</span><span>確認問題4問</span></div><a class="open-guide" href="./{c["id"]}/index.html">この講座を開く<span aria-hidden="true">→</span></a><p style="font-size:12px;margin-bottom:0"><a href="../guide/index.html#{c["id"]}">元の章を読む</a></p></article>')
    return head+'''<body><a class="skip" href="#courses">講座一覧へ移動</a><header class="site-header"><div class="wrap header-inner"><a class="brand" href="../index.html">← Androidの教材一覧</a><a href="../slides/index.html">概要版スライド →</a></div></header><main class="wrap"><section class="hero"><div class="eyebrow">ANDROID / FOCUSED VIDEO LESSONS</div><h1>ひとつの項目を、<br>狭く、深く。</h1><p class="lead">概要を知った次は、設計と証拠を自分の言葉で。<br>30項目を、それぞれ独立した動画風スライドで学びます。</p></section>'''+GUIDE.replace('Android学習','Android深掘り').replace('この教材ページ','この講座一覧').replace('アイコンから起動します。','アイコンから起動し、講座を選びます。')+'''<aside class="reading-note"><p>各講座は「課題 → 内部構造 → 実装 → 失敗例 → 調査 → 演習」の6場面・約4分です。図と字幕で進み、コードと解説は停止して読めます。実機の計測動画ではなく説明用の図解で、コードは前提を伴う断片です。再生位置は講座ごとに保存します。</p></aside><section id="courses" aria-labelledby="courses-title"><div class="section-heading"><h2 id="courses-title">深掘り講座</h2><span class="count">30 講座 / 全約120分</span></div><div class="grid">'''+''.join(cards)+'''</div></section></main><footer class="site-footer"><div class="wrap"><a href="../index.html">← Androidの教材一覧</a><a href="../slides/index.html">概要版スライド</a></div></footer></body></html>'''

def build():
    expected={s['chapter'] for s in base.SLIDES[1:-1]};assert expected=={c['id'] for c in COURSES}
    OUT.mkdir(parents=True,exist_ok=True)
    for c in COURSES:
        target=OUT/c['id']/'index.html';target.parent.mkdir(parents=True,exist_ok=True);result=player(c)
        assert '__DATA__' not in result and '__HOME_' not in result and '__JS__' not in result
        target.write_text(result)
    (OUT/'index.html').write_text(catalog())
    manifest=json.loads((ROOT/'android/slides/manifest.webmanifest').read_text())
    manifest.update(id='/android-learning-guide/android/deep-dives/',name='Android 項目別・深掘り動画',short_name='Android深掘り',description='30項目の内部構造・実装・失敗例・調査を、独立した動画風スライドで深く学ぶ。')
    for icon in manifest['icons']:icon['src']='../slides/'+icon['src']
    (OUT/'manifest.webmanifest').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Generated 30 deep-dive courses / 180 scenes / 720 explanation steps / 120 unique questions.')
if __name__=='__main__':build()
