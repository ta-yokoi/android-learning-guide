#!/usr/bin/env python3
"""Apply the library navigation and editorial layout to the existing static pages."""
from html import escape
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent

STYLE = """
<style id="library-layout">
:root{--library-surface:#fff;--library-bg:#f6f8f5;--library-accent:#075e55;--library-tint:#e7f2ec}
body{background:var(--library-bg)}
.site-header{background:var(--library-surface)}
.hero{padding:clamp(32px,6vw,70px) 0 clamp(25px,4vw,44px);background:transparent;position:relative}
.hero h1{max-width:18ch;font-weight:780;letter-spacing:-.045em}
.hero .lead{max-width:66ch;text-wrap:pretty}
.library-nav{display:flex;flex-wrap:wrap;align-items:center;gap:4px 12px;margin:12px auto 8px}
.library-nav a{display:inline-flex;align-items:center;min-height:44px;font-size:13px;padding:0 9px;border-radius:7px}
.library-nav a[aria-current]{background:var(--library-tint);color:var(--library-accent);font-weight:700;text-decoration:none}
.library-routes{margin:0 0 34px;padding:20px 0;border-block:1px solid var(--line)}
.library-routes h2{font-size:18px;margin:0 0 12px}
.library-route-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:10px}
.library-route{display:block;background:var(--library-surface);border:1px solid var(--line);padding:13px 15px;border-radius:8px;text-decoration:none;color:var(--ink)}
.library-route strong{display:block;color:var(--library-accent);font-size:14px;text-decoration:underline;text-underline-offset:3px}
.library-route span{display:block;color:var(--muted);font-size:13px;line-height:1.6;margin-top:4px}
.library-route:hover{border-color:var(--library-accent)}
.card{min-width:0;background:var(--library-surface);border-top:3px solid var(--library-accent);padding:clamp(17px,3vw,28px)}
.card h3{font-size:clamp(20px,2.4vw,26px);margin-top:5px;text-wrap:pretty}
.card .description{font-size:14px;line-height:1.8}
.card .open-guide{min-height:44px}
.home-install{margin-bottom:22px}
.card:has(#gof-title),.card:has(#slides-title){border-top-color:#8066a8}
.card:has(#embedded-title){border-top-color:#ab763d}
.card:has(#works-card-title){border-top-color:#677cae}
.works-cover{height:clamp(96px,16vw,156px);margin:0 0 15px;border-radius:6px;background-color:#111a30}
.works-cover.gallery{background-image:radial-gradient(ellipse at 48% 45%,transparent 19%,#91e6fe99 20%,transparent 23%),radial-gradient(ellipse at 52% 55%,transparent 28%,#9f7cffaa 29%,transparent 33%),radial-gradient(ellipse at 56% 50%,#534190,transparent 67%)}
.works-cover.observatory{background-image:radial-gradient(circle at 48% 44%,#c6faff, #458ccb 6%,#1b315b 20%,transparent 45%),repeating-radial-gradient(ellipse at center,#a9d7ff88 0 1px,transparent 2px 13px)}
.works-cover.tides{background-image:radial-gradient(ellipse at 32% 108%,#61e9d2 0%,#266caa 25%,transparent 58%),radial-gradient(ellipse at 82% -10%,#bc7adc 0%,#534190 27%,transparent 58%),linear-gradient(156deg,#10182e,#16294d)}
.library-groups{display:flex;flex-wrap:wrap;gap:4px 14px;margin:12px 0}
.library-groups a{display:inline-flex;align-items:center;min-height:44px;font-size:14px}
.library-course-group .facts{margin-top:auto}
.library-course-group{margin:26px 0 34px;scroll-margin-top:12px}
.library-course-group>h3{font-size:20px;margin:0 0 10px}
.library-course-group>.grid>.card h4{font-size:clamp(18px,2vw,23px);margin:0 0 8px;line-height:1.5}
.library-search{display:flex;flex-wrap:wrap;align-items:end;gap:10px;margin:0 0 16px}
.library-search>label{font-weight:700;flex:1 1 240px}
.library-search input{display:block;width:100%;padding:9px 12px;margin-top:4px}
.library-search button{padding:9px 13px}
.library-search input,.library-search button{min-height:44px;border:1px solid var(--line);border-radius:7px;background:var(--library-surface);color:var(--ink);font:inherit}
.library-search-status{min-height:1.8em;color:var(--muted);font-size:14px}
[hidden]{display:none!important}
@media(prefers-color-scheme:dark){:root{--library-surface:#18242f;--library-bg:#101820;--library-accent:#8bdfc3;--library-tint:#203c35}}
@media(max-width:700px){.library-routes{margin-bottom:26px}.library-nav{gap:0 3px}.library-nav a{padding:0 7px}.library-course-group{margin-bottom:26px}}
@media print{.library-nav,.library-search,.library-search-status{display:none!important}body{background:#fff}.library-route{break-inside:avoid}}
</style>
"""

