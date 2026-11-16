"""Original worked cases: executable boundary tests and reasoned exercises for GoF."""
from textwrap import dedent

LABS={}
def add(key,title,requirement,contract,reading,alternatives,trace,main,output,questions,support=''):
    assert len(reading)==2 and len(alternatives)==2 and len(trace)==3 and len(questions)==3
    LABS[key]=dict(title=title,requirement=requirement,contract=contract,reading=reading,
        alternatives=alternatives,trace=trace,main=dedent(main).strip(),output=dedent(output).strip(),
        questions=questions,support=dedent(support).strip())

add('abstract-factory','製品群の整合は、型だけで保証できるか',
 '暗色・明色に加えて、高コントラストの製品群を追加する。画面の処理を変更せず、ボタンとチェックの見た目をそろえたい。',
 '同じThemeから得た製品は同じテーマに属する。ただしButtonとCheckの型だけでは、テーマの混在を禁止できない。',
 ['Contrastを追加して既存のscreenへ渡すと、新しい製品群を利用できる。変わるのは具体工場と組立側であり、画面の呼出手順ではない。ここで守っているのは「工場ごとに製品群が整合する」という意味の契約である。',
  '反例のBrokenもThemeを実装できるが、暗色ボタンと明色チェックを返してしまう。インターフェースを導入しただけで整合性を証明したことにはならない。各工場の組合せテスト、必要なら製品へのテーマ識別子の導入を検討する。'],
 [('画面内のswitch','テーマが二つで固定なら分岐も候補。ただし製品の生成箇所が散らばると混在を検査しにくい。'),('Factory Method','継承で生成操作を差し替える問題を扱う。関連製品を一組で選ぶ要求そのものとは異なる。')],
 [('Contrastを渡す','contrast button / contrast check','画面の共通処理を再利用できる。'),('Brokenを渡す','dark button / light check','型は合っていても意味の契約に違反する。'),('混在を検出','mixed=true','この例の文字列判定はテスト用。実製品なら識別子などを契約化する。')],
 '''
 class Contrast implements Theme {
     public Button button() { return () -> "contrast button"; }
     public Check check() { return () -> "contrast check"; }
 }
 class Broken implements Theme {
     public Button button() { return () -> "dark button"; }
     public Check check() { return () -> "light check"; }
 }
 screen(new Contrast());
 Theme broken = new Broken();
 screen(broken);
 boolean mixed = broken.button().draw().startsWith("dark")
     && broken.check().draw().startsWith("light");
 System.out.println("mixed=" + mixed);
 ''','''
 contrast button / contrast check
 dark button / light check
 mixed=true
 ''',
 [('Tooltipという製品を増やすと、どこが変わるか。','Themeの生成操作と、各具体工場を変更する。製品群の追加には強いが、製品の種類の追加には全工場への影響がある。'),('混在をコンパイル時に禁止したい場合、何が追加で必要か。','テーマ別の型や型パラメーターなどで製品の関連を表す設計が候補。ただし利用側の型が複雑になるため、テストと実行時検査との費用も比較する。'),('新テーマの受入テストを一つ定義する。','同じ工場が作った全製品のテーマ識別子が一致することを確認する。単に生成できることだけをテストしても混在を検出できない。')])

add('builder','ビルダーを二度使うと、結果はどうなるか',
 '同じディレクターで月次レポートを繰り返し作る。前月のデータが次の結果へ混ざらないことが必要になった。',
 '一つの生成で蓄積した状態の寿命を決める。このTextBuilderは一回の生成用で、resultは内容を消去しない。',
 ['最初のresultを文字列として保存し、同じビルダーにもう一度constructすると、二つのレポートが連結される。Directorの手順が正しくても、Builderの再利用契約が未定義なら成果物は正しくならない。',
  '最も単純な修正は生成ごとに新しいBuilderを用意すること。再利用が必要なら明示的なreset、build後の状態遷移、例外で途中終了した場合の扱いまで決める。メソッドチェーンの見た目より、完成条件と所有する状態を確認する。'],
 [('毎回newする','状態の取りこぼしを防ぎやすい。生成コストが問題かは計測してから判断する。'),('再利用とreset','割当てを減らせる場合があるが、リセット漏れと途中失敗後の状態を管理する責任が増える。')],
 [('同じBuilderで二回construct','reused-concatenates=true','内部バッファに前回の結果が残る。'),('新しいBuilderでconstruct','fresh-independent=true','生成ごとに状態を分離する。'),('resultを先に保存','first-unchanged=true','このresultは不変なStringを返し、以前の値は後から変わらない。')],
 '''
 ReportDirector director = new ReportDirector();
 TextBuilder reused = new TextBuilder();
 director.construct(reused);
 String first = reused.result();
 director.construct(reused);
 System.out.println("reused-concatenates=" + reused.result().equals(first + first));
 TextBuilder fresh = new TextBuilder();
 director.construct(fresh);
 System.out.println("fresh-independent=" + fresh.result().equals(first));
 System.out.println("first-unchanged=" + first.equals("TITLE: Sales\\nTOTAL: 120\\nEND"));
 ''','''
 reused-concatenates=true
 fresh-independent=true
 first-unchanged=true
 ''',
 [('resultでバッファを消す設計にすれば常に安全か。','常に安全ではない。結果取得の副作用、複数回の取得、生成途中の取得をどう扱うかが新しい契約になる。'),('titleより前にtotalを呼べないようにする案は。','状態検査で拒否するか、段階ごとに異なる型を返す方法がある。型の増加が利用者の誤用防止に見合うか比較する。'),('HTML出力を実用化する際の追加テストは。','動的なタイトルに山括弧や引用符を含め、表示用に適切にエスケープされることを確認する。組立パターン自体は出力の安全性を保証しない。')])

add('factory-method','staticへの置換で、なぜ差替えが失われるか',
 '生成関数はstaticの方が簡単だという提案が出た。JSON用のクラスを選べば、既存の共通手順がJSONを使うか検証する。',
 '共通手順内の生成呼出が、実際のインスタンスに対応するオーバーライドへ解決される必要がある。staticの隠蔽では同じ契約にならない。',
 ['JsonImporter.runは親の手順を再利用しながら、仮想メソッドcreateParserによってJSONの製品を得る。対してStaticJson.runの本体は親で定義されたstaticの共通手順であり、その中の生成呼出は親の実装へ結び付く。',
  'メソッド名が同じでも、差替えの仕組みが違う。この例で比較すべき観測点は、生成関数を直接呼んだ結果ではなく、利用したい共通手順を通した結果である。継承が不要ならParserの注入も正当な代案になる。'],
 [('Parserを引数で注入','生成と利用を分けるだけなら単純。共通の継承フレームワークを必要としない。'),('static生成関数','生成の入口としては有用。ただし動的なオーバーライドによる生成フックではない。')],
 [('JsonImporter.run','open -> JSON parsed -> close','共通手順からサブクラスのフックへ進む。'),('StaticJson.run','static -> CSV parsed','親に書かれた共通手順の呼出先は変わらない。'),('StaticJson.createParserを直接呼ぶ','static direct -> JSON parsed','直接呼出の成功だけでは共通手順の差替えを検証できない。')],
 '''
 new JsonImporter().run();
 StaticJson.run();
 System.out.println("static direct -> " + StaticJson.createParser().parse());
 ''','''
 open -> JSON parsed -> close
 static -> CSV parsed
 static direct -> JSON parsed
 ''',
 [('StaticJsonにrunを複製すれば解決か。','結果は変えられるが、共通手順を複製しないという要求を失う。動くことと、守るべき変更境界を満たすことを分ける。'),('Factory Methodのテストは何を経由すべきか。','実際に生成フックを呼ぶ共通手順を経由する。フックの単体試験に加え、手順から期待する製品が使われることを検証する。'),('生成に引数が必要になったら、必ず継承するか。','必須ではない。生成方針のオブジェクトやSupplierなどの注入も比較する。継承と合成のどちらが寿命や設定を明確にするかで選ぶ。')],
 '''
 static class StaticBase {
     static Parser createParser() { return new CsvParser(); }
     static void run() { System.out.println("static -> " + createParser().parse()); }
 }
 static class StaticJson extends StaticBase {
     static Parser createParser() { return new JsonParser(); }
 }
 ''')

