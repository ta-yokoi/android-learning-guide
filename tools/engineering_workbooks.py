"""Shared rendering and managed insertion for Android and embedded workbooks."""
from html import escape as E
from pathlib import Path
import re
import android_workbooks as android
import embedded_workbooks as embedded

CSS=r'''
.engineering-workbook{margin:28px 0;padding:23px;border:1px solid var(--line,#b9ccc4);border-radius:10px;min-width:0;color:inherit;background:transparent;line-height:1.9}.engineering-workbook h3{font-size:22px;line-height:1.55;margin:0 0 18px}.engineering-workbook h4{font-size:16px;margin:24px 0 9px}.engineering-workbook p,.engineering-workbook li{font-size:14px;line-height:1.95}.engineering-kicker{font-size:11px!important;font-weight:700;letter-spacing:.1em;color:var(--accent,var(--teal,#176f64))}.engineering-contract{padding:14px 18px;border-left:3px solid var(--accent,var(--teal,#176f64));background:#638a7610}.engineering-table{max-width:100%;overflow:auto}.engineering-workbook table{min-width:570px;width:100%;border-collapse:collapse;font-size:13px;background:transparent}.engineering-workbook th,.engineering-workbook td{padding:12px;text-align:left;vertical-align:top;border:1px solid var(--line,#b9ccc4);line-height:1.8}.engineering-workbook pre{max-width:100%;overflow:auto;padding:17px;background:#102433;color:#e4f0eb;border:1px solid #52717e;border-radius:8px;font:12px/1.7 ui-monospace,SFMono-Regular,Consolas,monospace;tab-size:4}.engineering-workbook pre code{white-space:pre;background:transparent;color:inherit}.engineering-workbook details{padding:13px 0;margin:14px 0;border-top:1px solid var(--line,#b9ccc4)}.engineering-workbook summary{font-size:14px;line-height:1.7;font-weight:600;cursor:pointer}.engineering-scope{font-size:12px!important;color:var(--muted,#536d77)}.engineering-workbook :focus-visible{outline:3px solid #bc8d2d;outline-offset:3px}.engineering-learning{margin:22px 0;padding:18px 22px;border-left:3px solid var(--accent,var(--teal,#176f64));font-size:14px}.engineering-learning p{font-size:14px}.engineering-bench{width:100%;height:100%;overflow:auto;border:1px solid #5a7b85;border-radius:10px;background:#0d202c;color:#e4f0eb;padding:clamp(7px,1.6cqw,20px)}.engineering-beat{display:none}.engineering-beat.focus{display:block;opacity:1}.engineering-beat h3{font-size:clamp(11px,1.7cqw,22px);color:#c4ef9b;margin:0 0 10px;line-height:1.5}.engineering-beat p,.engineering-beat li,.engineering-beat pre{font-size:clamp(10px,1.5cqw,19px);line-height:1.65}.engineering-beat li{margin:6px 0}.engineering-beat pre{white-space:pre-wrap;overflow-wrap:anywhere;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;margin:0}.engineering-beat code{color:inherit;background:transparent}.engineering-beat ol{margin:0;padding-left:22px}.static-diagram:has(.engineering-bench){height:auto!important}.static-diagram .engineering-bench{display:grid;grid-template-columns:1fr 1fr;gap:20px}.static-diagram .engineering-beat{display:block}.static-diagram .engineering-beat h3{font-size:14px}.static-diagram .engineering-beat p,.static-diagram .engineering-beat li,.static-diagram .engineering-beat pre{font-size:12px}
@media(max-width:650px){.engineering-workbook{padding:16px}.engineering-workbook h3{font-size:19px}.engineering-workbook p,.engineering-workbook li{font-size:13px}.engineering-workbook pre{font-size:11px;padding:12px}.static-diagram .engineering-bench{grid-template-columns:1fr}}
@media print{.engineering-workbook{padding:6px 0;border:0;break-inside:auto}.engineering-workbook h3{font-size:17px}.engineering-workbook h4{font-size:13px;margin:12px 0 5px}.engineering-workbook p,.engineering-workbook li,.engineering-workbook table,.engineering-workbook th,.engineering-workbook td{font-size:10px}.engineering-workbook pre{background:#f1f6f3;color:#16392c;font-size:9px;white-space:pre-wrap;overflow:visible}.engineering-workbook pre code{white-space:pre-wrap;overflow-wrap:anywhere}.engineering-table{overflow:visible}.engineering-workbook table{min-width:0}.engineering-workbook details{break-inside:auto}.engineering-bench{background:#f1f6f3;color:#16392c}.engineering-beat h3{color:#28614d}.engineering-learning{display:none}}
'''