ROUTES = {
    "home": ("目的から探す", [
        ("Androidの全体像をつかむ", "アプリからOS・機器までを音声付きの32枚で。", "android/slides/index.html"),
        ("設計パターンを動きで理解する", "GoF全23パターンを図・Java・音声で。", "gof/slides/index.html"),
        ("組み込みの設計を検証する", "割込み、DMA、通信、電源断をC11の実習で。", "embedded/guide/index.html#overview"),
    ]),
    "android": ("目的に合う教材", [
        ("初めて学ぶ", "OSとアプリのつながりを概要版で一周する。", "slides/index.html"),
        ("仕組みを読み直す", "ライフサイクル、電源、描画の説明と実習を読む。", "guide/index.html#overview"),
        ("特定の課題を掘り下げる", "30講座から、調査したい仕組みを探す。", "deep-dives/index.html"),
    ]),
    "gof": ("目的に合う教材", [
        ("設計の流れから学ぶ", "役割と呼び出しを音声付きで追う。", "slides/index.html"),
        ("実装と判断を比較する", "Javaのコードや反例を章ごとに読む。", "guide/index.html#start"),
        ("処理の動きを見比べる", "委譲・通知・状態遷移を図ごとに再生する。", "animations/index.html"),
    ]),
    "embedded": ("テーマから読み始める", [
        ("データと周辺機器", "回路・CPU・DMAの境界をつかむ。", "guide/index.html#hardware"),
        ("時間と割込み", "応答時間と資源の待ちを計算する。", "guide/index.html#interrupts"),
        ("電源断に備える", "二つの保存領域から復元する条件を考える。", "guide/index.html#storage-update"),
    ]),
}

NAV = [("home", "トップ", "index.html"), ("android", "Android", "android/index.html"),
       ("gof", "GoF", "gof/index.html"), ("embedded", "組み込み", "embedded/index.html"),
       ("works", "作品集", "works/index.html")]


def route_section(title, links):
    cards = "".join(
        f'<a class="library-route" href="{escape(href, quote=True)}"><strong>{escape(name)}</strong>'
        f'<span>{escape(description)}</span></a>'
        for name, description, href in links
    )
    return (f'<section class="library-routes" aria-labelledby="library-routes-title">'
            f'<h2 id="library-routes-title">{escape(title)}</h2>'
            f'<div class="library-route-grid">{cards}</div></section>')


def managed(html, name, markup, anchor, after=False):
    start, end = f"<!-- {name} -->", f"<!-- /{name} -->"
    html = re.sub(re.escape(start) + r".*?" + re.escape(end), "", html, flags=re.S)
    assert anchor in html, (name, anchor)
    block = start + markup + end
    return html.replace(anchor, anchor + block if after else block + anchor, 1)


def decorate(html, current, prefix, current_kind="page"):
    navigation = '<nav class="library-nav" aria-label="ライブラリ内の移動">'
    for key, label, path in NAV:
        active = f' aria-current="{current_kind}"' if key == current else ''
        navigation += f'<a href="{prefix}{path}"{active}>{label}</a>'
    navigation += '</nav>'
    html = managed(html, 'library-navigation', navigation, '</header>', after=True)
    html = html.replace('<nav class="library-nav"', '<nav class="library-nav wrap"', 1)
    html = managed(html, 'library-style', STYLE, '</head>')
    # These labels repeated the page title or displayed a decorative initial.
    html = re.sub(r'<div class="eyebrow">[^<]*</div>', "", html)
    html = re.sub(r'<div class="card-top">.*?</span></div>', "", html, flags=re.S)
    return html


