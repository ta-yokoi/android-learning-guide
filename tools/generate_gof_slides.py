#!/usr/bin/env python3
"""Build the self-contained GoF video-style course; viewing requires no build step."""
import html,json,re
from pathlib import Path
from xml.etree import ElementTree
import generate_android_slides as player
from android_progress_transfer import JS as TRANSFER_JS
from android_slide_narration import CONTROLS,SETTINGS
from android_slide_presentation import JS as DIRECTION_JS,CASE_HTML,OPENING,RECAP
from android_slide_fullscreen import JS as FULLSCREEN_JS
from android_slide_diagrams import SVG
from gof_video_patterns import PATTERNS
from gof_slide_diagrams import diagram,code_diagram
from gof_book_labs import LABS
from gof_book_sections import CSS as BOOK_CSS,READING_GUIDE,render_lab,lab_figure,update_guide

ROOT=Path(__file__).resolve().parent.parent
E=lambda value:html.escape(str(value),quote=True)
ACCENTS=['#b8e8d4','#c4ef9b','#7ed8ed','#c9b2ff','#f6cb8f','#8be2cb','#c4ef9b']
NAMES=['設計の見方','生成の5パターン','構造の7パターン','振る舞いの11パターン','似た設計の比較','注文通知の総合演習','学びの整理']

def plain(text):return html.unescape(re.sub('<[^>]+>','',text)).strip()

def sources():
    guide=(ROOT/'gof/guide/index.html').read_text()
    result={}
    for key,content in re.findall(r'<section class="chapter" id="([^"]+)"(.*?)(?=<section class="chapter"|<footer)',guide,re.S):
        content=content.split('<!-- GOF-BOOK-START -->')[0]
        codes=[plain(value) for value in re.findall(r'<pre[^>]*>(.*?)</pre>',content,re.S)]
        if key not in {p['id'] for p in PATTERNS}:continue
        assert len(codes)==3,(key,len(codes))
        qa=[(re.sub(r'^Q\d+\.\s*','',plain(q)),plain(a)) for q,a in re.findall(r'<details class="answer"><summary>(.*?)</summary><p>(.*?)</p></details>',content,re.S)]
        assert len(qa)==2,(key,qa)
        sections={plain(h):plain(body) for h,body in re.findall(r'<h3>([^<]*)</h3><p>(.*?)</p>',content,re.S)}
        result[key]=dict(before=codes[0],code=codes[1],output=codes[2],qa=qa,
            change=sections['変更に強くなった場所'],cost=sections['コスト・前提・使わない判断'],comparison=sections['似たパターンとの違い'])
    assert len(result)==23
    return result

def excerpt(code,marker):
    lines=code.splitlines();start=next(i for i,line in enumerate(lines) if marker in line)
    end=start;balance=0;opened=False
    for end in range(start,len(lines)):
        line=lines[end];balance+=line.count('{')-line.count('}');opened=opened or '{' in line
        if opened and balance<=0:break
    segment=lines[start:end+1];indent=min(len(x)-len(x.lstrip()) for x in segment if x.strip())
    return '\n'.join(x[indent:] for x in segment)

def detail(p,source):
    return '<section class="implementation"><h3>変化する場所と、採用の代償</h3>'+''.join('<p><b>'+label+'：</b>'+E(source[key])+'</p>' for label,key in [('変更への対応','change'),('コスト・使わない判断','cost'),('似たパターンとの違い','comparison')])+f'''<details class="java-full"><summary>適用前後の実行可能なJava 17コードを読む</summary><p>通常教材と同じ独立したMain.javaです。それぞれを別々に保存し、<code>javac --release 17 Main.java</code>、<code>java Main</code>で実行できます。ページ上のアニメーションはJavaを実行していません。</p><h4>適用前</h4><pre tabindex="0" role="region" aria-label="適用前のJavaコード"><code>{E(source['before'])}</code></pre><h4>適用後と使用例</h4><pre tabindex="0" role="region" aria-label="適用後のJavaコード"><code>{E(source['code'])}</code></pre><h4>適用後の実行結果</h4><pre tabindex="0" role="region" aria-label="実行結果"><code>{E(source['output'])}</code></pre></details><p class="scope-note">図は説明用です。矢印のラベルで呼出・参照・継承・状態遷移を区別します。時間・通信・例外・並行性を実行再現するシミュレーションではありません。主要例はJava単体で理解できます。</p></section>'''