add('prototype','リストをコピーしても、要素は共有され得る',
 '文字列だったタグを、名前を編集できるTagオブジェクトへ変更する。複製したひな型の編集が元へ漏れないことが必要になった。',
 '独立させる必要のある可変状態を、どこまで複製するか定義する。コンテナーの複製と、要素の複製は別の操作である。',
 ['元の例ではStringが不変なので、新しいリストへ参照をコピーしてもタグの文字列自体は書き換えられない。一方、可変なTagへ置き換えると、ArrayListのコピーは同じ要素を指し続ける。',
  '深いコピーを機械的に選ぶ前に、所有関係を決める。共有すべき外部サービスや識別子まで複製すると意味が変わる。要素を不変にする、変更した部分だけ新しい値にする、複製対象を明示する、という代案もある。'],
 [('要素を不変値にする','共有しても変更の漏れが起きにくい。編集は新しい値への置換として扱う。'),('可変要素を複製する','独立した編集ができるが、循環参照・同一性・外部資源の扱いを決める必要がある。')],
 [('元のTemplate.copy','list-independent=true','文字列の要素を共有しても、追加先のリストは独立する。'),('可変要素を含むリストだけコピー','shared-element=urgent','元とコピーが同じTagを指す。'),('要素もnewする','deep-independent=true','この小さな例では要素の名前も独立する。')],
 '''
 Template base = new Template(java.util.List.of("base"));
 Template copy = base.copy(); copy.add("urgent");
 System.out.println("list-independent=" + base.describe().equals("[base]"));
 class Tag { String name; Tag(String name) { this.name = name; } }
 java.util.List<Tag> original = new java.util.ArrayList<>();
 original.add(new Tag("base"));
 java.util.List<Tag> shallow = new java.util.ArrayList<>(original);
 shallow.get(0).name = "urgent";
 System.out.println("shared-element=" + original.get(0).name);
 java.util.List<Tag> deep = new java.util.ArrayList<>();
 for (Tag tag : original) deep.add(new Tag(tag.name));
 deep.get(0).name = "edited";
 System.out.println("deep-independent=" + original.get(0).name.equals("urgent"));
 ''','''
 list-independent=true
 shared-element=urgent
 deep-independent=true
 ''',
 [('copyの仕様書へ何を書くか。','独立する可変状態、共有する不変値や外部資源、識別子の扱いを記す。「コピーを返す」だけでは編集時の期待を定められない。'),('タグが親への参照を持つと、再帰コピーだけで十分か。','循環で停止しない可能性がある。コピー済み対応表や所有境界を検討し、循環と共有参照を含むテストを追加する。'),('不変の大きなひな型にPrototypeは必須か。','必須ではない。不変の値を共有し、変更した部分だけ新しい値へ置換する方が単純なこともある。')])

add('singleton','一個であることと、二回の更新が残ることは別',
 '共有設定へ利用回数のカウンターを追加する。二つのスレッドが一回ずつ増やしたら、結果が二になることを期待する。',
 '列挙型の安全な初期化は、可変フィールドのread-modify-writeを不可分にはしない。volatileも複合操作の原子性は保証しない。',
 ['実習はラッチで「両方がゼロを読んだ後に書く」順序を作る。二つのスレッドはどちらも一を書き戻すため、結果は一になる。偶然のタイミングに頼る負荷試験ではなく、失われた更新を再現する小さな反例である。',
  'AtomicIntegerや同期で更新を直しても、グローバルな状態が次の試験へ残る問題は別に残る。何を一個にする必要があるのか、寿命を誰が所有するかを考え、テストごとに生成できる依存の注入と比較する。'],
 [('AtomicInteger / 同期','更新の原子性を守る。テスト間の状態共有や寿命の問題まで解決するわけではない。'),('依存を注入する','利用範囲ごとに生成と破棄を管理できる。一意性が本当に必要な範囲は別途決める。')],
 [('二つのスレッドが一回ずつ更新','after-two-writes=1','両者が同じ古い値を読んでから書く。'),('次の利用者が参照','next-test-sees=1','同じ共有状態が引き継がれる。'),('finallyで状態を戻す','後続実行への持越しを抑える','テスト用の後始末であり、設計上の依存を消すものではない。')],
 '''
 enum Counter { INSTANCE; volatile int value; }
 java.util.concurrent.CountDownLatch readBoth = new java.util.concurrent.CountDownLatch(2);
 Runnable increment = () -> {
     int old = Counter.INSTANCE.value;
     readBoth.countDown();
     try { readBoth.await(); }
     catch (InterruptedException e) { Thread.currentThread().interrupt(); return; }
     Counter.INSTANCE.value = old + 1;
 };
 try {
     Thread a = new Thread(increment), b = new Thread(increment);
     a.start(); b.start(); a.join(); b.join();
     System.out.println("after-two-writes=" + Counter.INSTANCE.value);
     System.out.println("next-test-sees=" + Counter.INSTANCE.value);
 } finally { Counter.INSTANCE.value = 0; }
 ''','''
 after-two-writes=1
 next-test-sees=1
 ''',
 [('volatileを付けたのに、なぜ更新が失われるか。','読み出しと書き込みの可視性と、読み出し・計算・書き込み全体の原子性は異なる。二者が同じ古い値から計算できるため。'),('AtomicIntegerに替えたらテストの独立性も得られるか。','得られない。更新は安全でも同じ状態を共有するため、試験の順序依存や寿命管理は別に扱う。'),('「全システムで一個」という要件にこのenumだけで足りるか。','足りない。通常はクラスローダーごとの範囲であり、複数プロセスや複数端末の一意性は外部の調整を要する。')])

add('adapter','名前の変換だけでは、エラー契約はそろわない',
 '送信側は空白のメッセージを拒否し、旧SMS部品が失敗した場合は呼出側へ失敗を伝えることになった。',
 'sendからpostへ呼べることに加え、入力の意味と失敗の伝え方が利用側の契約を満たす必要がある。',
 ['検査付きの境界が空白を先に拒否する。送信できない入力を渡してから旧APIの偶然の動作へ任せるより、どの層が責任を持つかが明確になる。ここではIllegalArgumentExceptionで拒否する方針を選ぶ。',
  '旧部品のofflineはそのまま伝播する。実製品なら自アプリの例外型への変換や、再試行可能性の表現を検討する。戻り値が受付だけを示すAPIを、配送完了の契約へ名前だけで変換することはできない。'],
 [('境界で入力と例外を変換','外部APIの変更を局所化できる。どの例外を保存し、原因をどう残すかを決める。'),('利用側で個別に対処','一箇所だけなら単純。ただし利用箇所が増えると変換規則の不一致が起きやすい。')],
 [('readyを送信','SMS: ready','正常系は旧部品へ渡る。'),('空白を送信','blank=rejected','境界で拒否し、postしない。'),('旧部品が例外','failure=offline','この実習では失敗を握りつぶさない。')],
 '''
 Sender target = new SmsAdapter(new LegacySms());
 Sender checked = text -> {
     if (text == null || text.isBlank()) throw new IllegalArgumentException("blank");
     target.send(text);
 };
 checked.send("ready");
 try { checked.send(" "); }
 catch (IllegalArgumentException e) { System.out.println("blank=rejected"); }
 LegacySms offline = new LegacySms() {
     void post(String text) { throw new IllegalStateException("offline"); }
 };
 try { new SmsAdapter(offline).send("ready"); }
 catch (IllegalStateException e) { System.out.println("failure=" + e.getMessage()); }
 ''','''
 SMS: ready
 blank=rejected
 failure=offline
 ''',
 [('旧APIの単位が秒、新契約がミリ秒なら何を検証するか。','変換式だけでなく丸め、負値、上限、オーバーフローを検証する。境界の値をテストし、精度の違いを契約へ記す。'),('非同期のpostを同期のsendへ単純に包んでよいか。','待機、タイムアウト、取消、実行スレッドへの影響を定義する必要がある。メソッド名を合わせるだけでは同じ意味にならない。'),('すべての例外をcatchして成功を返す案は。','呼出側が失敗を観測できず契約違反になり得る。扱える例外だけ変換し、原因と再試行方針を残す。')])