LEARNING='''<aside class="engineering-learning"><h3>設計検証ノートの使い方</h3><p>各項目の最後に、追加要求・守る契約・架空の入力と期待結果・実行できるホストモデル・代案・三つの実習問題を設けています。</p><ol><li>コードを開く前に結果を予想する。</li><li>標準出力と、自分が予想した理由を照合する。</li><li>モデルで確認できた範囲と、対象機で未確認の範囲を書く。</li><li>代案のコストを比べ、次に必要な実機試験を一つ定義する。</li></ol><p>モデルの合格はAndroid API、回路、ドライバー、RTOSや実機の正しさを証明しません。条件・時計・寿命・副作用の契約を学び、実際の対象仕様と証拠へ結び付けてください。</p></aside>'''

def source_for(w):return android.code_for(w) if w['language']=='python' else embedded.code_for(w)
def output_for(w):return android.output_for(w) if w['language']=='python' else embedded.output_for(w)

def render(w,subject,static=False,guide=False):
    ident=' id="workbook-'+w['id']+'"' if guide else ''
    opened=' open' if static else ''
    lang='Python 3 / Main.py' if w['language']=='python' else 'C11 / main.c'
    command='python3 Main.py' if w['language']=='python' else 'cc -std=c11 -Wall -Wextra -Werror -pedantic main.c -o experiment\n./experiment'
    scope=('標準ライブラリだけで動くPythonのホストモデルです。Android APIやサービスを呼ばず、架空の入力に対する状態・判断・計算を検証します。'
           if w['language']=='python' else '標準C11で動くホスト上の検証例です。レジスター、実割込み、DMA、RTOS、実ストレージを操作しません。')
    evidence=''.join('<tr><th scope="row">'+E(a)+'</th><td>'+E(b)+'</td><td>'+E(c)+'</td></tr>' for a,b,c in w['evidence'])
    alternatives=''.join('<tr><th scope="row">'+E(a)+'</th><td>'+E(b)+'</td></tr>' for a,b in w['alternatives'])
    questions=''.join(f'<details class="engineering-answer"{opened}><summary>実習{i+1}. {E(q)}</summary><p><b>解答と理由：</b>{E(a)}</p></details>' for i,(q,a) in enumerate(w['questions']))
    refs='#sources' if guide else '../../guide/index.html#sources'
    video=('<p><a href="../deep-dives/'+w['id']+'/index.html#slide-6">この項目を音声付き動画の設計実習で学ぶ →</a></p>' if guide and subject=='android' else '')
    return f'''<section class="engineering-workbook"{ident}><p class="engineering-kicker">DESIGN WORKBOOK / {E(subject.upper())}</p><h3>設計検証ノート：{E(w['title'])}</h3><h4>追加された要求</h4><p>{E(w['request'])}</p><div class="engineering-contract"><b>先に定める契約</b><p>{E(w['contract'])}</p></div><h4>実行前に予想する</h4><p>以下の入力は説明用の架空ケースです。なぜその結果になるか、コードを開く前に一行ずつ説明してください。表は狭い画面で横スクロールできます。</p><div class="engineering-table" tabindex="0" role="region" aria-label="入力と期待結果の表"><table><thead><tr><th scope="col">入力・条件</th><th scope="col">期待する結果・観点</th><th scope="col">検証する理由</th></tr></thead><tbody>{evidence}</tbody></table></div><details class="engineering-code"{opened}><summary>検証コードと標準出力を開く（{lang}）</summary><p>{E(scope)}</p><p>別のフォルダーに保存し、次のコマンドで実行します。アサーションは有効にした状態で使います。</p><pre tabindex="0" role="region" aria-label="ホスト検証の実行方法"><code>{E(command)}</code></pre><pre tabindex="0" role="region" aria-label="独立して実行できるホストモデル"><code>{E(source_for(w))}</code></pre><h4>このモデルの標準出力</h4><pre tabindex="0" role="region" aria-label="ホストモデルの標準出力"><code>{E(output_for(w))}</code></pre></details><h4>読み解く：観測から設計へ</h4><p>{E(w['reading'][0])}</p><p>{E(w['reading'][1])}</p><h4>別の案なら何が変わるか</h4><div class="engineering-table" tabindex="0" role="region" aria-label="設計案とコストの比較"><table><thead><tr><th scope="col">設計案</th><th scope="col">選ぶ理由とコスト</th></tr></thead><tbody>{alternatives}</tbody></table></div><h4>自分で判断する：三つの実習問題</h4><p>解答を開く前に、守る契約・設計の変更箇所・追加する実機試験を書いてください。以下はこの前提に基づく解答例です。</p>{questions}<p class="engineering-scope">{E(scope)} 合格した出力を、対象機の性能・安全性・互換性の保証へ読み替えないでください。</p><p><a href="{refs}">一次資料と適用範囲を確認する</a></p>{video}</section>'''

