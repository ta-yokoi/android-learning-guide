"""Guided learning path and self-assessment for the data design guide."""

from html import escape


STEPS = (
    ("守る条件を決める", "どの操作が、どの失敗に耐える必要があるかを言葉にします。",
     (("requirements", "要件の決め方"), ("tail-amplification", "遅延と成功率の実習")),
     "「今日の閲覧数が1分遅れる」と「確定した注文が消える」で、許容する条件を分けられる。"),
    ("データの形と探し方を選ぶ", "同じ注文でも、購入履歴と倉庫検索では読む単位が異なります。",
     (("storage", "モデルと索引"), ("schema", "スキーマを変える"), ("covering-index-plan", "実行計画の実習")),
     "注文ID・商品ID・購入時の単価をどこに置くか決め、必要な索引と書込み費用を説明できる。"),
    ("同時実行と再試行を扱う", "在庫を減らす取引と、応答が届かないときの再送を分けて考えます。",
     (("transactions", "在庫と取引"), ("uncertainty", "応答が失われた決済"), ("isolation-details", "分離レベル")),
     "残り1個の同時注文で成功が1件となり、同じ要求を再送しても二重に減算されない理由を示せる。"),
    ("複製・分割・復旧を設計する", "コピーを増やす目的と、担当を分ける目的を区別し、停止時に確定できる範囲を決めます。",
     (("distribution", "複製と分割"), ("replica-choices-details", "複製方式"), ("raft-failure-lab", "分断と復帰")),
     "3台のうち1台だけが残った場合の確定可否を示し、停止と古い表示の扱いを説明できる。"),
    ("正本から検索・集計を作る", "社員が使う検索や売上表示を、作り直せるデータとして扱います。",
     (("analytics", "バッチとストリーム"), ("event-time-corrections", "遅れて届くイベント"), ("derived-store-boundaries", "正本と導出データ")),
     "正本と集計の作成位置を区別し、再配送、訂正、復元後の照合を手順にできる。"),
    ("別の題材に適用する", "注文基盤を復旧する実習を終えたら、会場の予約を自分で設計します。",
     (("order-system-capstone", "注文基盤の総合課題"), ("privacy-recovery-review", "削除と復元"), ("design-assessment", "到達度チェック")),
     "要求、設計、障害テストの期待結果を一枚にまとめ、要件が変わったときの見直し箇所を指摘できる。"),
)

QUESTIONS = (
    ("100件の予約要求のうち90件だけが成功しました。成功だけのp95は200 msです。受付は良好と言えますか？",
     "成功時の速度は分かります。全100件を母数に、期限内に確定した件数・拒否・不明を分けて初めて受付全体を判定できます。",
     "requirements", "要求と測定へ戻る"),
    ("商品マスターの価格が変わりました。過去の注文履歴にはどちらの金額を表示しますか？ その金額をどこに保存しますか？",
     "購入時の金額を注文の明細に保存します。変更後の商品マスターを参照して過去の請求額を再計算すると、当時の値を失います。",
     "storage", "モデルの選択へ戻る"),
    ("在庫が1個です。AとBは別の注文、Aの再送は同じ注文です。何を取引で守り、何で再送を判別しますか？",
     "在庫を原子的に検査・更新し、予約と要求キーを同じ取引で確定します。AとBの成功は最大1件です。同じキー・同じ内容の再送には記録済みの結果を返し、内容が異なる再利用は拒否します。",
     "transactions", "在庫の取引へ戻る"),
    ("3台のうち、リーダー1台と残り2台が分断されました。確定に過半数が必要なら、孤立側は注文成功を返せますか？",
     "孤立側は過半数に届かず確定できません。過半数側も適格なリーダーを選出してから確定できます。受付できない要求を確定済みと表示しないようにします。",
     "raft-failure-lab", "分断の実習へ戻る"),
    ("検索データは位置120を含むコピーから作り直します。同じ変更121が2回届く場合、何を検証しますか？",
     "コピーに含まれない位置121以降を適用し、イベントのIDや位置で変更の重複を吸収します。配信位置だけを見るのではなく、注文IDと版や値を正本と照合します。",
     "integration-details", "正本と復旧へ戻る"),
    ("連絡先を削除した直後に、前日のバックアップから復元しました。稼働へ戻す前に何を確認しますか？",
     "隔離環境で削除記録を最新位置まで適用し、正本、検索、通知先のどこにも対象が復活していないことを確認してから公開します。",
     "privacy-recovery-review", "削除と復元へ戻る"),
)