add('bridge','種類と経路を別々に増やす効果を測る',
 '緊急・通常の通知を、画面へ出す代わりにメモリへ記録して試験したい。通知側のクラスを増やさず対応する。',
 '通知は文面の意味を担当し、Channelは配送・記録の手段を担当する。どの組合せもChannelの同じ失敗契約へ従う。',
 ['テスト用のBufferという経路を一つ足すと、既存のUrgentとNormalの両方で使える。緊急メール、緊急SMS、通常メールという組合せごとのクラスを足す場合と比べ、どちらの軸を変更したかが明確になる。',
  '経路の例外は通知側を通って呼出側へ返る。二つの軸を分離しても、失敗の意味まで独立にできるとは限らない。単なる装飾や既存APIの互換性調整なら、別の設計の方が意図を伝えやすい場合がある。'],
 [('組合せごとのサブクラス','少数で固定なら読みやすい。二つの軸が増えると組合せの重複が増える。'),('単一の関数と引数','種類の違いが接頭辞だけなら十分なこともある。独立した責務の大きさに合わせる。')],
 [('UrgentとBuffer','URGENT: fireを記録','通知の責務は維持される。'),('Normalと同じBuffer','readyを記録','経路の追加が両方の種類に効く。'),('失敗するChannel','failure=offline','委譲しても失敗を自動で回復するわけではない。')],
 '''
 class Buffer implements Channel {
     final StringBuilder log = new StringBuilder();
     public void send(String text) { log.append(text).append("|"); }
 }
 Buffer buffer = new Buffer();
 new Urgent(buffer).publish("fire");
 new Normal(buffer).publish("ready");
 System.out.println(buffer.log);
 Channel offline = text -> { throw new IllegalStateException("offline"); };
 try { new Urgent(offline).publish("fire"); }
 catch (IllegalStateException e) { System.out.println("failure=" + e.getMessage()); }
 ''','''
 URGENT: fire|ready|
 failure=offline
 ''',
 [('経路を一種類しか使わないならBridgeは必要か。','必須ではない。独立して増える二つの軸が実際にあるかを確かめ、単純な委譲や関数で足りるか比較する。'),('記録用Channelを追加するテストの利点は。','外部送信をせず、通知側が作った文面と呼出順を観測できる。実配送の到達性を検証したことにはならない。'),('既存SMS部品のAPIが異なる場合、BridgeとAdapterは排他か。','排他ではない。通知と経路の分離をBridgeで行い、経路の内部で外部部品をAdapterで包む設計も可能。')])

add('composite','木からグラフへ変わる瞬間を見逃さない',
 '同じ項目を複数のフォルダーから参照できるようにする。循環した参照で集計が停止しなくなる事故も防ぎたい。',
 '集計を出現回数で数えるか、項目の同一性で一度だけ数えるかを決める。循環と共有は異なる問題である。',
 ['同じ葉を二回追加した場合、この実習の集計は出現回数で数えるため八になる。全体で一度だけ訪問する集合を使うと四になり、意図せず集計の意味が変わる。',
  '循環の検出には、今回の再帰経路上にある要素の集合を使う。処理後に経路から外すので、別の枝で同じ葉を再利用しても循環とは扱わない。補助関数は教材の二種類のEntryに限定しており、実製品では構築時の検査や契約の配置も検討する。'],
 [('木として構築を制限','集計を単純に保ちやすい。親の所有権と移動操作を定義する。'),('共有を許すグラフ','用途が広がるが、訪問回数・循環・同一性の仕様と検査が必要になる。')],
 [('4と6の木','tree=10','元の再帰集計と同じ意味。'),('同じ4の葉を二回参照','shared=8','この例は出現回数を数える。'),('Aの子がB、Bの子がA','cycle=rejected','現在の再帰経路への再入を検出する。')],
 '''
 Folder root = new Folder(); root.add(new FileEntry(4)); root.add(new FileEntry(6));
 System.out.println("tree=" + checkedSize(root, path()));
 FileEntry leaf = new FileEntry(4);
 Folder shared = new Folder(); shared.add(leaf); shared.add(leaf);
 System.out.println("shared=" + checkedSize(shared, path()));
 Folder a = new Folder(), b = new Folder(); a.add(b); b.add(a);
 try { checkedSize(a, path()); }
 catch (IllegalArgumentException e) { System.out.println("cycle=rejected"); }
 ''','''
 tree=10
 shared=8
 cycle=rejected
 ''',
 [('全体の訪問済み集合だけで循環を調べると、共有の集計はどう変わるか。','同じ要素の二回目を除外してしまい、出現回数の集計でなくなる。現在の経路と全訪問済みを使い分ける。'),('単純なentry == thisの検査で十分か。','直接の自己参照だけしか拒否できない。AからB、BからAという間接循環も試験する必要がある。'),('非常に深い木を扱う追加設計は。','再帰によるスタック消費を避ける明示的なスタックや深さ制限を検討する。サイズ加算のオーバーフローも確認する。')],
 '''
 static java.util.Set<Entry> path() {
     return java.util.Collections.newSetFromMap(new java.util.IdentityHashMap<>());
 }
 static int checkedSize(Entry entry, java.util.Set<Entry> active) {
     if (entry instanceof FileEntry file) return file.size();
     if (!(entry instanceof Folder folder)) throw new IllegalArgumentException("unknown entry");
     if (!active.add(entry)) throw new IllegalArgumentException("cycle");
     try {
         int total = 0;
         for (Entry child : folder.children) total = Math.addExact(total, checkedSize(child, active));
         return total;
     } finally { active.remove(entry); }
 }
 ''')

