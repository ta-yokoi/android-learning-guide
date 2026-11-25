#!/usr/bin/env python3
"""Insert advanced chapters and the reading map into the data design guide."""

from html import escape
from pathlib import Path
import re

from data_design_advanced import EXTRA_LABS, LAB_OUTPUT, UNITS, WORKED
from data_design_lessons import CHAPTERS as INTRO_CHAPTERS
from data_design_deep_dive import DEEP, DEEP_LABS, DEEP_LAB_OUTPUT

ROOT = Path(__file__).resolve().parent.parent / "data-design"
FIRST_ADVANCED_SLIDE = 1 + sum(len(scenes) for _, _, scenes in INTRO_CHAPTERS)
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
    title, example = WORKED[key]
    worked = f"<h3>{escape(title)}</h3><p>{escape(example)}</p>"
    return (
        f'<section class="chapter" id="{key}" aria-labelledby="{key}-title">\n'
        f'<h2 id="{key}-title">発展{index + 1}. {escape(item["title"])}</h2>\n'
        f'<p class="chapter-video"><a href="../slides/index.html#slide-{number}">この章を動画で見る</a> · <a href="#reading-map">第2版 {escape(item["sources"])}との対応</a></p>\n'
        f'<p class="contract">{escape(item["goal"])}</p>\n{concepts}\n{worked}\n{checks}\n{lab}\n{detailed}\n'
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
        '<h3>方式を確かめる一次資料</h3><ul>'
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
    ) + '</ol><a href="#reading-map">書籍との対応表</a>'
    html = replace_block(html, "advanced-toc", toc, '<a href="#references">参考資料</a>')
    part = ('<div class="hero" id="advanced"><h2>発展編</h2>'
            '<p>ストアの規模と運用条件を変えながら、方式の内部、障害時の制約、データの責任を検討します。</p></div>\n')
    content = part + "\n".join(section(item, index) for index, item in enumerate(UNITS)) + map_section()
    html = replace_block(html, "advanced-chapters", content, '<section id="references"')
    html = re.sub(r"\.chapter:not\(#references\)(?::not\(#reading-map\))*",
                  ".chapter:not(#references):not(#reading-map)", html)
    p.write_text(html)


if __name__ == "__main__":
    main()
