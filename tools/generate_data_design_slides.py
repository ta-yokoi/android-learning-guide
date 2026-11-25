#!/usr/bin/env python3
"""Generate a self-contained video-style companion to the data design guide."""

from html import escape
import json
from pathlib import Path
import re

from android_progress_transfer import JS as TRANSFER_JS
from android_slide_diagrams import SVG
from android_slide_fullscreen import JS as FULLSCREEN_JS
from android_slide_narration import CONTROLS, SETTINGS
from android_slide_presentation import CASE_HTML, JS as DIRECTION_JS, OPENING, RECAP
from data_design_advanced import UNITS, VIDEO
from data_design_deep_dive import DEEP, DEEP_LABS, DEEP_VIDEO
from data_design_experiments import VIDEOS
from data_design_focus import FOCUS
from data_design_learning_path import LEARNING_VIDEOS
from data_design_workshops import WORKSHOPS, lab_file
from data_design_lessons import CHAPTERS as INTRO_CHAPTERS
import generate_android_slides as player

ROOT = Path(__file__).resolve().parent.parent / "data-design"
STEP = 8
CHAPTERS = INTRO_CHAPTERS + [
    (item["key"], "発展 " + str(index + 1) + " " + item["title"], [
        (VIDEO[item["key"]][0], "parallel" if item["key"] == "isolation" else "timeline",
         *VIDEO[item["key"]][1:], item["question"], item["answer"]),
    ])
    for index, item in enumerate(UNITS)
]
CHAPTERS += [
    (item["key"] + "-details", "詳説 " + str(index + 1), [
        (DEEP[item["key"]][0], "timeline", *DEEP_VIDEO[item["key"]], *DEEP[item["key"]][-2:]),
    ])
    for index, item in enumerate(UNITS)
]
CHAPTERS += [(chapter, name, [tuple(scene[:-1])]) for chapter, name, *scene in VIDEOS]
CHAPTERS += [
    (lesson.anchor, "節 " + lesson.section, [
        (lesson.title, lesson.kind, lesson.labels, lesson.captions, lesson.question, lesson.answer),
    ])
    for lesson in FOCUS
]
CHAPTERS += [
    (item.anchor, "実践 " + str(index + 1), [
        (item.title, item.kind, item.labels, item.captions, *item.exercises[0]),
    ])
    for index, item in enumerate(WORKSHOPS)
]
CHAPTERS += [(chapter, name, [tuple(scene[:-1])]) for chapter, name, *scene in LEARNING_VIDEOS]
SCENE_COUNT = sum(len(scenes) for _, _, scenes in CHAPTERS)
TOTAL_SECONDS = SCENE_COUNT * 4 * STEP
DURATION = f"{TOTAL_SECONDS // 60}分{TOTAL_SECONDS % 60:02d}秒"
ACCENTS = ["#c4ef9b", "#b5d7ff", "#f4d39d", "#9fe1d7"]
EXPERIMENTS = {
    "transactions": "inventory.py",
    "uncertainty": "payment_retry.py",
    "analytics": "sales_events.py",
}
CHAPTER_NOTES = {
    "requirements": "測定条件と数値は架空のストアの受入基準です。注文の成功率と対象障害を指定してから、遅延や復旧の時間を比較します。",
    "storage": "索引の計画はSQLiteの例です。採用する製品では、実データに近い分布で読み取りと書き込みの両方を測ります。",
    "schema": "出荷元を補えるのは根拠のある注文だけです。制約を強める前に、旧版が書き込んだデータも照合します。",
    "distribution": "複製は同じデータの写しを維持し、分割はデータの担当を振り分けます。履歴の鮮度と分割先ごとの負荷を別々に測ります。",
    "transactions": "在庫実習は単一SKUの条件付き更新を検証します。予約行の作成や複数SKUの一括予約は、実サービスの取引で追加試験します。",
    "uncertainty": "決済実習はメモリ上のモデルです。実サービスに適用する際は、決済先のキー保持期限、状態照会、並行要求の扱いを確認します。",
    "analytics": "集計実習では固定の締め日を使います。本番ではタイムゾーン、訂正版の公開方法、元イベントの保持期間を決めます。",
    "capstone": "障害を注入した後は、表示だけで合否を決めず、予約行、請求記録、集計に使ったイベントIDを照合します。",
}
ADVANCED_LABS = {item["key"]: item["lab"] for item in UNITS if item["lab"]}
CHAPTER_NOTES.update({item["key"]: item["goal"] for item in UNITS})
CHAPTER_NOTES.update({key + "-details": value[2] for key, value in DEEP.items()})
ADVANCED_LABS.update({key + "-details": lab for key, lab in DEEP_LABS.items()})
CHAPTER_NOTES.update({entry[0]: entry[-1] for entry in VIDEOS})
ADVANCED_LABS.update({"engine-benchmark": "engine_benchmark.py", "raft-failure-lab": "raft_recovery.py"})
CHAPTER_NOTES.update({lesson.anchor: lesson.tradeoff for lesson in FOCUS})
ADVANCED_LABS.update({lesson.anchor: "section_examples.py" for lesson in FOCUS if lesson.lab})
CHAPTER_NOTES.update({item.anchor: item.criterion for item in WORKSHOPS})
ADVANCED_LABS.update({item.anchor: lab_file(item) for item in WORKSHOPS if item.lab})
CHAPTER_NOTES.update({entry[0]: entry[-1] for entry in LEARNING_VIDEOS})
DIAGRAM_NAMES = {
    "flow": "手順と判断",
    "timeline": "時系列",
    "compare": "条件と選択の比較",
    "parallel": "二つの処理の流れ",
    "matrix": "四つの検証観点",
}
READINGS = [
    ["p95", "ピー九十五"], ["SQL", "エスキューエル"], ["SQLite", "エスキューライト"],
    ["SKU", "エスケーユー"], ["NULL", "ヌル"], ["UPDATE", "アップデート"],
    ["API", "エーピーアイ"], ["ID", "アイディー"], ["DB", "データベース"],
    ["CHECK", "チェック"], ["Raft", "ラフト"], ["LSM", "エルエスエム"], ["CDC", "シーディーシー"], ["W02", "ダブリューゼロツー"],
    ["RPC", "アールピーシー"], ["ACID", "アシッド"], ["UUID", "ユーユーアイディー"],
    ["Parquet", "パーケー"], ["DuckDB", "ダックディービー"], ["Protobuf", "プロトバフ"],
]
CSS = """
.data-reader>summary{margin:1.5rem 0;font-weight:650;color:var(--ink)}
.data-course .data-reader .fallback{display:block}
.data-reader .static-diagram{overflow:auto}
.data-reader .static-diagram>svg{min-width:520px}
.data-download{margin:1rem 0}
.data-course .chapters-strip{flex-wrap:nowrap}
.data-course .chapter-link{flex:0 0 148px}
.data-course .cue-box{min-height:0}
.data-course .diagram[data-kind="parallel"] .edge-path{stroke-dasharray:7 4}
@media print{
    .data-reader>summary{display:none}
    .data-reader .static-diagram{overflow:visible}
    .data-reader .static-diagram>svg{min-width:0}
}
"""