add('decorator','ラッパーの順序と、ログが意味する成功を分ける',
 '監査では「利用者が渡した文面」と「実際に送る文面」のどちらを残すか指定された。送信失敗時のログの読み方も決めたい。',
 '委譲の前後に何を記録するか、変換の外側と内側のどちらかを明示する。ログの存在だけを配送成功の証拠にしない。',
 ['LoggingをUpperの外へ置くと、ログはreadyでメールはREADYになる。逆順ならログもREADYになる。両者ともSenderを満たすが、監査仕様に対して同じ意味ではない。組立順もコードレビューと試験の対象である。',
  'このLoggingは送信前に記録する。内側が例外を投げてもLOGは残るため、記録があることは送信を試みた証拠にとどまる。試行・受付・完了・失敗を区別するイベントや識別子を設ける判断につながる。'],
 [('Decoratorで順序を組み立てる','責務を交換・併用しやすい。順序と例外の通り方を仕様として固定する。'),('一つの送信関数に固定する','監査順が固定なら明示的で追いやすい。任意の組合せが本当に必要かを先に確認する。')],
 [('Logging(Upper(Mail))','LOG ready / MAIL READY','変換前を記録する。'),('Upper(Logging(Mail))','LOG READY / MAIL READY','変換後を記録する。'),('Loggingの内側が失敗','LOG readyの後にfailure','事前ログは配送の成功を保証しない。')],
 '''
 System.out.println("A"); new Logging(new Upper(new Mail())).send("ready");
 System.out.println("B"); new Upper(new Logging(new Mail())).send("ready");
 Sender offline = text -> { throw new IllegalStateException("offline"); };
 try { new Logging(offline).send("ready"); }
 catch (IllegalStateException e) { System.out.println("failure=" + e.getMessage()); }
 ''','''
 A
 LOG: ready
 MAIL: READY
 B
 LOG: READY
 MAIL: READY
 LOG: ready
 failure=offline
 ''',
 [('暗号化と圧縮の順序を自由に替えてよいか。','一般に結果や効率が変わる。要求する形式、復号と展開の逆順、失敗時の扱いを定義してから組み立てる。'),('送信成功のログを委譲の後へ移すだけで配送完了を保証できるか。','できない場合がある。内側の戻りが受付だけを意味するなら、配送完了の確認は別の通知や照会を要する。'),('順序の受入テストには何を含めるか。','変換前後の入力、最終的に実体へ渡る値、内側の例外、各ラッパーの実行順を含める。')])

add('facade','入口を一つにしても、処理全体は原子的にならない',
 '注文確定で支払い後の発送が失敗した。呼出側は失敗を受け取ったので、支払いも行われていないと思っている。',
 '処理全体の成功・部分成功・失敗を区別する。Facadeは入口をまとめるが、複数の副作用を自動で巻き戻さない。',
 ['例では在庫確認と支払いが進んだ後、発送の例外が伝わる。呼出が失敗しても、記録したchargedはtrueのままである。入口が一つであることと、一括して成功・失敗することは異なる。',
  '実用では処理段階の記録、冪等な再試行、返金などの補償、運用上の再開方法を検討する。同じデータベース内ならトランザクションが候補でも、外部決済や配送まで同じ保証に含められるとは限らない。'],
 [('単一DBのトランザクション','同じ資源の更新には有効。外部サービスを含む全処理への保証と混同しない。'),('段階の永続化と補償','部分失敗を扱えるが、補償の失敗や二重実行を含めた運用設計が増える。')],
 [('Stock.check','stock checked','最初の処理は完了している。'),('Payment.pay','paid','支払いの副作用が残る。'),('Shipping.shipが失敗','charged=true','例外だけでは以前の副作用を消せない。')],
 '''
 class RecordedPayment extends Payment {
     boolean charged;
     void pay() { charged = true; super.pay(); }
 }
 RecordedPayment payment = new RecordedPayment();
 Shipping offline = new Shipping() {
     void ship() { throw new IllegalStateException("shipping offline"); }
 };
 try { new Checkout(new Stock(), payment, offline).checkout(); }
 catch (IllegalStateException e) { System.out.println(e.getMessage()); }
 System.out.println("charged=" + payment.charged);
 ''','''
 stock checked
 paid
 shipping offline
 charged=true
 ''',
 [('失敗時にcheckout全体を再度呼べばよいか。','支払いの二重実行が起き得る。段階の記録と各操作の冪等性、照会手段を先に定義する。'),('補償とは元へ完全に戻す操作か。','常にそうではない。返金などの業務上の埋合せであり、履歴や手数料などが残る場合もある。'),('Facadeの責務が大きくなりすぎた兆候は。','全画面の判断や全業務の状態管理が集中し、変更理由が増えること。利用目的別の入口と業務部品へ責任を分ける。')])

add('flyweight','共有キーに、何を含めるべきか',
 '同じフォントでも文字サイズが異なる設定を扱う。フォント名だけで共有すると、異なる表示設定を同一と見なしてしまう。',
 '共有キーは共有対象の意味的な同一性を表す。共有する状態は不変にし、配置位置などの個別状態を混ぜない。',
 ['古いプールはフォント名だけをキーにする。文字サイズも内部状態へ増やすなら、キーと共有オブジェクトの両方へサイズを加える必要がある。キャッシュを使うこと自体より、等しいと見なす条件が重要である。',
  '同じフォントと同じサイズなら再利用し、サイズが違えば分ける。キーが増えるほど共有率は下がり、プールの保持量は増える。性能は実測し、並行利用や上限、破棄の方針もパターンとは別に定める。'],
 [('不変値を共有する','値の同一性が明確なら安全に再利用しやすい。利用件数と共有率を測る。'),('共有せず生成する','量が小さければ管理が単純。プールの探索・保持・同期の費用を払わずに済む。')],
 [('旧プールの同じフォント','old-same=true','サイズを区別する契約はまだない。'),('新キーで12ptと18pt','different-size-distinct=true','異なる内部状態を同じオブジェクトへ混ぜない。'),('同じ12ptを再要求','same-style-reused=true','等しいキーは共有できる。')],
 '''
 StylePool old = new StylePool();
 System.out.println("old-same=" + (old.get("Serif") == old.get("Serif")));
 record Key(String font, int points) {}
 record SizedStyle(String font, int points) {}
 java.util.Map<Key, SizedStyle> pool = new java.util.HashMap<>();
 Key small = new Key("Serif", 12), large = new Key("Serif", 18);
 SizedStyle a = pool.computeIfAbsent(small, k -> new SizedStyle(k.font(), k.points()));
 SizedStyle b = pool.computeIfAbsent(large, k -> new SizedStyle(k.font(), k.points()));
 SizedStyle again = pool.computeIfAbsent(new Key("Serif", 12),
     k -> new SizedStyle(k.font(), k.points()));
 System.out.println("different-size-distinct=" + (a != b));
 System.out.println("same-style-reused=" + (a == again));
 ''','''
 old-same=true
 different-size-distinct=true
 same-style-reused=true
 ''',
 [('色も共有状態へ増やすなら何を直すか。','色を含むキーと共有オブジェクトを定義し、同じ色の再利用と異なる色の分離の両方を試験する。'),('文字ごとのx座標をキーへ含めるべきか。','通常は外部状態として描画時に渡す。キーへ含めると同じスタイルでも共有しにくくなり、責任の境界も曖昧になる。'),('HashMapをConcurrentHashMapへ替えれば完成か。','マップ操作の並行性は改善するが、値の可変性、生成の副作用、キャッシュの上限と寿命は別に設計する。')])