def comparison_figure(nodes,prefix):
    s=SVG(prefix)
    for i,(x,y) in enumerate([(15,15),(475,15),(15,145),(475,145)]):s.node(i,x,y,405,77,nodes[i],'component')
    s.raw('<path class="divider" d="M450 10V230"/>')
    return s.finish(),'比較図：左と右の意図・変更点を対照する（矢印は呼出を表す場合だけ）'

def make_slide(chapter,title,nodes,steps,note,qa,module,kind='flow',svg=None,label=None,extra=''):
    index=module+1
    if svg is None:
        svg,label=comparison_figure(nodes,'extra-'+str(len(SLIDES)))
    frame_labels=['問題・契約','責任の分離','結果の確認','採用の判断'] if kind=='code' else ['着眼点','役割','処理','要点']
    frames=[dict(status=frame_labels[i],value=nodes[i],detail=steps[i]) for i in range(4)]
    return dict(chapter=chapter,title=title,nodes=nodes,steps=steps,note=note,question=qa[0],answer=qa[1],svg=svg,diagramLabel=label,diagramType='gof-'+kind,detail=extra,module=dict(index=index,name=NAMES[module],accent=ACCENTS[module]),direction=dict(hook=title,takeaway=steps[3],kind='terminal' if kind=='code' else 'check',label='Java 17 / 実装と出力' if kind=='code' else '役割と設計判断',frames=frames))

SLIDES=[]
def extra(chapter,title,nodes,steps,note,qa,module):
    SLIDES.append(make_slide(chapter,title,nodes,steps,note,qa,module))