def diagram(prefix, kind, labels):
    svg = SVG(prefix)
    if kind in ("flow", "timeline"):
        for i, label in enumerate(labels):
            x = 8 + i * 225
            svg.node(i, x, 70, 206, 90, label, "state" if kind == "timeline" else "component")
            if i < 3:
                svg.edge(i + 1, f"M{x + 206} 115H{x + 224}")
        if kind == "timeline":
            svg.text(450, 210, "時間の流れ →")
    else:
        if kind != "matrix":
            svg.region(8, 5, 884, 108, "")
            svg.region(8, 127, 884, 108, "")
        for i, label in enumerate(labels):
            x, y = 28 + (i % 2) * 467, 24 + (i // 2) * 122
            svg.node(i, x, y, 377, 70, label, "box" if kind == "compare" else "component")
            if i % 2 == 0 and kind != "matrix":
                svg.edge(i + 1, f"M{x + 377} {y + 35}H{x + 467}")
    return svg.finish()


def lessons():
    data, modules, static = [], [], []
    guide = (ROOT / "guide/index.html").read_text()
    for module, (chapter, name, scenes) in enumerate(CHAPTERS):
        assert f'id="{chapter}"' in guide
        first = len(data)
        accent = ACCENTS[module % len(ACCENTS)]
        for offset, (title, kind, labels, steps, question, answer) in enumerate(scenes):
            index = len(data) + 1
            assert len(labels) == len(steps) == 4
            diagram_label = DIAGRAM_NAMES[kind]
            lab = ADVANCED_LABS.get(chapter) or (EXPERIMENTS.get(chapter) if offset == 1 else None)
            if lab:
                assert (ROOT / "labs" / lab).is_file()
            ref = f"../guide/index.html#{chapter}"
            detail = (
                f'<p class="data-download"><a href="../labs/{lab}" download>{lab}を取得</a>。'
                '実行方法と結果の読み方は本文で確認できます。</p>' if lab else ""
            )
            frames = [
                {"status": f"段階{i + 1}", "value": label, "detail": step}
                for i, (label, step) in enumerate(zip(labels, steps))
            ]
            data.append({
                "chapter": chapter, "title": title, "nodes": labels, "steps": steps,
                "note": CHAPTER_NOTES[chapter],
                "question": question, "answer": answer, "svg": diagram(f"scene-{index}", kind, labels),
                "diagramType": kind, "diagramLabel": diagram_label, "detail": detail,
                "module": {"name": name, "index": module + 1, "accent": accent},
                "direction": {"hook": title, "takeaway": steps[-1], "kind": "check",
                              "label": "設計上の観測点", "frames": frames},
            })
            step_list = "".join(f"<li>{escape(step)}</li>" for step in steps)
            figure = diagram(f"static-{index}", kind, labels)
            figure_label = escape(diagram_label + "。 " + "、".join(labels))
            static.append(
                f'<article id="slide-{index}"><h2>{index}. {escape(title)}</h2>'
                f'<div class="static-diagram" role="img" aria-label="{figure_label}" tabindex="0">{figure}</div>'
                f'<ol>{step_list}</ol><p>{escape(CHAPTER_NOTES[chapter])}</p><p><strong>確認問題</strong>　{escape(question)}</p>'
                f'<p><strong>解答</strong>　{escape(answer)}</p>{detail}<a href="{ref}">対応する本文を読む</a></article>'
            )
        modules.append({"name": name, "first": first, "last": len(data) - 1, "accent": accent})
    return data, modules, static


def build_script(data, modules):
    script = player.JS.removesuffix("\n" + TRANSFER_JS)
    script = re.sub(r" window.addEventListener\('android-learning-progress-imported'.*?\n", "", script)
    script = script.replace("STEP=6,DURATION=24", f"STEP={STEP},DURATION={STEP * 4}")
    script = script.replace("android-animated-slides-player-v1", "data-design-slides-player-v1")
    script = script.replace("android-narration-preferences-v1", "data-design-narration-preferences-v1")
    script = script.replace("initHomeApp();", "").replace("__HOME_JS__", "")
    script = script.replace("Androidの仕組みを、音声と図で学びます。", "注文データの設計を、音声と図で学びます。")
    script = re.sub(r" const pronunciations=\[.*?\];",
                    " const pronunciations=" + json.dumps(READINGS, ensure_ascii=False) + ";", script)
    script = script.replace("prepareCase(slide);", "prepareCase(slide);$('lab-link').innerHTML=slide.detail;")
    script = script.replace("'input,select,button,a,summary,textarea'", "'input,select,button,a,summary,textarea,.data-reader'")
    script = script.replace(" DATA.forEach", """
 const reader=$('data-reader');
 // Leave the chapter targets available in the HTML-only reader. In player mode,
 // the same hashes select scenes without jumping down to the static copy.
 reader.querySelectorAll('article[id]').forEach(article=>{article.id='static-'+article.id});
 reader.open=false;
 reader.addEventListener('toggle',()=>{if(reader.open)pause()});
 let readerBeforePrint;
 window.addEventListener('beforeprint',()=>{if(readerBeforePrint!==undefined)return;readerBeforePrint=reader.open;pause();reader.open=true});
 window.addEventListener('afterprint',()=>{if(readerBeforePrint!==undefined)reader.open=readerBeforePrint;readerBeforePrint=undefined});
 DATA.forEach""", 1)
    direction = DIRECTION_JS.replace(
        "['01 / 着眼点','02 / 仕組みを追う','03 / 観測する','04 / 持ち帰る要点'][s]",
        "'段階 '+(s+1)+' / 4'",
    )
    return (
        script.replace("__DIRECTION_JS__", direction.replace("__MODULES__", json.dumps(modules, ensure_ascii=False)))
        .replace("__FULLSCREEN_JS__", FULLSCREEN_JS)
        .replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c"))
    )


def main():
    data, modules, static = lessons()
    template = player.TEMPLATE
    labels = {
        "Android 16の30章を動く図と字幕で振り返る、16:9のスライド教材。全32枚、自動再生とスマートフォン全画面に対応。":
            f"注文システムの入門と発展テーマを動く図と音声で学ぶ{SCENE_COUNT}場面の教材。",
        "Androidを動く図で学ぶ｜スライド教材": "データ指向アプリケーション設計｜音声付き動画版",
        "← Androidの教材一覧": "← データ設計の教材一覧",
        "元のAndroid教材を読む": "通常教材を読む",
        "ANDROID 16 / MOTION LESSONS": "データ設計の動画版",
        "Androidを、<br>動く図で学ぶ。": "注文システムで学ぶ<br>データ設計",
        "身近な疑問から、図と実例で仕組みを追う32レッスン。": f"入門・発展・詳説の{SCENE_COUNT}場面で、設計と検証を追います。",
        "字幕のみは約13分": f"字幕のみは{DURATION}",
        "Androidスライドプレーヤー": "データ設計スライドプレーヤー",
        "Androidの教材一覧へ戻る": "データ設計の教材一覧へ戻る",
        "Android 16 / 図は説明用に簡略化しています": "注文・在庫・決済・売上集計",
        '<body>': '<body class="data-course">',
        '<div class="text-links"><a id="reference"': '<div id="lab-link"></div><div class="text-links"><a id="reference"',
        '<section class="fallback" id="all-slides"': f'<details class="data-reader" id="data-reader" open><summary>全{SCENE_COUNT}場面を静止版で読む</summary><section class="fallback" id="all-slides"',
        '__FALLBACK__</section>': '__FALLBACK__</section></details>',
    }
    for old, new in labels.items():
        assert old in template, old
        template = template.replace(old, new)
    opening = (OPENING.replace("ANDROID 16 / VISUAL LESSONS", "データ設計")
               .replace("Androidを、<br><em>仕組み</em>で理解する。", "注文の流れから<br><em>データ設計</em>を学ぶ")
               .replace("要求を追う。状態を分ける。証拠で説明する。", "注文処理から、合意・集計・データ利用まで学びます。")
               .replace("32 LESSONS", f"22章・{SCENE_COUNT}場面"))
    slots = {
        "CSS": player.CSS + player.PLAYER_PALETTE + CSS, "FALLBACK": "\n".join(static),
        "STEP_BUTTONS": "".join(f'<button type="button" data-step="{i}" aria-label="段階{i+1}へ移動" aria-pressed="false">{i+1}</button>' for i in range(4)),
        "JS": build_script(data, modules), "CASE_HTML": CASE_HTML, "OPENING": opening,
        "RECAP": RECAP, "SPEECH_CONTROLS": CONTROLS, "SPEECH_SETTINGS": SETTINGS,
        "HOME_HEAD": "", "HOME_GUIDE": "", "TRANSFER_HTML": "",
    }
    for key, value in slots.items():
        template = template.replace(f"__{key}__", value)
    assert not re.search(r"__[A-Z_]+__", template)
    target = ROOT / "slides/index.html"
    target.parent.mkdir(exist_ok=True)
    target.write_text(template)
    print(f"Generated {len(data)} scenes and {len(data) * 4} stages.")


if __name__ == "__main__":
    main()