add('proxy','初期化の失敗を、いつ再試行するか',
 '文書の初回読み込みが一時的に失敗する。失敗を永続的にキャッシュするか、次の要求で再試行するかを決めたい。',
 'この実習では成功した実体だけを保持し、失敗は呼出側へ伝える。次のreadは再試行するが、呼出内部で無限に再試行しない。',
 ['ローダーは最初の一回だけ失敗し、二回目に実体を返す。代理は失敗した時点ではrealへ値を代入していないため、次の呼出で生成を試せる。三回目のreadは成功した実体を再利用する。',
  'これは初期化失敗の方針であり、生成後のreadの失敗で実体を破棄するかは別である。失敗の保持期間、タイムアウト、同時初期化、資源の破棄を要件として決める。同期領域で重い読込を行う場合の待ち時間にも注意する。'],
 [('失敗後の次回要求で再試行','単純で一時障害から回復できる。連続要求時の負荷を必要に応じて制限する。'),('失敗を期限付きで保持','障害中の負荷を抑えられるが、復旧後も期限まで失敗を返す可能性がある。')],
 [('初回read','first=offline','失敗した実体を成功扱いで保持しない。'),('二回目read','load manual / manual','次の呼出で初期化に成功する。'),('三回目read','manual / attempts=2','成功後は同じ実体を利用する。')],
 '''
 java.util.concurrent.atomic.AtomicInteger attempts = new java.util.concurrent.atomic.AtomicInteger();
 RetryingDocument doc = new RetryingDocument(() -> {
     if (attempts.incrementAndGet() == 1) throw new IllegalStateException("offline");
     return new RealDocument();
 });
 try { doc.read(); }
 catch (IllegalStateException e) { System.out.println("first=" + e.getMessage()); }
 System.out.println(doc.read());
 System.out.println(doc.read());
 System.out.println("attempts=" + attempts.get());
 ''','''
 first=offline
 load manual
 manual
 manual
 attempts=2
 ''',
 [('初期化の途中で例外になった実体を保持してよいか。','一般に成功後だけ公開する方が安全。部分的な資源があれば生成側で解放し、失敗した状態を再利用しない契約を定める。'),('synchronizedにすれば読込の遅延は消えるか。','消えない。同時初期化を抑えられても、他の呼出側はロックやI/Oを待つ。非同期化をする場合は契約自体も検討する。'),('代理の寿命が長いと追加で何を決めるか。','キャッシュの鮮度、実体の破棄と再生成、認可の再確認などを決める。一度生成して永久に使うことが常に正しいとは限らない。')],
 '''
 static class RetryingDocument implements Document {
     private final java.util.function.Supplier<Document> loader;
     private Document real;
     RetryingDocument(java.util.function.Supplier<Document> loader) { this.loader = loader; }
     public synchronized String read() {
         if (real == null) real = java.util.Objects.requireNonNull(loader.get());
         return real.read();
     }
 }
 ''')

add('chain-of-responsibility','担当の並び順も業務ルールである',
 '少額はチーム、大きな額は部署が承認する。上限の大きい担当を先頭へ移しても、同じ結果になるかを確認する。',
 '最初に処理できた担当で止まる方式では、並び順が結果を決める。誰も扱えない要求と不正な入力の扱いを明示する。',
 ['通常順では五十はteam、六百はdepartmentとなる。部署を先頭へ移すと五十もdepartmentが処理する。「全担当が同じ契約を持つから自由に並べ替えられる」という判断は成り立たない。',
  '二千は終端まで届いてrejected、負の値は入力エラーになる。未処理と不正入力を区別すると、監視や呼出側の回復方針を決めやすい。全担当を必ず実行するフィルター列とは、停止条件を分けて説明する。'],
 [('責任連鎖','担当を組立で替えやすい。順序・停止条件・終端を試験する。'),('明示的な条件分岐','担当が少数で固定なら見通しがよい。順序がコードに直接表れる。')],
 [('通常順で50 / 600','team / department','担当の上限と停止位置を確かめる。'),('通常順で2000 / -1','rejected / invalid','未処理と入力エラーを区別する。'),('部署を先頭にして50','reordered=department','順序の変更で結果が変わる。')],
 '''
 Approver usual = new LimitApprover(100, "team", new LimitApprover(1000, "department", null));
 System.out.println(usual.approve(50));
 System.out.println(usual.approve(600));
 System.out.println(usual.approve(2000));
 try { usual.approve(-1); }
 catch (IllegalArgumentException e) { System.out.println("invalid"); }
 Approver reversed = new LimitApprover(1000, "department", new LimitApprover(100, "team", null));
 System.out.println("reordered=" + reversed.approve(50));
 ''','''
 team
 department
 rejected
 invalid
 reordered=department
 ''',
 [('上限ちょうど100と101では何を期待するか。','100はteam、101はdepartment。等号を含む境界のテストを定義し、比較演算の誤りを検出する。'),('担当が処理した後も次へ渡すなら同じ設計か。','責任連鎖の変種として考えられるが、ここでの最初に処理して停止する契約とは異なる。二重承認や副作用の重複を含めて停止条件を定める。'),('すべての担当へ必ず監査情報を渡したい場合は。','承認の担当選択とは責務を分ける案がある。処理列やイベント通知などを比較し、承認が止まっても監査が欠けない要件を表す。')])

add('command','同じCommandを二度実行すると、undoは戻せるか',
 '画面の再操作で同じAppendオブジェクトが二回使われた。二回undoすれば元へ戻るはず、という期待を検証する。',
 '元のAppendは一つの要求を一度だけ実行する前提。実行前の長さを一つのフィールドへ上書きするため、再使用すると履歴が壊れる。',
 ['同じAppendを二回実行すると、oldLengthは二回目の値で上書きされる。履歴に積まれた二つの参照も同じオブジェクトなので、二回目のundoが最初の実行前の長さを知らず、文書はAまで戻らない。',
  '一回ごとに新しい要求を生成すれば、この例の前提を保てる。再実行自体を許す設計なら、要求の内容と各実行の取り消し情報を分ける案がある。外部編集や非同期実行まで混ぜる場合は、逆順の取り消しだけでは足りない。'],
 [('要求を毎回newする','一回の実行に一個の取り消し情報が対応する。小さな編集履歴で単純に扱える。'),('実行結果とundo情報を別にする','同じ要求内容を再利用しやすいが、実行と履歴の型や寿命が増える。')],
 [('同じAppendを二回実行','reused=ABB','oldLengthが二回目の値へ上書きされる。'),('同じ要求のundoを二回','reused-after-undo=AB','Aへ戻らず、契約の前提違反が表れる。'),('別のAppendを二回使う','fresh-after-undo=A','各実行の取り消し情報が独立する。')],
 '''
 StringBuilder reused = new StringBuilder("A");
 History first = new History();
 Command same = new Append(reused, "B");
 first.run(same); first.run(same);
 System.out.println("reused=" + reused);
 first.undo(); first.undo();
 System.out.println("reused-after-undo=" + reused);
 StringBuilder fresh = new StringBuilder("A");
 History second = new History();
 second.run(new Append(fresh, "B")); second.run(new Append(fresh, "B"));
 second.undo(); second.undo();
 System.out.println("fresh-after-undo=" + fresh);
 ''','''
 reused=ABB
 reused-after-undo=AB
 fresh-after-undo=A
 ''',
 [('再実行を禁止するなら、どこで検査するか。','Commandの実行状態やHistoryの受付で明示的に拒否する案がある。利用側の注意だけに依存せず、例外時に履歴へ積むかも定義する。'),('同じ要求内容を再利用したい場合の設計案は。','不変な要求と、一回の実行が返すundo情報を分ける。履歴が要求そのものではなく実行記録を保持すれば、状態の上書きを避けられる。'),('メール送信をundoで消せるか。','すでに相手へ届いた副作用は単純に戻せない。取消可能性、補償通知、未実行キューからの削除を区別する。')])