def lessons():
    SLIDES.clear();data=sources()
    extra('start','名前より先に、困っている変更を探す',
      ['変更要求','単純な案','分ける責務','コストを比較'],
      ['デザインパターンは設計上の問題に対する考え方です。名前を当てるより、変更するとどこが壊れるかを説明するところから始めます。',
       'まず条件分岐や関数で十分か試します。将来の予想だけで部品を増やすと、読解やデバッグの負担が先に発生します。',
       '各パターンを、役割、Java、要件変更の検証実習の三場面で追います。実行前に予想し、反例から契約を見直す手順で学びます。',
       '図の動きは説明用の強調です。停止してコードと理由を読み、変更を受け止めやすくなる利益が追加の複雑さに見合うかを判断します。'],
      '79場面・316段階。字幕のみ1倍は42分08秒、読み上げ時は声の長さに合わせて進みます。基本コード、検証コード、詳説と実習問題は解説欄にあります。',
      ('使えそうなパターンを先にすべて入れると、よい設計になる？','なりません。具体的な変更と境界を決め、単純な案とのコストを比較します。'),0)
    extra('start','委譲と合成で、変更の境界を作る',
      ['凝集度','結合度','継承 / 合成','SOLID と判断'],
      ['凝集度は関連する責任がまとまっているかという観点です。クラスやメソッドが少なければ良い、という意味ではありません。',
       '結合度には型だけでなく、呼ぶ順序や寿命、例外の意味への依存も含まれます。インターフェースを作るだけでは切り離せません。',
       '継承は型の関係と差替え、合成は別の部品の保持、委譲はその部品へ処理を任せることです。変更の軸と契約に合わせて使い分けます。',
       'SOLIDは責任や拡張、置換、契約、依存の向きを考える原則です。パターンは手段の候補で、採用すれば原則を自動で満たすわけではありません。'],
      '矢印の先だけでなくラベルを読みます。実線の呼出、破線の参照・実装・制御復帰などを区別し、厳密なUMLとしては扱いません。',
      ('インターフェースに依存すれば、通知順や例外への依存もなくなる？','なくなりません。型以外の時間・順序・エラーの契約も設計とテストで確認します。'),0)
    for n,p in enumerate(PATTERNS):
        source=data[p['id']];mod=1 if n<5 else 2 if n<12 else 3
        drawing,label=diagram(p,'flow-'+p['id'])
        SLIDES.append(make_slide(p['id'],p['name']+'｜役割と処理を追う',p['nodes'],p['flow'],source['change']+' '+source['cost'],source['qa'][0],mod,svg=drawing,label=label))
        parts=[('契約・境界',excerpt(source['code'],p['markers'][0])),('差替え・委譲の実装',excerpt(source['code'],p['markers'][1])),('使用例',excerpt(source['code'],'public static void main')),('実行結果',source['output'])]
        steps=p['code_steps'];nodes=['契約と境界','実装の責任','使用例と出力','コストと採否']
        slide=make_slide(p['id'],p['name']+'｜Javaと採用判断',nodes,steps,'コードは通常教材のJava 17の例と一致します。'+source['comparison'],source['qa'][1],mod,'code',code_diagram(parts,'code-'+p['id']),'実装の抜粋：全文・適用前・出力は下の解説欄へ',detail(p,source))
        slide['direction']['frames']=[dict(status=['契約','実装','使用','判断'][i],value=[p['markers'][0],p['markers'][1],'Main.main → 出力','増える型と責任を評価'][i],detail=steps[i]) for i in range(4)]
        SLIDES.append(slide)
        lab=LABS[p['id']]
        steps=[lab['requirement'],lab['contract'],*lab['reading']]
        tested=make_slide(p['id'],p['name']+'｜'+lab['title'],['追加要求','予想と契約','出力の照合','代案の比較'],steps,
            '実行前に結果を予想し、解説欄の独立したMain.javaと標準出力で照合します。'+lab['contract'],lab['questions'][0],mod,
            'lab',lab_figure(lab),'検証実習：要求 → 予想 → 出力 → 設計判断',render_lab(p,source))
        tested['reference']='../guide/index.html#lab-'+p['id']
        tested['direction']['frames']=[dict(status=['要求','契約','観測','採否'][i],value=['変わった前提を固定','結果を先に予想','出力と理由を照合','二つの設計案を比較'][i],detail=steps[i]) for i in range(4)]
        SLIDES.append(tested)
    extra('comparison','Abstract Factory と Factory Method',
      ['Abstract Factory','Factory Method','製品群の整合','継承の生成フック'],
      ['Abstract Factoryでは、ボタンとチェックのような関連製品を、一組としてそろえる問題に着目します。',
       'Factory Methodでは、共通の手順から呼ぶ生成操作を、サブクラスへ任せる問題に着目します。',
       '製品群の整合性が重要なら工場の契約を検討します。ただし新しい製品の種類が増える場合、全工場への影響があります。',
       '継承による生成の差替えが必要なら生成フックを検討します。両者は併用できますが、static生成関数という名前だけではFactory Methodとは判断できません。'],
      '左は製品群、右は生成フックの差替えです。関連する通常教材の二章も比べてください。',
      ('ボタンとチェックを同じテーマにそろえる主な候補は？','Abstract Factoryです。共通の処理の一部で生成を上書きするか、製品群の整合を保つかで判断します。'),4)
    extra('comparison','Bridge と Adapter',
      ['Bridge','Adapter','二つの変化軸','既存の契約差'],
      ['Bridgeは通知の種類と送信経路など、独立して増える二つの変化軸を初めから分けます。',
       'Adapterは利用側のsendと既存部品のpostのように、すでにある契約の違いを境界で吸収します。',
       'Bridgeでは両側を独立に拡張できることが利益です。一方の軸が固定なら、分離が過剰になるかもしれません。',
       'Adapterでは名前だけでなく例外や単位、同期性も合わせます。どちらも委譲を使えますが、見た目が似ていることではなく導入する問題で選びます。'],
      '役割の数ではなく、二つの軸を分けるのか、既存契約を合わせるのかを説明します。',
      ('既存SDKのpostを、自アプリのsendとして使いたい場合は？','Adapterが候補です。二つの製品軸を独立に拡張する問題ならBridgeを検討します。'),4)
    extra('comparison','Decorator と Proxy',
      ['Decorator','Proxy','責務を重ねる','アクセスを制御'],
      ['Decoratorは同じ契約で包み、ログや変換などの責務を組み合わせます。順序も結果の一部になります。',
       'Proxyは実体へのアクセスを制御します。文書の遅延読込、権限検査、遠隔の代理などが候補です。',
       'ログを変換の外へ置くか内へ置くかで、記録する文字列が変わります。順序や例外の通り方も契約に含めます。',
       '同じ契約で実体を保持する構造だけでは分類できません。責務を増やしたいのか、アクセスの条件を管理したいのかを先に述べます。'],
      '同じ構造が異なる意図を持つ場合があります。実装の名前だけで判断しません。',
      ('重い文書を最初のreadまで生成しないラッパーは？','遅延Proxyが候補です。ラッパーという構造だけでDecoratorとは決めません。'),4)
    extra('comparison','State と Strategy',
      ['State','Strategy','状態と許可操作','同じ目的の手段'],
      ['Stateは未払い、支払い済み、発送済みのように、状態ごとの操作と許可された遷移を表します。',
       'Strategyは会員料金と通常料金のように、同じ目的のアルゴリズムを交換します。選択は利用側や組立側が担当します。',
       'Stateで操作の結果が変わるのは、現在の状態と遷移に意味があるためです。単なる手段の選択とは違います。',
       'Strategyも実行時に替えられますが、それだけでStateになるわけではありません。状態のライフサイクルをモデル化するのか、手段の違いを分離するのかで判断します。'],
      'Template Methodは継承で手順の一部を変え、Strategyは合成で手段を交換するという比較も重要です。',
      ('会員の割引方式を組立側が渡すなら、注文の状態遷移か？','その例はStrategyです。未払いから支払い済みへの遷移ならStateを検討します。'),4)
    extra('exercise','注文通知 1｜一通から、送信経路の追加へ',
      ['一通のメール','SMS が追加','送信契約','組立で選択'],
      ['最初の要求は注文確定後にメールを一通送ることです。直接関数を呼ぶだけで十分なら、抽象化を急ぎません。',
       '次に顧客ごとにメールかSMSを選ぶ要求が増えました。注文処理が全経路のAPIを知ることが、新しい変更の痛みです。',
       '送信の契約を用意し、外部SMSの契約差はAdapterで吸収する案があります。選んだ送信手段へ委譲する部分はStrategyの観点でも考えられます。',
       '組立側が顧客条件で経路を選びます。継承で生成する要件がないなら、Factory Methodを増やすより注入が単純かもしれません。'],
      '候補は要件から選びます。送信処理はこのページでは実行せず、設計の変更を説明しています。',
      ('SMS追加で、必ずFactory Methodを使うべき？','必須ではありません。既存契約の変換はAdapter、送信手段の選択は注入やStrategyが候補です。生成の差替えが必要かを別に判断します。'),5)
    extra('exercise','注文通知 2｜監査とログを、同じ責務にしない',
      ['注文確定イベント','mail / audit','ログ付き送信','解除・失敗方針'],
      ['注文確定を契機に、顧客通知とは独立した監査処理も動かしたいという要求が増えます。',
       '独立した購読先を増減するならObserverが候補です。固定の二箇所へ呼ぶだけなら、明示した関数呼出しも比較します。',
       '一つの送信へログを重ねる責務はDecoratorで分けられます。独立したイベント購読と、同じ送信の前後処理は異なる境界です。',
       '購読解除の時点、例外で後続を止めるか、ログに機密情報を残さないかを決めます。通知の図だけで配送保証が得られるわけではありません。'],
      'ObserverとDecoratorは併用できます。図で分かれた購読先と、入れ子のラッパーを取り違えないでください。',
      ('監査の失敗で顧客通知まで止めるかは、Observerが自動的に決める？','決めません。例外方針、順序、再試行と必要な保証をアプリ側で設計します。'),5)
    extra('exercise','注文通知 3｜再試行と注文状態を分ける',
      ['送信要求 Command','順番・再試行','注文 State','保証を設計'],
      ['送信を後から実行したい場合、送信要求をCommandとして保持する案があります。要求の内容と実行する役割を分けます。',
       '再試行すると二重送信の可能性があります。永続キュー、要求の識別子、冪等性、成功の記録はCommandだけでは得られません。',
       '未払いでは発送できないという規則は、注文のStateで表す候補です。通知の送信待ちと注文の支払い状態は、同じ軸にまとめない方がよい場合があります。',
       '状態遷移とイベントの保存をどう整合させるかは追加の設計です。小規模なら分岐や直接呼出しを残し、要件と失敗時の根拠で採否を決めます。'],
      '唯一の正解はありません。想定する失敗、必要な保証、運用できる複雑さを説明した設計案を作ってください。',
      ('Commandにして再試行すれば、重複なく一度だけ届く？','保証されません。配送と実行の成功は別です。識別子、永続化、冪等性や整合性の方針が必要です。'),5)
    extra('references','次は、自分の変更要求で説明する',
      ['変更を一つ書く','候補を二つ比較','依存と寿命','採否を言葉に'],
      ['手元のコードで困る変更を一つ選び、今の設計でどの型や呼出側を直すかを書き出します。',
       'パターンを使う案と、単純な分岐や関数で済ませる案を比較します。使わない案も説明できれば理解が進んでいます。',
       '役割、依存の向き、所有者、例外、寿命、並行性を確認します。コードの実行結果と設計上の保証を混同しません。',
       '通常教材のJavaコードと確認問題で検証してください。参考資料は元の教材の資料章へ。名前ではなく問題と判断の根拠を説明できることが目標です。'],
      '用語は通常教材の用語集へ、GoFの書籍とJavaの公式仕様は参考資料章へリンクしています。',
      ('パターンを適用しないという結論も、学習の成果になる？','なります。具体的な変更に対する利益と複雑さを比較し、単純な案を選んだ根拠を説明できることが重要です。'),6)
    assert len(SLIDES)==79 and len(LABS)==23
    return SLIDES

