#!/usr/bin/env python3
"""Insert advanced chapters and the reading map into the data design guide."""

from html import escape
from pathlib import Path
import re

from data_design_advanced import EXTRA_LABS, LAB_OUTPUT, UNITS, WORKED
from data_design_experiments import ENGINE_RESULTS, VIDEOS
from data_design_focus import FOCUS, FOCUS_BY_SECTION, LAB_OUTPUT as FOCUS_LAB_OUTPUT
from data_design_learning_path import CSS as LEARNING_CSS, assessment, learning_start
from data_design_topic_map import NOTES, TOPICS
from data_design_workshops import FORMAT_DEPENDENCIES, WORKSHOPS, lab_file
from data_design_section_audit import AUDIT, SUPPLEMENTS, UNIX_EXAMPLE
from data_design_lessons import CHAPTERS as INTRO_CHAPTERS
from data_design_deep_dive import DEEP, DEEP_LABS, DEEP_LAB_OUTPUT

ROOT = Path(__file__).resolve().parent.parent / "data-design"
FIRST_ADVANCED_SLIDE = 1 + sum(len(scenes) for _, _, scenes in INTRO_CHAPTERS)
FIRST_FOCUS_SLIDE = FIRST_ADVANCED_SLIDE + 2 * len(UNITS) + len(VIDEOS)
FIRST_WORKSHOP_SLIDE = FIRST_FOCUS_SLIDE + len(FOCUS)
FIRST_LEARNING_SLIDE = FIRST_WORKSHOP_SLIDE + len(WORKSHOPS)
READING_MAP = [
    ("システム全体の選択", "workloads", "業務と分析、クラウドと自社運用。法規や利用目的は発展編のデータ利用で扱います。"),
    ("期待する品質と負荷", "load-and-recovery", "応答時間、耐障害性、過負荷からの復帰、実行基盤の構成。"),
    ("データの構造と問合せ", "models", "関係、文書、グラフ、分析スキーマ、イベントと読取りモデル。"),
    ("保存と探索の内部", "engines", "Bツリー、LSM、列指向、全文とベクトル検索。"),
    ("データ形式の互換性", "contracts", "JSON、Protobuf、Avro、呼出しとワークフロー。"),
    ("複製方式の選択", "replica-choices", "単一・複数リーダーとリーダーレス、遅延と競合。"),
    ("データの担当割り", "routing", "範囲とハッシュ、再配置、ルーティングと二次索引。"),
    ("取引と並行性", "isolation", "分離レベル、更新異常、二相ロックと二相コミット。"),
    ("時間と部分障害", "clocks", "時計の用途、停止と遅延、リースとフェンシング。"),
    ("外から見た順序と合意", "order-and-agreement", "線形化可能性、論理時計、任期と多数派。"),
    ("固定した入力の集計", "batch-pipelines", "入力の版、局所集約とシャッフル、再実行。"),
    ("連続入力の処理と復旧", "stream-recovery", "ログ、CDC、結合、位置と副作用の復元。"),
    ("導出データをつなぐ設計", "integration", "正本と投影の切替、鮮度と完全性、端から端までの検証。"),
    ("データ利用への責任", "data-responsibility", "目的と保持、削除伝播、推薦の偏りと説明責任。"),
]


def link(key, title):
    return f'<a href="#{escape(key)}">{escape(title)}</a>'


def table(caption, headings, rows):
    header = "".join(f'<th scope="col">{escape(h)}</th>' for h in headings)
    return (
        f'<div class="table-wrap" tabindex="0" role="region" aria-label="{escape(caption)}">'
        f'<table><caption>{escape(caption)}</caption><thead><tr>{header}</tr></thead>'
        f'<tbody>{rows}</tbody></table></div>'
    )


def lab_html(lab):
    output, note = LAB_OUTPUT[lab] if lab in LAB_OUTPUT else DEEP_LAB_OUTPUT[lab]
    assert (ROOT / "labs" / lab).is_file()
    return (
        f'<h3>実行実習</h3><p><a href="../labs/{lab}" download>{lab}をダウンロード</a>し、'
        '保存したディレクトリで実行してください。</p>'
        f'<pre tabindex="0"><code>python3 {escape(lab)}\n{escape(output)}</code></pre><p>{escape(note)}</p>'
    )