add('interpreter','式の形が正しくても、言語の意味は正しいか',
 'paidという語の有無で支払い済みを判定したい。unpaidまで一致するなら、条件式の構造が正しくても業務判断を誤る。',
 '終端規則が扱うのは部分文字列か単語かを定義する。複合式はその意味と評価順序に依存する。',
 ['Containsの実装は部分文字列を調べるため、unpaidもpaidを含むと評価する。木構造やAndの実装が正しくても、終端の意味が要求と異なれば結論は誤る。ここでは空白区切りの完全一致という小さな規則と比較する。',
  'Andの右側は左がfalseなら評価されない。副作用を持つ判定を混ぜると、この順序が結果へ影響する。文法、字句の境界、無効入力、評価の副作用を別々に仕様化し、パターンを使うことを言語処理の正しさと混同しない。'],
 [('直接の条件式','規則が少なければ最も読みやすい。式を保存・組合せる必要があるか確認する。'),('構文木と評価器','小さな言語を組み立てやすい。大きな文法には既存の解析技術やライブラリを比較する。')],
 [('Contains(paid)でunpaidを評価','substring=true','部分一致という元の規則に従う。'),('空白区切りの語で比較','token=false','業務が求める意味との差を示す。'),('false AND probe','and=false / rightCalls=0','短絡評価で右側は実行されない。')],
 '''
 System.out.println("substring=" + new Contains("paid").eval("unpaid"));
 Expr token = text -> java.util.Arrays.stream(text.split("\\\\s+"))
     .anyMatch(word -> word.equals("paid"));
 System.out.println("token=" + token.eval("unpaid"));
 System.out.println("token-paid=" + token.eval("urgent paid"));
 java.util.concurrent.atomic.AtomicInteger calls = new java.util.concurrent.atomic.AtomicInteger();
 Expr no = text -> false;
 Expr probe = text -> { calls.incrementAndGet(); return true; };
 System.out.println("and=" + new And(no, probe).eval("paid"));
 System.out.println("rightCalls=" + calls.get());
 ''','''
 substring=true
 token=false
 token-paid=true
 and=false
 rightCalls=0
 ''',
 [('paid unpaidを入力したとき、単語一致だけで支払い済みと判断してよいか。','業務の文法と優先順位による。相反する語の扱い、無効な入力の拒否などを定義し、文字列検索だけで状態の真偽を決めない。'),('右側の判定が監査ログを必ず残す設計は安全か。','短絡で呼ばれないため安全ではない。監査の副作用を真偽判定から分離するか、評価の規則を明確に変更する。'),('字句解析・構文解析はどこにあるか。','この例は式の木を直接組み立てており省略している。外部文字列を受けるなら長さ制限、文法エラー、解析と評価の費用も扱う。')])

add('iterator','反復子が独立することと、データの複製は別',
 '同じプレイリストを二人が別々の位置から走査する。元の配列を後から書き換えた影響と、終端の例外も確認する。',
 '各Iteratorは独立した現在位置を持つ。今回のPlaylistは入力配列を複製するが、一般のIteratorがデータのスナップショットを保証するわけではない。',
 ['二つのiteratorを作ると、どちらも最初はintroを返す。最初の反復子を進めても、二つ目の位置は変わらない。入力配列のchangedが見えないのは、Playlistのコンストラクタがcloneしたためである。',
  '終端を越えたnextはNoSuchElementExceptionになる。反復子の独立性、コレクション変更時の方針、データの複製、スレッド安全性は別の契約である。標準のIterableやIteratorで満たせる部分を再発明しない判断も大切になる。'],
 [('標準コレクションを使う','基本の走査には十分なことが多い。変更時の契約は利用する型で確認する。'),('独自のIteratorを実装','木や外部資源など独自の走査に有効。終端、取消、資源解放の契約が増える。')],
 [('一つ目と二つ目のnext','first=intro / second=intro','走査位置が別々である。'),('一つ目をさらに進める','next=finale','入力配列の書換えは今回の複製後の配列へ影響しない。'),('終端を越える','end=NoSuchElementException','契約に従って例外にする。')],
 '''
 String[] input = {"intro", "finale"};
 Playlist playlist = new Playlist(input);
 input[0] = "changed";
 java.util.Iterator<String> first = playlist.iterator(), second = playlist.iterator();
 System.out.println("first=" + first.next());
 System.out.println("second=" + second.next());
 System.out.println("next=" + first.next());
 try { first.next(); }
 catch (java.util.NoSuchElementException e) { System.out.println("end=NoSuchElementException"); }
 ''','''
 first=intro
 second=intro
 next=finale
 end=NoSuchElementException
 ''',
 [('iteratorを二つ作れば、元データも二つ複製されるか。','一般には複製されない。今回も走査位置は二つだが、保存したsongs配列は同じものを参照する。'),('曲の要素自体が可変な場合、配列のcloneだけで独立するか。','しない。配列の要素参照は共有する。スナップショットを必要とするなら、要素の可変性と複製範囲も定義する。'),('走査中に削除したい場合のテストは。','利用するIteratorの削除対応と呼出順の契約を確認する。未対応操作、next前の削除、同時変更を想定した仕様が必要。')])

add('mediator','仲介が部品を直すと、変更通知が再入する',
 '入力の前後の空白を取り除いてから、送信ボタンを更新する。仲介が入力を修正した結果、もう一度changedが呼ばれる。',
 '非nullの文字列を単一スレッドで扱う。同期的な再入で同じ調整を無限に繰り返さず、正規化した後の値からボタン状態を決める。',
 ['入力欄のsetは毎回仲介へ通知する。仲介から再びsetを呼ぶと、その呼出の途中でchangedへ入り直す。この実習は調整中のフラグで再入を止め、外側の呼出が最後の値を評価する方式を選ぶ。',
  'フラグはfinallyで戻すため、調整途中の例外で永遠に更新が止まる状態を避ける。ただし単一スレッドでの小さな正規化に限定している。非同期通知や複数の依存ルールでは、バッチ更新やイベントの待ち行列も比較する。'],
 [('再入の抑止フラグ','同期的で小さな調整には単純。抑止中の必要な変更まで落とさないかを確認する。'),('バッチ更新と最後の再評価','複数部品の整合を扱いやすい。更新単位や例外時の確定方針が増える。')],
 [('空白付きhelloを設定','value=hello','正規化による再通知がある。'),('ボタン状態を評価','enabled=true','正規化後の値から決める。'),('空白だけに変更','empty-enabled=false','再度の更新でもフラグが残っていない。')],
 '''
 NormalizeForm form = new NormalizeForm();
 form.field.set(" hello ");
 System.out.println("value=" + form.field.value());
 System.out.println("enabled=" + form.button.enabled);
 System.out.println("adjustments=" + form.adjustments);
 form.field.set("   ");
 System.out.println("empty-enabled=" + form.button.enabled);
 ''','''
 value=hello
 enabled=true
 adjustments=1
 empty-enabled=false
 ''',
 [('フラグを処理の最後でfalseへ戻すだけでよいか。','途中の例外でフラグが残る。finallyで戻し、失敗後に次の入力を処理できることも試験する。'),('抑止中に別の有効な変更が来るとどうなるか。','単純なフラグでは見落とす可能性がある。再評価要求の記録、バッチ処理、キューなどを要件に合わせて設計する。'),('この仲介を複数スレッドから使えるか。','この例では保証しない。UIスレッドへ集約するか、同期と状態の一貫性を別途定義する。')],
 '''
 static class NormalizeForm implements Mediator {
     final Field field = new Field(this);
     final Button button = new Button();
     private boolean updating;
     int adjustments;
     public void changed() {
         if (updating) return;
         updating = true;
         try {
             adjustments++;
             String normalized = field.value().trim();
             if (!normalized.equals(field.value())) field.set(normalized);
             button.enabled = !field.value().isBlank();
         } finally { updating = false; }
     }
 }
 ''')