CSS=r'''
.gof-course .scope-note{font-size:12px;border-left:3px solid var(--accent);padding-left:13px;color:var(--muted)}
/* Set the final palette after the shared presentation layer's light defaults. */
@media screen and (prefers-color-scheme:dark){:root{color-scheme:dark;--paper:#101b23;--ink:#e5efec;--muted:#b6cbd0;--line:#45636d;--accent:#b8e8d4}.gof-course .transcript,.gof-course .fallback article{background:#162630;color:var(--ink)}}
.static-reader{margin:30px 0;border-top:1px solid var(--line);padding-top:20px}.static-reader>summary{font-weight:600;cursor:pointer;color:var(--accent);padding:8px 0}.gof-course .static-reader .fallback{display:block}.static-reader .static-diagram{overflow:auto}.static-reader .static-diagram>.lesson-svg{min-width:650px}.static-reader .static-diagram:focus-visible{outline:3px solid #bc8d2d;outline-offset:3px}
.implementation{margin-top:24px;padding-top:15px;border-top:1px solid var(--line)}.implementation h3{font-size:17px}.implementation p{font-size:13px;line-height:1.9}.implementation details{margin:16px 0;padding:15px;border:1px solid var(--line);border-radius:8px}.implementation summary{cursor:pointer;font-size:14px;font-weight:600}.implementation pre{background:#102433;color:#e1eee9;border:1px solid #567780;border-radius:8px;padding:17px;overflow:auto;font:12px/1.7 ui-monospace,SFMono-Regular,Consolas,monospace;tab-size:4}.implementation pre code{white-space:pre;color:inherit;background:transparent}.code-sequence{width:100%;height:100%;min-height:0;overflow:auto;background:#0d202b;border:1px solid #51727b;border-radius:8px;padding:clamp(5px,1.4cqw,17px)}.code-part{display:none;color:#e4f2e9}.code-part.focus{display:block;opacity:1}.code-part>p{margin:0 0 5px;font-size:clamp(9px,1.1cqw,14px);color:#c4ef9b}.code-part pre{margin:0;white-space:pre-wrap;overflow-wrap:anywhere;font:clamp(9px,1.4cqw,18px)/1.55 ui-monospace,SFMono-Regular,Consolas,monospace}.code-part code{color:inherit;background:none}.static-diagram:has(.code-sequence){height:auto;min-height:220px}.static-diagram .code-sequence{display:grid;grid-template-columns:1fr 1fr;gap:18px;overflow:visible}.static-diagram .code-part{display:block;opacity:1}.static-diagram .code-part pre{font-size:11px}.static-diagram .code-part>p{font-size:12px}.gof-course .lesson-svg .edge-label{font-size:20px}.gof-course .lesson-svg .annotation{font-size:20px}.related{display:flex;gap:18px;flex-wrap:wrap;margin:15px 0;font-size:13px}.gof-course .case-detail{overflow:auto}.gof-course .cue{overflow:auto;max-height:100%}.gof-course .opening-title{font-size:clamp(18px,4.7cqw,58px)}
@media(max-width:650px){.gof-course .cue{font-size:10px;line-height:1.45}.static-diagram .code-sequence{grid-template-columns:1fr}.implementation pre{font-size:11px}}
@media print{.static-reader{margin:0;padding:0;border:0}.static-reader>summary{display:none}.static-reader .static-diagram{overflow:visible}.static-reader .static-diagram>.lesson-svg{min-width:0}.implementation details{border:0;padding:0}.implementation pre{font-size:9px;white-space:pre-wrap;background:#f2f6f3;color:#16392c}.implementation pre code{white-space:pre-wrap;overflow-wrap:anywhere}.implementation p{font-size:10px}.fallback article{break-inside:auto}.static-diagram .code-sequence{background:white;border-color:#79968a}.static-diagram .code-part{color:#16392c}.static-diagram .code-part>p{color:#285a42}.static-diagram .code-part pre{font-size:9px}.related{display:none}}
'''