LEARNING_VIDEOS = (
    ("first-data-experiment", "初回実習", "同じ注文を二度送るとどうなるか", "timeline",
     ("在庫2個", "確定と応答喪失", "同じキーで再送", "在庫を比較"),
     ("在庫が2個の店で、注文Aを受け付けます。",
      "注文が確定した後で応答が消え、買い手は結果が分かりません。",
      "同じ注文キーで送ると、保存済みの結果を照会できます。",
      "再送後に在庫が1個で、別の注文を受けられるか確かめます。"),
     "待ち時間切れだけで、取引が失敗したと判断できますか？",
     "サーバの確定後に応答だけ失われることがあります。要求キーで確定した結果を照会または再送します。",
     "ブラウザ実習は順番を固定したモデルです。同時アクセスへの備えは、続く取引と在庫の実習で扱います。"),
    ("design-assessment", "到達度チェック", "会場予約をデータから設計する", "matrix",
     ("要件", "予約の正本", "空席の表示", "試験と復旧"),
     ("残り1席では、同時予約でも成功は最大1件と決めます。",
      "予約と残席を一緒に確定し、同じキーの再送を識別します。",
      "空席一覧は遅れを許し、確定時に正本で残席を調べます。",
      "応答喪失、古い表示、削除後の復元をテストします。"),
     "古い一覧で『空席あり』と表示されても、予約を安全に確定できますか？",
     "確定処理は正本で残席を検査します。一覧は更新時刻を示し、満席なら確定せず応答します。",
     "同じ判断を、正本、取引、再送、復旧に分けて説明できるかセルフチェックします。"),
)

CSS = """
.learning-block{border:1px solid var(--line);border-radius:10px;background:var(--paper);padding:clamp(15px,3vw,32px);margin-bottom:20px;scroll-margin-top:12px;min-width:0;overflow-wrap:anywhere}
.learning-actions{display:flex;gap:6px 18px;flex-wrap:wrap}
.learning-actions a{display:inline-flex;align-items:center;min-height:44px}
.learning-steps{padding-inline-start:1.6rem}
.learning-steps>li+li{border-block-start:1px solid var(--line);margin-block-start:1.1rem}
.learning-steps h3{margin-top:.85rem}
.learning-demo{border:1px solid var(--line);border-radius:8px;padding:clamp(12px,2.5vw,20px);margin:1rem 0;background:var(--bg)}
.learning-demo fieldset{min-width:0;margin:0;padding:.65rem .8rem;border:1px solid var(--line)}
.learning-demo legend{font-weight:700}
.learning-demo label{display:flex;align-items:center;min-height:44px;gap:.5rem}
.learning-demo input{accent-color:var(--accent)}
.learning-demo button{font:inherit;font-weight:700;min-height:44px;padding:.35rem .8rem;border:1px solid var(--line);border-radius:6px;background:var(--paper);color:var(--ink);cursor:pointer}
.learning-demo button:disabled{opacity:.6;cursor:default}
.learning-demo button[data-next]{border-color:var(--accent);color:var(--accent)}
.learning-demo .learning-actions{margin-top:.8rem}
.learning-demo output{display:block;margin:.8rem 0;min-height:3.7em}
@media print{.learning-demo,.learning-actions{display:none!important}.learning-block{padding:12px 0;border:0}}
"""