def figure(w):
    expected='<ol>'+''.join('<li>'+E(a)+'<br><b>'+E(b)+'</b></li>' for a,b,_ in w['evidence'])+'</ol>'
    alternatives='<ol>'+''.join('<li><b>'+E(a)+'</b><br>'+E(b)+'</li>' for a,b in w['alternatives'])+'</ol>'
    panels=[('01 / 要求と前提','<p>'+E(w['request'])+'</p>'),('02 / 契約と予想','<p>'+E(w['contract'])+'</p>'+expected),('03 / モデルの出力','<pre><code>'+E(output_for(w))+'</code></pre>'),('04 / 設計案を比較',alternatives)]
    return '<div class="engineering-bench" tabindex="0" aria-label="要求・予想・モデルの出力・設計案の四段階">'+''.join(f'<section class="engineering-beat role" data-step="{i}"><h3>{title}</h3>{body}</section>' for i,(title,body) in enumerate(panels))+'</div>'

def update_guide(root,subject):
    path=root/subject/'guide/index.html';text=path.read_text()
    text=re.sub(r'<!-- ENGINEERING-WORKBOOK-START -->.*?<!-- ENGINEERING-WORKBOOK-END -->','',text,flags=re.S)
    text=re.sub(r'<style id="engineering-workbook-styles">.*?</style>','',text,flags=re.S)
    text=text.replace('</head>','<style id="engineering-workbook-styles">'+CSS+'</style></head>')
    workbooks=android.WORKBOOKS if subject=='android' else embedded.WORKBOOKS
    chunks=re.split(r'(?=<section class="chapter" id=")',text);seen=set()
    for i,chunk in enumerate(chunks):
        match=re.match(r'<section class="chapter" id="([^"]+)"',chunk)
        if not match or match[1] not in workbooks:continue
        key=match[1];seen.add(key);w=workbooks[key]
        learning=LEARNING.replace('各項目の最後に、',f'この分野の{len(workbooks)}項目へ実習{len(workbooks)*3}問を追加しています。各項目の最後に、')
        content=(learning if key=='overview' else '')+render(w,subject,guide=True)
        marker='<div class="chapter-bottom">';assert marker in chunk,(subject,key)
        chunks[i]=chunk.replace(marker,'<!-- ENGINEERING-WORKBOOK-START -->'+content+'<!-- ENGINEERING-WORKBOOK-END -->'+marker,1)
    assert seen==set(workbooks),(subject,set(workbooks)-seen)
    path.write_text(''.join(chunks))

if __name__=='__main__':
    root=Path(__file__).resolve().parent.parent
    for subject in ['android','embedded']:update_guide(root,subject)
    print('Generated Android 30 + embedded 13 design workbooks / 129 explained exercises.')