add('memento','保存した状態を、別の所有者へ戻してよいか',
 '複数のエディターを開く。Aのスナップショットを誤ってBへ渡しても、別文書を書き換えないようにしたい。',
 'Snapshotの内部を隠すだけでなく、どの所有者が作った状態かを検証する。永続化するなら版や互換性も別に扱う。',
 ['元のEditorはSnapshotの内容を直接戻すため、別のEditorが作ったものも受け入れる。型が合うことと、そのインスタンスへ復元してよいことは別の条件である。',
  'GuardedEditorは所有者ごとのトークンをSnapshotへ含め、restoreで参照を検査する。これは同じ実行中の所有者の検証であり、保存ファイルの真正性や長期互換性を保証する仕組みではない。Main内への型の配置も教材上の便宜で、実製品では所有者を別ファイルへ分離する。'],
 [('所有者トークンを検査','実行中の取り違えを検出しやすい。復元可能な所有者の範囲を明示する。'),('版付きの保存形式を使う','永続化の互換性を扱えるが、変換・検証・保存期限などの責任が増える。')],
 [('元のEditorで別の保存値を復元','legacy-foreign=draft','型が合えば受け入れる実装である。'),('所有者検査付きで別文書へ復元','guarded-foreign=rejected','状態を変更する前に拒否する。'),('同じ所有者へ復元','own=draft','正しい保存値は利用できる。')],
 '''
 Editor a = new Editor(), b = new Editor(); a.type("draft"); b.type("other");
 b.restore(a.save()); System.out.println("legacy-foreign=" + b.text());
 GuardedEditor first = new GuardedEditor(), second = new GuardedEditor();
 first.type("draft");
 var saved = first.save();
 try { second.restore(saved); }
 catch (IllegalArgumentException e) { System.out.println("guarded-foreign=rejected"); }
 first.type("edited"); first.restore(saved);
 System.out.println("own=" + first.text());
 ''','''
 legacy-foreign=draft
 guarded-foreign=rejected
 own=draft
 ''',
 [('所有者を検査する前にtextを代入してしまうと何が問題か。','拒否しても別文書の状態をすでに変えてしまう。妥当性を検証してから変更する順序をテストする。'),('保存をディスクへ書けばprivateだから安全か。','privateは保存データの改ざん防止ではない。形式・版・検証・必要な機密性と真正性は別の設計対象になる。'),('MementoとCommandを組み合わせる案は。','実行前のMementoを操作履歴へ保持し、undoで復元する案がある。ただしメモリ量、所有者、外部副作用の扱いは残る。')],
 '''
 static class GuardedEditor {
     private final Object owner = new Object();
     private String text = "";
     private record Saved(Object owner, String text) {}
     void type(String value) { text = value; }
     String text() { return text; }
     Saved save() { return new Saved(owner, text); }
     void restore(Saved saved) {
         if (saved.owner() != owner) throw new IllegalArgumentException("foreign snapshot");
         text = saved.text();
     }
 }
 ''')

add('observer','通知の途中で解除すると、今回も止まるか',
 '最初の購読者が監査の購読を解除した。まだ呼んでいない監査へ、今回のイベントを配ってよいかを仕様化したい。',
 'このEventsは通知開始時の購読者一覧をコピーして使う。通知中の解除は次回のpublishから有効で、今回のコピーは変えない。',
 ['最初の購読者がauditを解除しても、今回のコピーにはauditが残っているためoneは届く。次のtwoでは購読一覧から消えているため届かない。解除メソッドの完了と、すでに開始した配送の停止を区別する。',
  '途中のRuntimeExceptionは捕捉され、今回のauditまで進む。この例は単一スレッドの同期通知であり、非同期のキューや並行解除には別の競合条件がある。購読解除の即時性が必要なら、配信直前の有効性検査や購読トークンなどを比較する。'],
 [('通知時のスナップショット','通知中の一覧変更を扱いやすい。解除の効果が次回からという契約になる。'),('配信直前に有効性を検査','未開始の配信を止めやすいが、並行処理では検査と呼出の間の競合も設計する。')],
 [('oneの最初の購読者がauditを解除','first: one','元の一覧からは解除される。'),('oneの残りを通知','listener failed / audit: one','取得済みのコピーへ今回の解除は反映されない。'),('twoを通知','first: two / listener failed','次回はauditが呼ばれない。')],
 '''
 Events events = new Events();
 Listener audit = event -> System.out.println("audit: " + event);
 Listener first = event -> {
     System.out.println("first: " + event);
     events.unsubscribe(audit);
 };
 events.subscribe(first);
 events.subscribe(event -> { throw new IllegalStateException("offline"); });
 events.subscribe(audit);
 events.publish("one");
 events.publish("two");
 ''','''
 first: one
 listener failed
 audit: one
 first: two
 listener failed
 ''',
 [('unsubscribeが戻れば、非同期の通知も一切来ないと考えてよいか。','契約次第であり一般には断定できない。すでにキューへ入った通知や実行中のコールバックの扱いを明記する。'),('例外を捕捉して先へ進むだけで実用上十分か。','失敗の観測、監視、再試行、重複、重要な通知の保証などを別途決める。無言で失敗を捨てる方針にはしない。'),('通知順に依存する購読者がいる場合は。','順序を明示的な契約にするか、依存する処理を一つの協調役へまとめる。Observerという名前だけに順序保証を期待しない。')])

add('state','禁止操作と、繰り返し操作を状態ごとに試す',
 '発送ボタンの二重操作と、支払い前の発送を扱う。エラー応答だけでなく、その後の状態が正しいことを確認する。',
 '禁止された操作は状態を進めない。繰り返し操作が無害か、拒否か、副作用を再実行するかを操作ごとに決める。',
 ['未払いでshipを二度呼んでも、両方pay firstである。その後のpayがpaidになることからも、拒否によって支払い済みへ進んでいないと確認できる。エラーメッセージだけを試験して終わらせない。',
  '支払い後の二度目のpayと、発送後の二度目のshipは、完了済みの案内を返す。これはメモリ内の直列操作の契約である。同時要求や再起動後まで二重決済を防ぐには、状態の永続化、排他や比較更新、外部操作の識別子などを設計する。'],
 [('Stateオブジェクト','状態ごとの複雑な振る舞いを分けられる。遷移先と禁止操作を一覧で検査する。'),('enumと遷移表','状態と操作が少ない場合は全体を把握しやすい。型を増やすより簡潔なこともある。')],
 [('未払いでshipを二回','pay firstを二回','拒否後も未払いである。'),('payを二回','paid / already paid','同じ操作の契約を状態ごとに確認する。'),('shipを二回','shipped / already shipped','二回目に新しい発送処理を実行しない仕様。')],
 '''
 Order order = new Order();
 order.ship(); order.ship();
 order.pay(); order.pay();
 order.ship(); order.ship();
 ''','''
 pay first
 pay first
 paid
 already paid
 shipped
 already shipped
 ''',
 [('禁止操作の試験に、応答以外の何を加えるか。','状態が変わらないこと、外部の副作用が起きないこと、その後の正当な操作が成功することを加える。'),('状態の代入後に外部決済が失敗すると何が起こるか。','メモリ上は支払い済みでも決済が完了していない不整合が起こり得る。処理中状態や確定手順、失敗時の回復を要件化する。'),('Strategyとの違いを、この実習から説明する。','同じshipの結果がライフサイクル上の状態で変わり、許可された遷移がある。独立した計算手段を選ぶ問題ではない。')])