def polish_landing(html, key):
    html = decorate(html, key, './' if key == 'home' else '../')
    if key in ROUTES:
        anchor = '<section aria-labelledby="guides-title">' if key == 'home' else '<section aria-labelledby="formats-title">'
        html = managed(html, 'library-routes', route_section(*ROUTES[key]), anchor)
    if key == 'works':
        html = re.sub(r'<div class="works-cover [a-z]+" aria-hidden="true"></div>', '', html)
        for title, artwork in [('motion-gallery', 'gallery'), ('observatory', 'observatory'), ('tides', 'tides')]:
            anchor = f'<article class="card" aria-labelledby="{title}-title">'
            html = html.replace(anchor, anchor + f'<div class="works-cover {artwork}" aria-hidden="true"></div>')
    return html


GUIDE_ROUTES = {
    "android": ("図と実習を行き来する", [
        ("全体像を動画で確認", "アプリから機器までの流れを32枚で振り返る。", "../slides/index.html"),
        ("設計検証ノートを読む", "機能の利用条件と実行結果を区別する。", "#workbook-overview"),
        ("項目別の動画を探す", "Binder、保存、音声など30講座から選ぶ。", "../deep-dives/index.html"),
    ]),
    "gof": ("図と実習を行き来する", [
        ("音声付き動画を再生", "全23パターンの役割・実装・反例を追う。", "../slides/index.html"),
        ("類似パターンを比較", "選ぶ根拠を設計上の課題に結び付ける。", "#comparison"),
        ("注文通知の総合演習", "要求追加に合わせて設計案を練る。", "#exercise"),
    ]),
    "embedded": ("基礎から実習へ進む", [
        ("時間の見積りを試す", "処理・待ち・出力の合計を期限と比べる。", "#workbook-overview"),
        ("割込みの応答を考える", "高優先の処理や資源待ちを予算に含める。", "#workbook-interrupts"),
        ("電源断から復元する", "途中で書込みが止まった場合をC11で検証する。", "#workbook-storage-update"),
    ]),
}


def polish_guide(html, key):
    # The reading guides keep their own navigation and page layout.
    style = STYLE.split('.library-routes{', 1)[1].split('.card{', 1)[0]
    css = ('<style id="library-guide-layout">:root{--library-surface:#fff;--library-accent:#075e55}'
           '.library-routes{' + style +
           '@media(prefers-color-scheme:dark){:root{--library-surface:#18242f;--library-accent:#8bdfc3}}'
           '@media print{.library-routes{display:none}}</style>')
    style_id = 'gof-book-styles' if key == 'gof' else 'engineering-workbook-styles'
    anchor = f'<style id="{style_id}">'
    html = managed(html, 'library-guide-style', css, anchor)
    # Place shortcuts after the guide's title and introductory facts.
    html = re.sub(r'<!-- library-guide-routes -->.*?<!-- /library-guide-routes -->', '', html, flags=re.S)
    start = html.index('<main id="main">')
    end = html.index('</div>', html.index('<div class="chips">', start)) + len('</div>')
    if key == 'android':
        end = html.index('</header>', end) + len('</header>')
    routes = '<!-- library-guide-routes -->' + route_section(*GUIDE_ROUTES[key]) + '<!-- /library-guide-routes -->'
    return html[:end] + routes + html[end:]


COURSE_GROUPS = [
    ('platform', 'OSと製品の仕組み', 'overview layers execution boot build os-integration partition-detail'),
    ('apps', 'アプリの実装と状態管理', 'components lifecycle first-app app-design data-practice ipc binder-practice'),
    ('devices', '描画・音声・機器制御', 'graphics audio microphone power hardware-control'),
    ('networks', '通信と車載システム', 'network-security ethernet automotive aaos-detail'),
    ('diagnostics', '障害調査と総合演習', 'faults investigation adb-detail bugreport-detail test-lab walkthrough capstone'),
]

COURSE_TERMS = {
    'ipc': 'プロセス間通信 IPC oneway', 'binder-practice': 'Binder IPC 死亡通知 再bind',
    'lifecycle': '回転 プロセス終了 画面復元', 'power': 'スリープ 休止 WakeLock',
    'audio': '音が出ない スピーカー Audio Focus', 'microphone': '録音 AudioRecord',
    'graphics': 'カクつき jank 描画遅延', 'test-lab': 'Perfetto p95 性能計測',
    'bugreport-detail': 'バグレポート bugreport', 'partition-detail': 'OTA A/B アップデート',
    'network-security': 'ネットワーク TCP/IP TLS', 'ethernet': 'LAN VLAN 有線',
    'aaos-detail': 'Android Automotive OS ゾーン 車載',
}

