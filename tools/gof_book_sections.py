"""Shared prose/workbook rendering for the regular guide and narrated player."""
from html import escape as E
from gof_book_labs import LABS,java_for

REFERENCES={
 'factory-method':('JLS 17：呼出先メソッドの実行時の選択','https://docs.oracle.com/javase/specs/jls/se17/html/jls-15.html#jls-15.12.4.4'),
 'prototype':('Java 17 API：ArrayList','https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/ArrayList.html'),
 'singleton':('JLS 17：happens-beforeの規則','https://docs.oracle.com/javase/specs/jls/se17/html/jls-17.html#jls-17.4.5'),
 'flyweight':('Java 17 API：HashMapの並行利用の注意','https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/HashMap.html'),
 'interpreter':('JLS 17：条件付き論理積の短絡評価','https://docs.oracle.com/javase/specs/jls/se17/html/jls-15.html#jls-15.23'),
 'iterator':('Java 17 API：Iteratorの契約','https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/Iterator.html'),
 'memento':('JLS 17：アクセス制御','https://docs.oracle.com/javase/specs/jls/se17/html/jls-6.html#jls-6.6.1'),
 'observer':('Java 17 API：List.copyOf','https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/List.html#copyOf(java.util.Collection)'),
 'strategy':('JLS 17：整数乗算とオーバーフロー','https://docs.oracle.com/javase/specs/jls/se17/html/jls-15.html#jls-15.17.1'),
 'template-method':('JLS 17：try-finallyの実行','https://docs.oracle.com/javase/specs/jls/se17/html/jls-14.html#jls-14.20.2'),
 'visitor':('JLS 17：オーバーロードされた呼出の選択','https://docs.oracle.com/javase/specs/jls/se17/html/jls-15.html#jls-15.12.2'),
}

CSS=r'''
.book-lab{margin:30px 0 20px;padding:24px;border:1px solid var(--line,#b9ccc4);border-radius:10px;background:transparent;color:inherit;line-height:1.9;min-width:0}.book-lab h3{margin:0 0 18px;font-size:22px;line-height:1.55}.book-lab h4{font-size:16px;margin:25px 0 10px}.book-lab p,.book-lab li{font-size:14px;line-height:1.95}.book-kicker{font-size:11px!important;font-weight:700;letter-spacing:.12em;color:var(--accent,var(--teal,#176f64))}.book-contract{padding:16px 18px;border-left:3px solid var(--accent,var(--teal,#176f64));background:#6288750b}.book-table-wrap{max-width:100%;overflow:auto}.book-lab table{width:100%;min-width:560px;border-collapse:collapse;font-size:13px;background:transparent}.book-lab th,.book-lab td{padding:12px;text-align:left;vertical-align:top;border:1px solid var(--line,#b9ccc4);line-height:1.8}.book-lab th{font-weight:650}.book-lab pre{margin:15px 0;padding:18px;max-width:100%;overflow:auto;background:#102433;color:#e4f0eb;border:1px solid #52717e;border-radius:8px;font:12px/1.75 ui-monospace,SFMono-Regular,Consolas,monospace;tab-size:4}.book-lab pre code{white-space:pre;background:transparent;color:inherit}.book-lab details{border-top:1px solid var(--line,#b9ccc4);padding:14px 0;margin:15px 0}.book-lab summary{font-size:14px;line-height:1.7;cursor:pointer;font-weight:600}.book-lab :focus-visible{outline:3px solid #bc8d2d;outline-offset:3px}.book-exercises{margin-top:24px}.book-answer{padding:14px 0!important}.book-answer p{margin-bottom:0}.book-reading-guide{border-left:3px solid var(--accent,var(--teal,#176f64));padding:18px 22px;margin:22px 0}.book-reading-guide p{font-size:14px}.book-reading-guide ol{padding-left:22px}.book-next{font-size:12px!important;color:var(--muted,#536d77)}
.course-reading{margin:0 0 20px;padding:12px 16px;border:1px solid var(--line);border-radius:8px;font-size:13px}.course-reading>summary{color:var(--accent);font-weight:600;cursor:pointer}.course-reading .book-reading-guide{margin-bottom:0}
.lab-stage{height:100%;width:100%;overflow:auto;border:1px solid #5c7b86;border-radius:10px;padding:clamp(7px,1.7cqw,21px);background:#0b202e;color:#e4f0eb}.lab-beat{display:none}.lab-beat.focus{display:block;opacity:1}.lab-beat h3{font-size:clamp(11px,1.7cqw,22px);color:#c4ef9b;line-height:1.5;margin:0 0 12px}.lab-beat p,.lab-beat li{font-size:clamp(10px,1.5cqw,19px);line-height:1.65}.lab-beat ol{margin:0;padding-left:22px}.lab-beat li{padding:5px 0}.lab-beat pre{margin:0;font:clamp(10px,1.5cqw,19px)/1.7 ui-monospace,SFMono-Regular,Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere}.lab-beat pre code{background:transparent;color:inherit}.static-diagram:has(.lab-stage){height:auto!important}.static-diagram .lab-stage{display:grid;grid-template-columns:1fr 1fr;gap:22px}.static-diagram .lab-beat{display:block}.static-diagram .lab-beat p,.static-diagram .lab-beat li,.static-diagram .lab-beat pre{font-size:12px}.static-diagram .lab-beat h3{font-size:14px}
@media(max-width:650px){.book-lab{padding:16px;margin:20px 0}.book-lab h3{font-size:19px}.book-lab p,.book-lab li{font-size:13px}.book-lab pre{padding:12px;font-size:11px}.static-diagram .lab-stage{grid-template-columns:1fr}}
@media print{.book-lab{padding:5px 0;border:0;break-inside:auto}.book-lab h3{font-size:17px}.book-lab h4{font-size:13px;margin:12px 0 5px}.book-lab p,.book-lab li,.book-lab table,.book-lab th,.book-lab td{font-size:10px}.book-lab pre{font-size:9px;background:#f3f6f4;color:#16392c;white-space:pre-wrap;overflow:visible}.book-lab pre code{white-space:pre-wrap;overflow-wrap:anywhere}.book-lab table{min-width:0}.book-table-wrap{overflow:visible}.book-lab details{break-inside:auto}.lab-stage{background:#f3f6f4;color:#16392c}.lab-beat h3{color:#28614d}.book-reading-guide{margin:10px 0;padding:8px 14px}}
@media print{.course-reading{display:none}}
'''