SIMULATION = """
(() => {
    const demo = document.getElementById("retry-demo");
    const next = demo.querySelector("[data-next]");
    const reset = demo.querySelector("[data-reset]");
    const output = demo.querySelector("output");
    let stock, committed, firstResult, step;

    function show(message) {
        output.textContent = message + " 残り" + stock + "個。確定した処理" + committed + "件。";
    }
    function restart(message) {
        stock = 2;
        committed = 0;
        firstResult = undefined;
        step = 0;
        next.disabled = false;
        next.textContent = "注文Aを送る";
        show(message);
    }
    function reserve() {
        if (stock === 0) return false;
        stock--;
        committed++;
        return true;
    }
    next.addEventListener("click", () => {
        if (step === 0) {
            firstResult = reserve();
            show("注文Aは確定。成功の応答だけが消えました。");
            next.textContent = "同じ注文Aを再送する";
        } else if (step === 1) {
            if (demo.querySelector('input[name="retry-policy"]:checked').value === "reuse" && firstResult) {
                show("同じキーの確定記録を返しました。もう一度の減算はありません。");
            } else {
                reserve();
                show("再送を別の処理として確定し、注文Aに対して二度減算しました。");
            }
            next.textContent = "別の注文Bを送る";
        } else {
            show(reserve() ? "注文Bが確定しました。" : "在庫切れのため、注文Bを受け付けられません。");
            reset.focus();
            next.disabled = true;
            next.textContent = "この試行は完了";
        }
        step++;
    });
    demo.addEventListener("change", () => restart("方式を切り替えました。初期状態です。"));
    reset.addEventListener("click", () => restart("初期状態へ戻しました。"));
    restart("初期状態です。");
    demo.hidden = false;
})();
"""


def reading_link(anchor, label):
    return f'<a href="#{escape(anchor)}">{escape(label)}</a>'


def run_video(slide):
    return f'<p class="chapter-video"><a href="../slides/index.html#slide-{slide}">図と音声で見る</a></p>'


def learning_start(slide):
    steps = "\n".join(
        f'<li><h3>{escape(title)}</h3><p>{escape(goal)}</p>'
        f'<p class="learning-actions">{" ".join(reading_link(*target) for target in targets)}</p>'
        f'<p><strong>次へ進む目安</strong>　{escape(check)}</p></li>'
        for title, goal, targets, check in STEPS
    )
    return f'''
<section id="learning-path" class="learning-block" aria-labelledby="path-title">
<h2 id="path-title">データ指向アプリケーション設計の学び方</h2>
<p>データ指向アプリケーション設計では、アプリが扱うデータをどこに保存し、どう読み書きし、負荷や障害があっても何を守るかを決めます。身近な例は「注文を確定し、在庫を減らし、あとから集計する」処理です。</p>
<p class="contract"><strong>到達目標</strong>　要件から保存・取引・複製・集計の方法を選び、設計の理由を説明し、失敗時にも守る条件をテストできる。</p>
<p>まずブラウザ実習で結果を予想します。続く例で使う「正本」は最終的な判断の根拠にする記録、「導出データ」は正本から作る検索や集計、「取引」は更新をまとめて確定する単位です。SQLに慣れていない場合は<a href="#sql-reading-start">3行の予約から座席数を数える例</a>を先に読めます。</p>
<p class="learning-actions"><a href="#first-data-experiment">最初の実習へ</a><a href="#path-steps">6段階の順番を見る</a><a href="#design-reference">設計の手引き・用語集</a><a href="#design-assessment">到達度を確かめる</a></p>
<h3 id="first-data-experiment">最初の実習　同じ注文を二度送ると何が起きるか</h3>
{run_video(slide)}
<p>在庫は2個です。注文Aが確定した直後に返事だけが消え、買い手は同じ注文を再送します。次に別の買い手が注文Bを送ります。在庫と確定件数が各段階でどう変わるか予想し、二つの方式を試してください。</p>
<div class="learning-demo" id="retry-demo" role="group" aria-label="注文の再試行を比較する" hidden>
<fieldset>
<legend>再送の扱い</legend>
<label><input type="radio" name="retry-policy" value="repeat" checked> 届いた要求のたびに在庫を減らす</label>
<label><input type="radio" name="retry-policy" value="reuse"> 同じ注文キーなら確定済みの結果を返す</label>
</fieldset>
<output aria-live="polite" aria-atomic="true"></output>
<div class="learning-actions"><button type="button" data-next>注文Aを送る</button><button type="button" data-reset>やり直す</button></div>
</div>
<details>
<summary>予想と比べる</summary>
<p>毎回減らす方式では在庫は2→1→0→0となり、二度とも注文Aで減るためBは失敗します。キーを使う方式では2→1→1→0で、AとBが各1件確定します。</p>
<p>「返事がない」はクライアントが観測した結果です。取引が確定したかは正本で判定します。実装では、注文キーと要求内容を紐づけた一意な確定記録を、在庫の条件付き更新と同じ取引に置きます。この練習は順次到着の例です。同時注文は第3段階で確認します。</p>
</details>
<h3 id="path-steps">6段階の学習順</h3>
<p>各段階で「結果を予想する → 本文か動画で理由を学ぶ → 実習・問題で答え合わせする」を繰り返します。Pythonを使う実習には、本文に実行方法と出力例があります。</p>
<ol class="learning-steps">{steps}</ol>
</section>
<script>{SIMULATION}</script>
'''