SEARCH_SCRIPT = r"""
<script>
(() => {
    const form = document.getElementById('course-search');
    const input = document.getElementById('course-query');
    const status = document.getElementById('course-search-status');
    const normalize = value => value.normalize('NFKC').toLocaleLowerCase('ja');
    const groups = Array.from(document.querySelectorAll('.library-course-group'), group => ({
        element: group,
        cards: Array.from(group.querySelectorAll('.card'), card => ({
            element: card,
            text: normalize(card.querySelector('h4').textContent + ' ' +
                card.querySelector('.description').textContent + ' ' + card.dataset.terms + ' ' +
                group.querySelector('h3').textContent)
        }))
    }));
    function filter() {
        const terms = normalize(input.value).trim().split(/\s+/).filter(Boolean);
        let count = 0;
        for (const group of groups) {
            let visible = 0;
            for (const card of group.cards) {
                card.element.hidden = !terms.every(term => card.text.includes(term));
                if (!card.element.hidden) visible++;
            }
            group.element.hidden = visible === 0;
            count += visible;
        }
        status.textContent = count
            ? (terms.length ? count + '件の講座が見つかりました。' : '')
            : '一致する講座がありません。別のキーワードで検索するか、条件をクリアしてください。';
    }
    input.addEventListener('input', filter);
    form.addEventListener('submit', event => event.preventDefault());
    form.addEventListener('reset', () => {
        input.value = '';
        filter();
        input.focus();
    });
    // A heading shortcut should always reveal the target group.
    document.querySelector('.library-groups').addEventListener('click', event => {
        if (event.target.closest('a') && input.value) {
            input.value = '';
            filter();
        }
    });
    form.hidden = false;
    filter();
})();
</script>
"""


def polish_courses(html):
    html = decorate(html, 'android', '../../', 'location')
    cards = {}
    for card in re.findall(r'<article class="card".*?</article>', html, flags=re.S):
        key = re.search(r'aria-labelledby="course-([^"]+)"', card)[1]
        card = card.replace('<article class="card"', f'<article class="card" data-terms="{escape(COURSE_TERMS.get(key, ""), quote=True)}"')
        cards[key] = card.replace('<h3 ', '<h4 ').replace('</h3>', '</h4>')
    group_keys = [key for _, _, ids in COURSE_GROUPS for key in ids.split()]
    assert sorted(group_keys) == sorted(cards), 'Each course must appear in exactly one group'
    search = '''<form class="library-search" id="course-search" role="search" hidden>
<label for="course-query">講座をキーワードで検索<input id="course-query" type="search" placeholder="例：Binder、録音、電源" autocomplete="off"></label>
<button type="reset">条件をクリア</button></form>
<p class="library-search-status" id="course-search-status" role="status"></p>'''
    jumps = '<nav class="library-groups" aria-label="講座の分野">' + ''.join(
        f'<a href="#courses-{key}">{title}</a>' for key, title, _ in COURSE_GROUPS
    ) + '</nav>'
    groups = ''.join(
        f'<section class="library-course-group" id="courses-{key}" aria-labelledby="courses-title-{key}">'
        f'<h3 id="courses-title-{key}">{title}</h3><div class="grid">'
        + ''.join(cards[id_] for id_ in ids.split()) + '</div></section>'
        for key, title, ids in COURSE_GROUPS
    )
    html, count = re.subn(r'<div class="grid">(?=<article class="card").*?</article></div>', lambda _: search + jumps + groups, html, count=1, flags=re.S)
    assert count == 1
    html = html.replace('ひとつの項目を、<br>狭く、深く。', 'Androidの深掘り講座')
    html = html.replace('概要を知った次は、設計と証拠を自分の言葉で。<br>30項目を、それぞれ独立した動画風スライドで学びます。',
                        '調べたい仕組みから30講座を探せます。各講座は日本語の読み上げと設計実習に対応しています。')
    return html.replace('</body>', SEARCH_SCRIPT + '</body>', 1)


def main():
    for key, _, path in NAV:
        target = ROOT / path
        target.write_text(polish_landing(target.read_text(), key))
    for key in GUIDE_ROUTES:
        target = ROOT / key / 'guide/index.html'
        target.write_text(polish_guide(target.read_text(), key))


if __name__ == '__main__':
    main()