READING_GUIDE='''<aside class="book-reading-guide"><h3>読んで終わらせないための学習手順</h3><p>各パターンは、基本例の後に「設計検証ノートと実習」が続きます。正常系が動くことと、変化や失敗に耐えられることを分けて確かめてください。</p><ol><li><b>問題を固定する：</b>追加された要求と、今の設計で変更する箇所を書く。</li><li><b>結果を予想する：</b>実習コードを実行する前に、出力と守るべき契約をメモする。</li><li><b>反例を追う：</b>なぜ期待を外すかを、参照・状態・呼出順・例外の具体的な行で説明する。</li><li><b>代案を比較する：</b>パターンを使う案と単純な案を比べ、増える責任と適用範囲を明示する。</li><li><b>問題を解く：</b>解答を開く前に設計案とテストを一つずつ書き、理由を照合する。</li></ol><p>Java例は17を対象にしています。短い教材コードの前提を実用の保証へ拡大せず、入出力・寿命・並行性・外部副作用を要件に応じて追加してください。</p></aside>'''

def render_lab(p,source,static=False,guide=False):
    lab=LABS[p['id']];code=java_for(source['code'],lab)
    open_attr=' open' if static else ''
    ident=' id="lab-'+p['id']+'"' if guide else ''
    traces=''.join('<tr><th scope="row">'+E(i)+'</th><td>'+E(o)+'</td><td>'+E(reason)+'</td></tr>' for i,o,reason in lab['trace'])
    alternatives=''.join('<tr><th scope="row">'+E(name)+'</th><td>'+E(why)+'</td></tr>' for name,why in lab['alternatives'])
    questions=''.join(f'<details class="book-answer"{open_attr}><summary>実習{i+1}. {E(q)}</summary><p><b>解答と理由：</b>{E(a)}</p></details>' for i,(q,a) in enumerate(lab['questions']))
    references='<p class="book-next">根拠を確認する：<a href="'+('#references' if guide else '../guide/index.html#references')+'">GoFの書籍と参考資料</a>'
    if p['id'] in REFERENCES:
        name,url=REFERENCES[p['id']];references+=' ／ <a href="'+E(url)+'">'+E(name)+'</a>'
    references+='</p>'
    return f'''<section class="book-lab"{ident}><p class="book-kicker">DESIGN WORKBOOK / {E(p['name'])}</p><h3>設計検証ノートと実習：{E(lab['title'])}</h3><h4>追加された要求</h4><p>{E(lab['requirement'])}</p><div class="book-contract"><b>先に定める契約</b><p>{E(lab['contract'])}</p></div><h4>予想する：入力と検証ポイント</h4><p>表の結果を自分で説明してから、コードを開いてください。変更案の分析を示す行は、プログラムの実行結果とは区別しています。</p><div class="book-table-wrap" tabindex="0" role="region" aria-label="入力と検証ポイントの表"><table><thead><tr><th scope="col">入力・操作・変更案</th><th scope="col">結果または検討点</th><th scope="col">なぜ確かめるか</th></tr></thead><tbody>{traces}</tbody></table></div><details class="book-code"{open_attr}><summary>検証コードと実行結果を開く（Main.java / Java 17）</summary><p>基本例と別のフォルダーへMain.javaとして保存し、<code>javac --release 17 Main.java</code>、<code>java Main</code>で実行します。必要な型をすべて含む独立例です。表示するHTML自体はJavaを実行しません。</p><pre tabindex="0" role="region" aria-label="検証用Javaコード"><code>{E(code)}</code></pre><h4>このコードの標準出力</h4><pre tabindex="0" role="region" aria-label="検証コードの標準出力"><code>{E(lab['output'])}</code></pre></details><h4>読み解く：観測から設計へ</h4><p>{E(lab['reading'][0])}</p><p>{E(lab['reading'][1])}</p><h4>別の案なら、何が変わるか</h4><div class="book-table-wrap" tabindex="0" role="region" aria-label="設計案を比べる表"><table><thead><tr><th scope="col">候補</th><th scope="col">選ぶ理由と支払う費用</th></tr></thead><tbody>{alternatives}</tbody></table></div><section class="book-exercises"><h4>自分で判断する：三つの実習問題</h4><p>結論だけでなく、守る契約・変更箇所・検証する入力を添えて答えてください。以下は前提に基づく解答例です。</p>{questions}</section><p class="book-next">基本例 → 要件変更 → 反例と契約 → 代案 → テスト、の順で自分のコードでも検討してください。</p>{references}</section>'''