def engine_experiment(slide):
    rows = "".join("<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in row) + "</tr>"
                   for row in ENGINE_RESULTS)
    assert (ROOT / "labs/engine_benchmark.py").is_file()
    return (
        '<h3 id="engine-benchmark">SQLiteとRocksDBの実測</h3>'
        f'<p class="chapter-video"><a href="../slides/index.html#slide-{slide}">比較を動画で見る</a></p>'
        '<p>8,192キーと512バイトの値を使い、一点読取りまたは16件をまとめて同期書込みする操作を'
        '同じ順序で1,600回実行します。SQLiteはWALとFULL同期、RocksDBはWALと同期書込みを有効にして圧縮を無効にします。'
        '操作のうち書込みバッチを選ぶ確率を10％と60％、ページキャッシュまたはブロックキャッシュの設定値を256と4,096 KiBに変えます。'
        'この設定値は、エンジン全体のメモリ使用量をそろえるものではありません。</p>'
        '<p><a href="../labs/engine_benchmark.py" download>engine_benchmark.pyをダウンロード</a>し、Python 3.9以降で実行します。'
        'SQLiteだけなら追加パッケージは不要です。比較には仮想環境でRocksDBのPythonバインディングを入れます。'
        '次のコマンドはLinux・macOS向けです。</p>'
        '<pre tabindex="0"><code>python3 -m venv .venv\n.venv/bin/python -m pip install rocksdict==0.3.29\n'
        'for cache in 256 4096; do\n  for writes in 10 60; do\n    for seed in 42 43 44; do\n'
        '      for engine in sqlite rocksdb; do\n'
        '        .venv/bin/python engine_benchmark.py "$engine" --cache-kib "$cache" --write-percent "$writes" --seed "$seed"\n'
        '      done\n    done\n  done\ndone</code></pre>'
        '<p>各条件で3回測り、各回のp95とI/Oの中央値を掲載しています。SQLite 3.53.1、rocksdict 0.3.29を使用。'
        'LinuxのOSキャッシュを保持したまま測定し、12組すべてで両方式の全キーを照合しました。</p>'
        + table("同じ操作列を流した際の実測例",
                ["キャッシュ KiB", "書込み率", "エンジン", "一点読取り p95 µs", "書込みバッチ p95 µs", "書込み I/O MiB"], rows)
        + '<p>この環境ではSQLiteの一点読取りが短く、RocksDBの書込みI/Oが少なくなりました。'
        'キャッシュ拡大で改善幅が異なり、RocksDBの書込み60％条件では読取りのp95は短縮しませんでした。'
        '書込み量は最後のフラッシュを含むLinuxのプロセスI/Oです。読取りI/Oは全条件で0 MiBでした。'
        'OSのキャッシュを経た実測であり、物理ドライブの読取り量・寿命やコンパクション完了後の書込み量を表すものではありません。'
        '実習はp50・p99、ファイルサイズと最終状態のSHA-256も出力します。'
        '採用時は実データの偏り、並行アクセス、十分な実行時間、再起動後の冷えたキャッシュを含めて測り直します。</p>'
    )


def raft_experiment(slide):
    return (
        '<h3 id="raft-failure-lab">分断の反復とスナップショットによる復帰</h3>'
        f'<p class="chapter-video"><a href="../slides/index.html#slide-{slide}">復帰の手順を動画で見る</a></p>'
        '<p>同じ<a href="../labs/raft_recovery.py" download>raft_recovery.py</a>をシナリオ指定付きで実行します。</p>'
        '<pre tabindex="0"><code>python3 raft_recovery.py --partitions\n'
        'quorum lost: no election or commit\n'
        "second partition: stale log resisted; term 5 committed ['order-42', 'order-43']\n"
        "snapshot installed at: 2\nstate after replay: ['order-42', 'order-43', 'order-44']</code></pre>"
        '<ol><li>A、B、Cの通信が途切れ、Aの単独書込みは確定せず、C単独の投票でも新リーダーを選べません。</li>'
        '<li>BとCがつながり注文42を確定します。次の分断では古いログのAが選挙に敗れ、任期5のCがAと注文43を確定します。'
        '遅れて届く任期3の書込みは拒否されます。</li>'
        '<li>Cは確定位置2までを圧縮し、位置とその任期を状態と一緒に保持します。'
        '位置1までしか持たないBは再起動後、位置2のスナップショットを受け取ります。</li>'
        '<li>Bは位置3の注文44をログから適用します。位置2までを再適用せず、注文3件と順番が一致します。</li></ol>'
        '<p>確定前の操作はスナップショットに含めません。このモデルではディスク状態の置換を一操作とし、'
        '選挙タイマー、転送の中断、実ストレージの電源断は扱いません。</p>'
    )