add('strategy','交換可能な計算でも、金額の契約は必要',
 '基準額の上限が三億に広がる。元の九割計算をそのまま使うと、途中の整数演算がオーバーフローする。',
 '非負の整数を最小単位の金額として扱い、九割計算では端数を切り捨てる。実際の通貨や税の要件が違えば別の契約にする。',
 ['intの三億に九を掛けると、十で割る前に上限を越える。Strategyで計算を別クラスへ分けても算術は正しくならない。元の例の小さな値という前提を広げた時点で、境界条件を見直す必要がある。',
  '実習では先にlongへ拡張して計算し、非負を検査し、結果をintへ戻す。すべての方策が同じ単位・丸め・入力範囲へ従うことが交換可能性の前提である。通貨や端数規則が異なるなら、値の型や契約も含めて分ける。'],
 [('longで中間演算','この整数の九割計算には十分。単位と丸めの仕様を明示する。'),('専用の金額型やBigDecimal','通貨や小数規則を表しやすい。スケールや丸め方の指定と複雑さが増える。')],
 [('元のMemberで三億','naive-negative=true','掛け算の中間結果がintの範囲を越える。'),('安全な方策で三億と一','large=270000000 / small=0','この実習では非負の値の切り捨てを採用。'),('負値を入力','negative=rejected','方策を替えても入力契約を守る。')],
 '''
 int large = 300_000_000;
 System.out.println("naive-negative=" + (new Member().price(large) < 0));
 Pricing checked = base -> {
     if (base < 0) throw new IllegalArgumentException("negative amount");
     return Math.toIntExact((long) base * 9 / 10);
 };
 System.out.println("large=" + new Checkout(checked).total(large));
 System.out.println("small=" + new Checkout(checked).total(1));
 try { new Checkout(checked).total(-1); }
 catch (IllegalArgumentException e) { System.out.println("negative=rejected"); }
 ''','''
 naive-negative=true
 large=270000000
 small=0
 negative=rejected
 ''',
 [('計算の最後だけlongへキャストすれば直るか。','直らない。intの掛け算で先に壊れた値を変換しても戻らないため、演算前に一方をlongへ広げる。'),('別の方策が四捨五入を使っても交換可能か。','契約で方策ごとの端数規則を許しているかによる。同じルールのはずなら不一致なので、共通の契約試験へ含める。'),('Strategyの単体試験だけで組立は保証できるか。','できない。顧客条件から正しい方策を選ぶ組立の試験と、計算自体の試験を分ける。')])

add('template-method','終了処理は、成功時だけか、例外時にも必要か',
 '出力本体が失敗しても資源を解放したい。一方、成功を示す表示を失敗時に出してはいけない。',
 '正常終了の通知と、必ず行う後始末を区別する。固定した手順でも、例外がどの段階を飛ばすかを検証する。',
 ['元のexportはbegin、body、endという順だが、bodyの例外でendへ到達しない。正常系の順番を図に描けることと、失敗時の後始末が保証されることは別である。',
  '比較用のSafeExporterは成功通知をtry内、cleanupをfinallyへ置く。失敗時はcleanupの後に例外が伝わる。実資源を扱うならtry-with-resourcesなども比較し、後始末自身の例外や獲得途中の失敗を含む契約を決める。'],
 [('finally / try-with-resources','必須の後始末を表す。成功通知と同じ処理へまとめない。'),('Strategyへ手順を委譲','実行時の交換が必要なら候補。例外と後始末の責任はどちらの設計でも残る。')],
 [('元のexportでbodyが失敗','begin / legacy=failure','endは呼ばれない。'),('比較版でbodyが失敗','begin / cleanup / safe=failure','成功通知を出さず後始末を行う。'),('比較版でbodyが成功','begin / body / success / cleanup','成功通知の後にも後始末を行う。')],
 '''
 Exporter original = new Exporter() {
     protected void body() { throw new IllegalStateException("failure"); }
 };
 try { original.export(); }
 catch (IllegalStateException e) { System.out.println("legacy=" + e.getMessage()); }
 SafeExporter guarded = new SafeExporter() {
     protected void body() { throw new IllegalStateException("failure"); }
 };
 try { guarded.export(); }
 catch (IllegalStateException e) { System.out.println("safe=" + e.getMessage()); }
 new SafeExporter() {
     protected void body() { System.out.println("body"); }
 }.export();
 ''','''
 begin
 legacy=failure
 begin
 cleanup
 safe=failure
 begin
 body
 success
 cleanup
 ''',
 [('endをそのままfinallyへ移すだけでよいか。','endの意味による。出力の成功通知なら誤った表示になる。必須の資源解放と成功時の処理を別の責任にする。'),('beginが例外になった場合、どこまで解放するか。','何を獲得済みかによる。部分的な獲得の後始末を獲得側へ閉じ込めるか、資源ごとの管理構造を使う。'),('cleanupの例外で元の失敗を隠してよいか。','原因調査を妨げるため例外の保持方針を決める。try-with-resourcesの抑制例外など、言語の支援も検討する。')],
 '''
 static abstract class SafeExporter {
     final void export() {
         System.out.println("begin");
         try { body(); System.out.println("success"); }
         finally { System.out.println("cleanup"); }
     }
     protected abstract void body();
 }
 ''')

add('visitor','処理追加と、要素追加の費用は対称ではない',
 '円と長方形に、説明に加えて面積計算を追加する。図形のクラスを編集せずに追加できるか、次に三角形が増える場合も考える。',
 '安定した要素型の集合へ新しい処理を追加する設計である。要素型が増えるとVisitorの契約と各実装へ変更が波及する。',
 ['Areaという訪問者を追加すると、既存のCircleとRectangleへ手を入れず面積を出せる。acceptが要素の具体型に応じたvisitへ接続するため、利用側に型判定の大きな分岐を増やさずに済む。',
  'Triangleを増やしてvisit(this)しようとしても、現在のVisitorには三角形を受ける操作がない。すべての訪問者へ対応を追加するか、未知の要素の方針を変える必要がある。どちらの軸が頻繁に変わるかを見極めることが採用判断になる。'],
 [('Visitorで操作を追加','要素の種類が安定し、操作が増える場合に適する。要素側の必要な状態公開も確認する。'),('要素自身の多態メソッド','要素型が増えやすく操作が少ないなら単純。処理追加は各要素への変更になる。')],
 [('Areaを追加してCircleへ適用','circle-area=12.57','要素側のacceptは再利用する。'),('同じAreaをRectangleへ適用','rectangle-area=12','型別のvisitが呼ばれる。'),('Triangleを追加する変更案','visit(Triangle)が必要になる','この行は変更影響の分析であり、実行結果ではない。')],
 '''
 Visitor area = new Area();
 for (Shape shape : java.util.List.of(new Circle(2), new Rectangle(3, 4)))
     System.out.println(shape.accept(area));
 ''','''
 circle-area=12.57
 rectangle-area=12
 ''',
 [('新しい処理を追加するときの変更箇所は。','新しいVisitor実装と利用側の組立が主になる。既存要素のacceptが契約を満たしていれば、要素のクラスは変えずに済む。'),('Triangle.acceptでv.visit(this)とだけ書けばコンパイルできるか。','現在のVisitorではできない。三角形を受けるvisitの契約と既存実装への対応が必要であり、処理追加と要素追加の費用は非対称。'),('Visitorへ必要な内部状態をすべて公開するべきか。','必要最小限の読み取り契約に留める。操作の追加を容易にするためにカプセル化を過度に崩すなら、別の設計も比較する。')],
 '''
 static class Area implements Visitor {
     public String visit(Circle circle) {
         return String.format(java.util.Locale.ROOT, "circle-area=%.2f",
             Math.PI * circle.radius() * circle.radius());
     }
     public String visit(Rectangle rectangle) {
         return "rectangle-area=" + Math.multiplyExact(rectangle.width(), rectangle.height());
     }
 }
 ''')

def java_for(source,lab):
    """Use the guide's unchanged roles, replacing only the demonstration entry point."""
    prefix=source[:source.index('    public static void main')]
    from textwrap import indent
    support=indent(lab['support'],'    ')+'\n' if lab['support'] else ''
    return prefix+support+'    public static void main(String[] args) throws Exception {\n'+indent(lab['main'],'        ')+'\n    }\n}'