def lab_figure(lab,static=False):
    expected='<ol>'+''.join('<li>'+E(item[0])+'<br><b>'+E(item[1])+'</b></li>' for item in lab['trace'])+'</ol>'
    alternatives='<ol>'+''.join('<li><b>'+E(name)+'</b><br>'+E(why)+'</li>' for name,why in lab['alternatives'])+'</ol>'
    panels=[('01 / 要求を固定する','<p>'+E(lab['requirement'])+'</p><p>'+E(lab['contract'])+'</p>'),('02 / 結果を予想する',expected),('03 / 出力を照合する','<pre><code>'+E(lab['output'])+'</code></pre>'),('04 / 設計案を比較する',alternatives)]
    return '<div class="lab-stage" tabindex="0" aria-label="要求・予想・実行結果・設計判断の四段階">'+''.join(f'<section class="lab-beat role" data-step="{i}"><h3>{title}</h3>{body}</section>' for i,(title,body) in enumerate(panels))+'</div>'

def update_guide(root,patterns,sources):
    """Managed additions keep the original text, examples, navigation and progress keys."""
    import re
    path=root/'gof/guide/index.html';text=path.read_text()
    text=re.sub(r'<!-- GOF-BOOK-START -->.*?<!-- GOF-BOOK-END -->','',text,flags=re.S)
    text=re.sub(r'<style id="gof-book-styles">.*?</style>','',text,flags=re.S)
    text=text.replace('</head>','<style id="gof-book-styles">'+CSS+'</style></head>')
    sections=re.split(r'(?=<section class="chapter" id=")',text)
    for i,section in enumerate(sections):
        match=re.match(r'<section class="chapter" id="([^"]+)"',section)
        if not match:continue
        key=match[1]
        if key=='start':addition=READING_GUIDE
        elif key in LABS:addition=render_lab(next(p for p in patterns if p['id']==key),sources[key],guide=True)
        else:continue
        marker='<div class="chapter-bottom">';assert marker in section,key
        sections[i]=section.replace(marker,'<!-- GOF-BOOK-START -->'+addition+'<!-- GOF-BOOK-END -->'+marker,1)
    path.write_text(''.join(sections))