def coverage_table():
    rows = []
    focused = set()
    for chapter, (anchor, sections) in enumerate(AUDIT, 1):
        for section, (name, *coverage) in enumerate(sections, 1):
            number = f"{chapter}.{section}"
            if coverage:
                note, *target = coverage
                destination = target[0] if target else anchor
            else:
                lesson = FOCUS_BY_SECTION[number]
                assert lesson.chapter + "-details" == anchor
                focused.add(number)
                note, destination = lesson.audit, lesson.anchor
            rows.append(f'<tr><th scope="row">{number}</th><td>{link(destination, name)}</td>'
                        f'<td>{escape(note)}</td></tr>')
    assert focused == FOCUS_BY_SECTION.keys()
    return (
        '<h3 id="section-audit">公開目次の節別照合</h3>'
        f'<p>第2版の章末まとめを除いた{len(rows)}節すべてに、独自の具体例または実習があります。'
        '節の名前から対応する本文に移動できます。集計は節単位です。節内の小項目、原典の事例や論証は原典を参照してください。</p>'
        + table("節ごとの教材範囲", ["節", "主題", "教材の範囲"], "".join(rows))
    )


def supplement(key):
    anchor, title, steps, question, answer = SUPPLEMENTS[key]
    description = "".join(f"<dt>{escape(name)}</dt><dd>{escape(body)}</dd>" for name, body in steps)
    demo = f'<pre tabindex="0"><code>{escape(UNIX_EXAMPLE)}</code></pre>' if key == "batch-pipelines" else ""
    return (
        f'<h3 id="{anchor}">{escape(title)}</h3><dl class="mechanism">{description}</dl>{demo}'
        f'<details><summary>{escape(question)}</summary><p>{escape(answer)}</p></details>'
    )


def focus_lesson(lesson, slide):
    phases = "".join(f"<dt>{escape(label)}</dt><dd>{escape(body)}</dd>"
                     for label, body in zip(lesson.labels, lesson.explanation))
    demo = ""
    if lesson.lab:
        assert (ROOT / "labs/section_examples.py").is_file()
        demo = (
            '<p><a href="../labs/section_examples.py" download>実習ファイルを取得</a>し、'
            'Python 3.9以降で実行してください。</p>'
            f'<pre tabindex="0"><code>python3 section_examples.py {lesson.lab}\n'
            f'{escape(FOCUS_LAB_OUTPUT[lesson.lab])}</code></pre>'
        )
    label, url = lesson.source
    return (
        f'<h3 id="{lesson.anchor}">{lesson.section} {escape(lesson.title)}</h3>'
        f'<p class="chapter-video"><a href="../slides/index.html#slide-{slide}">この節の詳説を動画で見る</a></p>'
        f'<dl class="mechanism">{phases}</dl>'
        f'<p><strong>設計判断</strong>　{escape(lesson.tradeoff)}</p>'
        f'<p><strong>検証すること</strong>　{escape(lesson.check)}</p>{demo}'
        f'<details><summary>{escape(lesson.question)}</summary><p>{escape(lesson.answer)}</p></details>'
        f'<p><a href="{escape(url, quote=True)}">{escape(label)}</a></p>'
    )


def workshop_html(workshop, slide):
    steps = "".join(f"<li>{escape(body)}</li>" for body in workshop.walkthrough)
    reviews = "\n".join(f"<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>"
                         for q, a in workshop.exercises)
    lab = ""
    if workshop.lab:
        script = lab_file(workshop)
        assert (ROOT / "labs" / script).is_file()
        command = f"python3 {script} {workshop.lab}"
        instructions = "取得先で次のコマンドを実行します。"
        if dependency := FORMAT_DEPENDENCIES.get(workshop.lab):
            instructions += "仮想環境を作る例はLinux・macOS向けです。"
            command = ("python3 -m venv .venv\n"
                       f".venv/bin/python -m pip install {dependency}\n"
                       f".venv/bin/python {script} {workshop.lab}")
        lab = (
            f'<p><a href="../labs/{script}" download>{script}を取得</a>してください。'
            f'{instructions}</p>'
            f'<pre tabindex="0"><code>{escape(command)}</code></pre>'
            f'<p>出力例</p><pre tabindex="0"><code>{escape(workshop.output)}</code></pre>'
        )
    source, url = workshop.source
    return (
        f'<h3 id="{workshop.anchor}">{escape(workshop.title)}</h3>\n'
        f'<p class="chapter-video"><a href="../slides/index.html#slide-{slide}">図と読み上げで手順を追う</a></p>'
        f'<ol>{steps}</ol><p><strong>検証・提出すること</strong>　{escape(workshop.criterion)}</p>\n'
        f'{lab}{reviews}<p><a href="{escape(url, quote=True)}">{escape(source)}</a></p>\n'
    )