READINGS=[('Chain of Responsibility','チェイン オブ レスポンシビリティ'),('Abstract Factory','アブストラクト ファクトリー'),('Factory Method','ファクトリー メソッド'),('Template Method','テンプレート メソッド'),('GoF','ジー オー エフ'),('Builder','ビルダー'),('Prototype','プロトタイプ'),('Singleton','シングルトン'),('Adapter','アダプター'),('Bridge','ブリッジ'),('Composite','コンポジット'),('Decorator','デコレーター'),('Facade','ファサード'),('Flyweight','フライウェイト'),('Proxy','プロキシー'),('Command','コマンド'),('Interpreter','インタープリター'),('Iterator','イテレーター'),('Mediator','メディエーター'),('Memento','メメント'),('Observer','オブザーバー'),('State','ステート'),('Strategy','ストラテジー'),('Visitor','ビジター'),('Java','ジャバ'),('SOLID','ソリッド'),('API','エーピーアイ'),('UML','ユーエムエル'),('HTML','エイチティーエムエル'),('CSV','シーエスブイ'),('JSON','ジェイソン'),('SMS','エスエムエス'),('SDK','エスディーケー'),('UI','ユーアイ'),('Command','コマンド')]

def migrate_progress(script):
    old="let saved={};try{saved=JSON.parse(localStorage.getItem(KEY)||'{}')||{}}catch(_){}"
    new=r'''function legacySlide(n){if(!Number.isInteger(n)||n<0||n>=56)return null;return n<2?n:n<48?2+Math.floor((n-2)/2)*3+(n-2)%2:n+23}
 function lessonFromHash(){const h=location.hash.match(/^#(slide|lesson)-(\d+)$/);if(!h)return null;const n=Number(h[2])-1,value=h[1]==='slide'?legacySlide(n):n;return Number.isInteger(value)&&value>=0&&value<DATA.length?value:null}
 let saved={};try{const raw=localStorage.getItem(KEY);if(raw!==null)saved=JSON.parse(raw)||{};else{const previous=JSON.parse(localStorage.getItem('gof-motion-slides-player-v1')||'null');if(previous&&legacySlide(previous.slide)!==null&&[.75,1,1.25,1.5,2].includes(previous.rate)){saved={slide:legacySlide(previous.slide),rate:previous.rate};localStorage.setItem(KEY,JSON.stringify(saved))}}}catch(_){}'''
    assert old in script
    script=script.replace(old,new)
    initial=r"const hash=location.hash.match(/^#slide-(\d+)$/);if(hash){const n=Number(hash[1])-1;if(n>=0&&n<DATA.length)elapsed=n*DURATION}"
    assert initial in script
    script=script.replace(initial,'const requested=lessonFromHash();if(requested!==null)elapsed=requested*DURATION;')
    change=r"window.addEventListener('hashchange',()=>{const h=location.hash.match(/^#slide-(\d+)$/);if(h){const n=Number(h[1])-1;if(n>=0&&n<DATA.length&&n!==index)jump(n)}})"
    assert change in script
    script=script.replace(change,"window.addEventListener('hashchange',()=>{const n=lessonFromHash();if(n!==null&&n!==index)jump(n)})")
    return script.replace("'#slide-'+(n+1)","'#lesson-'+(n+1)")