def assessment(slide):
    questions = "\n".join(
        f'<details><summary>{escape(question)}</summary><p>{escape(answer)}</p>'
        f'<p>{reading_link(anchor, label)}</p></details>'
        for question, answer, anchor, label in QUESTIONS
    )
    return f'''
<section id="design-assessment" class="learning-block" aria-labelledby="assessment-title">
<h2 id="assessment-title">到達度チェック　別の題材でも設計できるか</h2>
{run_video(slide)}
<p>先に自分の答えを書き、解答を開いて照合します。用語が出てくることより、条件と結果の理由を説明できることが次へ進む目安です。説明が曖昧だった項目は、解答のリンクから学び直せます。</p>
{questions}
<h3 id="venue-design-task">自力演習　会場予約システム</h3>
<p>人気の講座に残り1席があります。同時に予約が届く場合でも確定は最大1件で、通信が切れた利用者は同じ予約を再送します。空席一覧は30秒まで古くてよいものとし、予約時のメールアドレスは連絡業務に使い、取り消し後に定めた期限で削除します。</p>
<p>予約を確定する正本、空席一覧、連絡データの関係を図にし、次を記録してください。</p>
<ol>
<li>満席・確定・結果不明それぞれの応答と、同時予約で守る条件。</li>
<li>予約を保存する取引の境界、同じ操作を再送するときのキー、一覧を作り直す入口。</li>
<li>同時予約、確定直後の応答喪失、古い一覧からの予約、削除済みデータを含む復元について、試験の入力と期待結果。</li>
<li>受付を一つのDBで行う案と別々の地域に分ける案で、必要な費用と失敗時の違い。</li>
</ol>
<details>
<summary>設計例と確認する観点</summary>
<ul>
<li><strong>確定と再送</strong>　予約の正本は講座ごとの残席と予約IDを持ちます。残席が正なら減らす操作、予約と要求キーの記録を同じ取引で確定します。競合の試験では別キー2件の成功が1件、再送試験では確定済みIDが同じで残席も変わらないことを確認します。要求内容が同じかも照合します。</li>
<li><strong>鮮度と復旧</strong>　一覧は正本の変更から生成し、閲覧時点の鮮度を示します。30秒を超えた一覧には遅れを表示するか、許容範囲内の読み先へ切り替えます。見た目が空席でも予約時点の正本で判定します。作り直した一覧を、講座ID・残席・適用位置で照合します。</li>
<li><strong>削除</strong>　連絡先は職務を限定した記録へ分離し、公開一覧には含めません。古いバックアップは隔離して復元し、削除を適用してから公開します。試験では削除した連絡先が通知経路と検索にも現れないことを確認します。</li>
<li><strong>方式の選択</strong>　単一DBに収まり、停止目標を満たすなら、その取引で始められます。確定済み予約の喪失が許されない障害範囲へ広げるときは、別障害領域での永続化と確定条件を決めます。同じ講座を二地域から受け付けるなら、講座の担当を決めるか、残席を調停する機構が必要です。</li>
</ul>
</details>
<p><strong>仕上げ</strong>　自分の設計について上の四つの観点を示し、少なくとも同時予約と応答喪失の試験に具体的な入力・期待結果・観測先を書けたか確認します。実装は<a href="#order-system-capstone">注文基盤の総合課題</a>と照合できます。</p>
<p class="learning-actions"><a href="#learning-path">学習順へ戻る</a><a href="#design-workshops">関連する実習を試す</a></p>
</section>
'''