def workshop_map():
    entries = "".join(f"<li>{link(item.anchor, item.title)}</li>" for item in WORKSHOPS)
    rows = []
    topic_count = 0
    for section, first, last, target, subject, scope in TOPICS:
        numbers = f"{section}.{first}" if first == last else f"{section}.{first}〜{section}.{last}"
        topic_count += last - first + 1
        rows.append(f'<tr><th scope="row">{numbers}</th><td>{link(target, subject)}</td>'
                    f'<td>{escape(scope)}</td></tr>')
    return (
        f'<h3 id="design-workshops">設計・検証ワークショップ</h3><p>実行結果を予想してから試し、'
        '結果を使って設計案を比較します。最後の注文基盤では複数章の知識を組み合わせます。</p>'
        f'<ol>{entries}</ol><h3 id="topic-map">節内の論点と参照先</h3>'
        f'<p>公開目次の3段階目に番号がある{topic_count}項目を、連続する番号ごとにまとめています。'
        '題材に対応する説明、実習、設計レビューへの入口と、それぞれの検証範囲を示します。</p>'
        + table("節内の論点", ["番号", "論点と参照先", "扱う範囲"], "".join(rows))
    )


def section(item, index):
    number = index + FIRST_ADVANCED_SLIDE
    key = item["key"]
    concepts = "".join(f"<h3>{escape(title)}</h3><p>{escape(body)}</p>" for title, body in item["concepts"])
    cases = "".join(
        "<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in row) + "</tr>"
        for row in item["cases"]
    )
    checks = table("設計を試す入力と合格条件", ["ケース", "試すこと", "観測する結果"], cases)
    lab_names = ([item["lab"]] if item["lab"] else []) + EXTRA_LABS.get(key, [])
    lab = "".join(lab_html(name) for name in lab_names)
    detailed_slide = FIRST_ADVANCED_SLIDE + len(UNITS) + index
    deep_title, steps, tradeoff, exercise, solution = DEEP[key]
    walk = "".join(f"<dt>{escape(name)}</dt><dd>{escape(body)}</dd>" for name, body in steps)
    example_lab = lab_html(DEEP_LABS[key]) if key in DEEP_LABS else ""
    detailed = (
        f'<h3 id="{key}-details">{escape(deep_title)}</h3>'
        f'<p class="chapter-video"><a href="../slides/index.html#slide-{detailed_slide}">仕組みを図で追う動画</a></p>'
        f'<dl class="mechanism">{walk}</dl><p><strong>採用条件と代償</strong>　{escape(tradeoff)}</p>'
        f'{example_lab}<details><summary>{escape(exercise)}</summary><p>{escape(solution)}</p></details>'
    )
    first_experiment_slide = FIRST_ADVANCED_SLIDE + 2 * len(UNITS)
    experiments = {"engines": engine_experiment, "order-and-agreement": raft_experiment}
    extra = experiments[key](first_experiment_slide + (key == "order-and-agreement")) if key in experiments else ""
    additional = supplement(key) if key in SUPPLEMENTS else ""
    focused = "".join(focus_lesson(lesson, FIRST_FOCUS_SLIDE + offset)
                      for offset, lesson in enumerate(FOCUS) if lesson.chapter == key)
    workshops = "".join(workshop_html(item, FIRST_WORKSHOP_SLIDE + offset)
                        for offset, item in enumerate(WORKSHOPS) if item.chapter == key)
    notes = "".join(f'<h3 id="{anchor}">{escape(title)}</h3><p>{escape(body)}</p>\n'
                    for anchor, title, body in NOTES.get(key, ()))
    title, example = WORKED[key]
    worked = f"<h3>{escape(title)}</h3><p>{escape(example)}</p>"
    return (
        f'<section class="chapter" id="{key}" aria-labelledby="{key}-title">\n'
        f'<h2 id="{key}-title">発展{index + 1}. {escape(item["title"])}</h2>\n'
        f'<p class="chapter-video"><a href="../slides/index.html#slide-{number}">この章を動画で見る</a> · <a href="#reading-map">第2版 {escape(item["sources"])}との対応</a></p>\n'
        f'<p class="contract">{escape(item["goal"])}</p>\n{concepts}\n{worked}\n{checks}\n{lab}\n{detailed}\n{extra}{additional}{focused}\n{notes}{workshops}\n'
        f'<h3>設計レビュー</h3><details><summary>{escape(item["question"])}</summary>'
        f'<p>{escape(item["answer"])}</p></details>\n</section>'
    )