def build():
    update_guide(ROOT,PATTERNS,sources())
    slides=lessons();modules=[]
    for i,name in enumerate(NAMES):
        positions=[n for n,s in enumerate(slides) if s['module']['index']==i+1]
        modules.append(dict(name=name,first=min(positions),last=max(positions),accent=ACCENTS[i]))
    static=[]
    for i,s in enumerate(slides):
        if s['diagramType'] in ('gof-code','gof-lab'):drawing=s['svg']
        elif s['chapter'] in {p['id'] for p in PATTERNS}:drawing=diagram(next(p for p in PATTERNS if p['id']==s['chapter']),'static-'+s['chapter'])[0]
        else:drawing=s['svg'].replace('extra-','static-extra-')
        ElementTree.fromstring(s['svg']) if s['svg'].startswith('<svg') else None
        assert {int(x) for x in re.findall(r'data-step="(\d)"',s['svg'])}=={0,1,2,3},s['title']
        extra_html=s['detail']
        for cls in ['java-full','book-code','book-answer']:extra_html=extra_html.replace('<details class="'+cls+'">','<details class="'+cls+'" open>')
        ref=s.get('reference','../guide/index.html#'+s['chapter'])
        static.append(f'<article id="static-slide-{i+1}"><p class="eyebrow">GOF / SCENE {i+1:02d}</p><h2>{E(s["title"])}</h2><div class="static-diagram" tabindex="0" role="img" aria-label="{E(s["diagramLabel"]+"。"+"、".join(s["nodes"]))}">{drawing}</div><ol>'+''.join('<li>'+E(step)+'</li>' for step in s['steps'])+f'</ol><p>{E(s["note"])}</p>{extra_html}<p><b>確認問題：</b>{E(s["question"])}</p><p><b>解答・理由：</b>{E(s["answer"])}</p><a href="{E(ref)}">通常教材の対応する章</a></article>')
    # Reuse the tested player, but remove Android-only progress import / app install code.
    script=player.JS.removesuffix('\n'+TRANSFER_JS)
    script=re.sub(r" window.addEventListener\('android-learning-progress-imported'.*?\n",'',script)
    script=script.replace('STEP=6,DURATION=24','STEP=8,DURATION=32').replace('android-animated-slides-player-v1','gof-motion-slides-player-v2').replace('android-narration-preferences-v1','gof-narration-preferences-v1')
    script=migrate_progress(script)
    script=script.replace('initHomeApp();','').replace('__HOME_JS__','')
    script=script.replace("e.target.closest('input,select,button,a,summary,textarea')","e.target.closest('input,select,button,a,summary,textarea,pre,.code-sequence,.lab-stage,.book-lab,#static-reader')")
    script=re.sub(r' const pronunciations=\[.*?\];',' const pronunciations='+json.dumps(READINGS,ensure_ascii=False)+';',script)
    script=script.replace('Androidの仕組みを、音声と図で学びます。','GoFデザインパターンを、音声と図で学びます。')
    script=script.replace('prepareCase(slide);',"prepareCase(slide);$('implementation').innerHTML=slide.detail;")
    script=script.replace("'../guide/index.html#'+slide.chapter","slide.reference||'../guide/index.html#'+slide.chapter")
    script=script.replace('directCase(slide,s);',"directCase(slide,s);const code=$('diagram').querySelector('.code-sequence,.lab-stage');if(code)code.scrollTop=0;")
    script=script.replace(' DATA.forEach'," $('implementation').addEventListener('toggle',e=>{if(e.target.tagName==='DETAILS'&&e.target.open)pause()},true);\n DATA.forEach",1)
    script=script.replace(' DATA.forEach'," $('course-reading').addEventListener('toggle',e=>{if(e.target.open)pause()});\n DATA.forEach",1)
    script=script.replace(' DATA.forEach'," const reader=$('static-reader');reader.open=false;reader.addEventListener('toggle',()=>{if(reader.open)pause()});let readerBeforePrint=false;window.addEventListener('beforeprint',()=>{readerBeforePrint=reader.open;pause();reader.open=true});window.addEventListener('afterprint',()=>{reader.open=readerBeforePrint});\n DATA.forEach",1)
    direction=DIRECTION_JS.replace("['01 / 着眼点','02 / 仕組みを追う','03 / 観測する','04 / 持ち帰る要点']","['01 / 問題と契約','02 / 役割を分ける','03 / 結果を確かめる','04 / 判断の根拠']")
    script=script.replace('__DIRECTION_JS__',direction.replace('__MODULES__',json.dumps(modules,ensure_ascii=False))).replace('__FULLSCREEN_JS__',FULLSCREEN_JS).replace('__DATA__',json.dumps(slides,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'))
    template=player.TEMPLATE.replace('<body>','<body class="gof-course">')
    template=template.replace('Androidを動く図で学ぶ｜スライド教材','GoFを動く図と音声で学ぶ｜設計検証と実践').replace('Android 16の30章を動く図と字幕で振り返る、16:9のスライド教材。全32枚、自動再生とスマートフォン全画面に対応。','GoFの23パターンを79場面で学ぶ日本語教材。変更要求・反例・Java 17の検証コード・設計判断を、図と音声で深く理解します。')
    template=template.replace('ANDROID 16 / MOTION LESSONS','GOF / MOTION + NARRATION').replace('Androidを、<br>動く図で学ぶ。','GoFを、<br>動く図と音声で学ぶ。')
    template=template.replace('身近な疑問から、図と実例で仕組みを追う32レッスン。','役割・Java・設計検証を、79場面で深く学ぶ。').replace('字幕のみは約13分','字幕のみは約42分')
    template=template.replace('← Androidの教材一覧','← GoFの教材一覧').replace('元のAndroid教材を読む','通常のGoF教材を読む').replace('Androidの教材一覧へ戻る','GoFの教材一覧へ戻る').replace('Androidスライドプレーヤー','GoFスライドプレーヤー').replace('Android 16 / 図は説明用に簡略化しています','GoF / Java 17 / 図は説明用です')
    template=template.replace('<ol id="explanation"></ol>','<ol id="explanation"></ol><div id="implementation"></div>')
    reading='<details class="course-reading" id="course-reading"><summary>学習の進め方：予想 → 実行 → 検証</summary>'+READING_GUIDE+'</details>'
    template=template.replace('__HOME_HEAD__','').replace('__HOME_GUIDE__',reading).replace('__TRANSFER_HTML__','')
    template=template.replace('<section class="fallback" id="all-slides"','<details class="static-reader" id="static-reader" open><summary>全79場面を静止版で読む（図は横スクロールできます）</summary><section class="fallback" id="all-slides"').replace('__FALLBACK__</section>','__FALLBACK__</section></details>')
    template=template.replace('要求・応答・観測など','呼出・参照・継承・状態遷移など')
    opening=OPENING.replace('ANDROID 16 / VISUAL LESSONS','GOF / DESIGN WORKBOOK').replace('Androidを、<br><em>仕組み</em>で理解する。','GoFを、<br><em>設計の判断</em>で理解する。').replace('要求を追う。状態を分ける。証拠で説明する。','予想する。反例を追う。設計を検証する。').replace('32 LESSONS','23 PATTERNS / 79 SCENES')
    related='<nav class="related" aria-label="GoFの関連教材"><a href="../animations/index.html">CSSだけで動く5つの図解</a><a href="../guide/index.html#glossary">用語集</a><a href="../guide/index.html#references">参考資料</a></nav>'
    template=template.replace('__SPEECH_SETTINGS__','__SPEECH_SETTINGS__'+related)
    result=template.replace('__CSS__',player.CSS+CSS+BOOK_CSS).replace('__FALLBACK__','\n'.join(static)).replace('__STEP_BUTTONS__',''.join(f'<button type="button" data-step="{i}" aria-label="説明{i+1}へ移動" aria-pressed="false">{i+1}</button>' for i in range(4))).replace('__JS__',script).replace('__CASE_HTML__',CASE_HTML).replace('__OPENING__',opening).replace('__RECAP__',RECAP).replace('__SPEECH_CONTROLS__',CONTROLS).replace('__SPEECH_SETTINGS__',SETTINGS)
    assert not re.search(r'__[A-Z_]+__',result)
    assert 'android-learning-progress-imported' not in result and 'android-narration-preferences' not in result
    assert all('id="'+s['chapter']+'"' in (ROOT/'gof/guide/index.html').read_text() for s in slides)
    target=ROOT/'gof/slides/index.html';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(result)
    print(f'Generated 23 patterns / {len(slides)} scenes / {len(slides)*4} explanations / {len(slides)} quizzes; {len(result.encode()):,} bytes.')

if __name__=='__main__':build()