def map_section():
    rows = "".join(
        f'<tr><th scope="row">{index + 1}章</th><td>{link(key, label)}</td><td>{escape(scope)}</td></tr>'
        for index, (label, key, scope) in enumerate(READING_MAP)
    )
    return (
        '<section id="reading-map" class="chapter" aria-labelledby="reading-map-title">'
        '<h2 id="reading-map-title">第2版と合わせて読むための対応表</h2>'
        '<p>公開目次の14章それぞれに、注文システムを使った学習入口を設けています。'
        'ここで扱う技術の範囲は表に示しています。製品別の実装、アルゴリズムの完全な証明、個別の論文や事例は原典を参照してください。</p>'
        + table("書籍の章番号と発展編", ["書籍", "教材の入口", "この教材で扱う内容"], rows)
        + '<p><a href="https://www.oreilly.co.jp/books/9784814401802/">オライリー・ジャパンの公式目次と書誌情報</a></p>'
        + coverage_table() + workshop_map()
        + '<h3>方式を確かめる一次資料</h3><ul>'
        '<li>索引内部とコンパクション。<a href="https://github.com/facebook/rocksdb/wiki/Leveled-Compaction">RocksDBの設計資料</a></li>'
        '<li>書き手と読み手のスキーマ解決。<a href="https://avro.apache.org/docs/1.12.0/specification/">Apache Avro仕様</a></li>'
        '<li>製品の分離レベルと再試行条件。<a href="https://www.postgresql.org/docs/current/transaction-iso.html">PostgreSQL公式文書</a></li>'
        '<li>任期、投票、ログの確定。<a href="https://raft.github.io/raft.pdf">Raftの原論文</a></li>'
        '<li>キー間で処理を分ける分散バッチ。<a href="https://research.google/pubs/mapreduce-simplified-data-processing-on-large-clusters/">MapReduceの原論文</a></li>'
        '</ul></section>'
    )


def replace_block(html, name, content, anchor):
    start, end = f"<!-- {name} -->", f"<!-- /{name} -->"
    html = re.sub(re.escape(start) + r".*?" + re.escape(end), "", html, flags=re.S)
    assert anchor in html
    return html.replace(anchor, start + "\n" + content + end + anchor, 1)


def main():
    p = ROOT / "guide/index.html"
    html = p.read_text()
    toc = "<strong>発展編</strong><ol>" + "".join(
        f'<li>{link(item["key"], item["title"])}</li>' for item in UNITS
    ) + '</ol><a href="#reading-map">書籍との対応表</a> · <a href="#section-audit">49節の対応</a> · <a href="#design-workshops">設計・検証ワークショップ</a>'
    html = replace_block(html, "learning-css", f"<style>\n{LEARNING_CSS}</style>\n", "</head>")
    html = replace_block(html, "learning-toc",
                         '<strong>学習コース</strong><a href="#learning-path">学習順と初回実習</a>'
                         '<a href="#design-assessment">到達度チェック</a>\n', '<strong>入門編</strong>')
    html = replace_block(html, "learning-start", learning_start(FIRST_LEARNING_SLIDE),
                         '<section id="requirements"')
    html = replace_block(html, "advanced-toc", toc, '<a href="#references">参考資料</a>')
    part = ('<div class="hero" id="advanced"><h2>発展編</h2>'
            '<p>ストアの規模と運用条件を変えながら、方式の内部、障害時の制約、データの責任を検討します。</p></div>\n')
    content = (part + "\n".join(section(item, index) for index, item in enumerate(UNITS))
               + assessment(FIRST_LEARNING_SLIDE + 1) + map_section())
    html = replace_block(html, "advanced-chapters", content, '<section id="references"')
    html = re.sub(r"\.chapter:not\(#references\)(?::not\(#reading-map\))*",
                  ".chapter:not(#references):not(#reading-map)", html)
    p.write_text(html)


if __name__ == "__main__":
    main()
