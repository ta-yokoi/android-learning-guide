"""Authored Android design cases. Host models validate contracts, not Android APIs."""
from textwrap import dedent
WORKBOOKS={}
def add(key,title,request,contract,reading,alternatives,evidence,questions,model,cases):
    assert len(reading)==len(alternatives)==2 and len(evidence)==len(questions)==3
    WORKBOOKS[key]=dict(id=key,title=title,request=request,contract=contract,reading=reading,
        alternatives=alternatives,evidence=evidence,questions=questions,model=dedent(model).strip(),cases=cases,language='python')

add('overview','同じOS版でも、利用可能性は一致しない',
 '同じAPIレベルの二製品で、録音ボタンの表示と失敗の説明を変えたい。機能宣言と実際の取得成功を分ける。',
 'このサンプルは最低API23とし、公開機能、権限、実行時準備を別の条件で保持する。録音API全般の最低版を示すものではなく、全条件の成立も処理成功の実証ではない。',
 ['OS版だけで画面を分岐すると、マイクを持たない製品にも録音可能と表示する。targetSdkはアプリ側の前提であり、機器が存在する証拠としては使えない。条件ごとに不足理由を返せば、製品差を説明できる。',
  'モデルのeligibleは試行してよいという判定に留まる。実装ではAudioRecord等の初期化・読み取り結果、利用中の機器やポリシーを観測する。試験表は条件の全組合せではなく、各条件だけを不足させるケースから作る。'],
 [('OS版だけの分岐','簡単だが機器・権限・製品構成を見落とす。'),('条件を別々に保持','不足理由と試験を対応づけやすい。条件更新時の再評価が必要。')],
 [('API=36、mic=false','missing_feature','OS版と機器の公開を分ける。'),('mic=true、permission=false','permission_required','宣言された機能は許可の証拠ではない。'),('全条件を満たす','eligible_not_proven','取得結果による最終確認は実機で行う。')],
 [('targetSdkを上げれば存在しない機器も使えるか。','使えない。対象APIの変更と、製品が公開する機能・機器を別々に確認する。'),('全条件trueの後に必要な試験は。','初期化失敗、別アプリの利用、読み取り失敗を含む。事前条件を成功の証拠へ格上げしない。'),('製品差の不具合報告へ何を残すか。','端末・ビルド、端末API、targetSdk、機能宣言、権限、再現操作と取得結果を一組で残す。')],
 '''
 def decide(x):
     if x['api'] < 23: return 'unsupported_api'
     if not x['mic']: return 'missing_feature'
     if not x['permission']: return 'permission_required'
     if not x['ready']: return 'not_ready'
     return 'eligible_not_proven'
 ''',[
 ('no-mic',dict(api=36,mic=False,permission=True,ready=True),'missing_feature'),
 ('denied',dict(api=36,mic=True,permission=False,ready=True),'permission_required'),
 ('eligible',dict(api=36,mic=True,permission=True,ready=True),'eligible_not_proven')])

add('layers','受付と機器反映の間に、失敗する時間がある',
 '機器への値変更が受け付けられた後、ドライバー側で失敗する。UIが成功と先走らない状態モデルにする。',
 '要求値・受付状態・観測値・世代を分ける。古い世代の観測は、現在の要求の完了に使わない。',
 ['受付は入力や権限の検査を通過した時点かもしれない。実機の反映は別の時点なので、受付をobservedへ代入すると未反映が見えなくなる。要求中と最後の観測値を同時に表示する設計が候補になる。',
  '値が一致していても再起動前の通知なら現在の証拠にはならない。要求ID、接続世代、取得時刻、必要なら許容差を含める。モデルは同世代の完全一致に限定し、実機値の出典と遅延は実機のログで検証する。'],
 [('受付時に成功表示','反応は速いが、失敗や遅延を隠してしまう。'),('要求と観測を分離','未反映を表現できる。期限超過・再照会の責任が増える。')],
 [('accepted=true、実測3、要求5','pending','受付済みでも反映していない。'),('値5だが旧世代','stale','値だけの比較を避ける。'),('同世代で値5','observed_match','その観測に対する一致を判定する。')],
 [('受付応答だけを使うテストで何を見落とすか。','受付後の失敗、通知の遅延・欠落・順序逆転を見落とす。境界ごとの時刻と結果を照合する。'),('タイムアウトは機器が失敗した証拠か。','必ずしも違う。反映済みで通知だけ失った可能性もあり、不明と失敗を分けて再照会する。'),('すべてのAPIがHALを通ると考えてよいか。','よくない。対象機能の実装経路を特定してから責任の境界を置く。')],
 '''
 def decide(x):
     if x['event_generation'] != x['generation']: return 'stale'
     if not x['accepted']: return 'not_accepted'
     return 'observed_match' if x['observed'] == x['requested'] else 'pending'
 ''',[
 ('accepted-only',dict(generation=2,event_generation=2,accepted=True,observed=3,requested=5),'pending'),
 ('old-event',dict(generation=2,event_generation=1,accepted=True,observed=5,requested=5),'stale'),
 ('matched',dict(generation=2,event_generation=2,accepted=True,observed=5,requested=5),'observed_match')])

add('execution','CPUを使わない待ちでも、メインは止まる',
 '低速通信の間だけ入力が反応しない。suspendという宣言やCPU使用率ではなく、入力が処理を始めるまでの待ちを説明する。',
 'モデルは一つの直列キュー。先行するブロッキング処理が終わるまで、入力の処理は始められない。ANRの条件や閾値は再現しない。',
 ['時刻ゼロから百ミリ秒の待ちがメインを占有すると、十ミリ秒に到着した入力は九十ミリ秒待つ。CPUがアイドルでも、そのキューで入力を処理できない点は変わらない。',
  'I/Oを別の実行場所へ移す案では、結果を戻す先と処理の寿命を決める。取消不能なブロッキング処理、タイムアウト、例外、画面離脱を含めて確認する。モデルの待ち時間だけから実端末のANR発生を断定しない。'],
 [('Main上で待つ','実装は短いが入力と描画を遅らせる。'),('I/Oの実行場所を分ける','応答性を保ちやすい。結果の受取先と取消・期限を設計する。')],
 [('先行処理100ms、入力到着10ms','input_wait=90ms','直列キューで前の処理を待つ。'),('先行処理0ms','input_wait=0ms','I/Oがそのキューを占有しないモデル。'),('先行処理15ms、入力10ms','input_wait=5ms','短い処理でも予算と頻度を確認する。')],
 [('suspendなら必ず別スレッドになるか。','ならない。内部の処理と実行コンテキストを確認する。'),('低CPU使用率からUI正常と判断できるか。','できない。ブロックやロック待ちを含め、入力・描画の進行を時間軸で確認する。'),('実機では何を測るか。','同じ再現操作のMainの実行・待ち、入力到着、描画と提示をPerfetto等で照合する。')],
 '''
 def decide(x):
     start = max(x['prior_finished_ms'], x['input_arrived_ms'])
     return f"input_wait={start - x['input_arrived_ms']}ms"
 ''',[
 ('blocked',dict(prior_finished_ms=100,input_arrived_ms=10),'input_wait=90ms'),
 ('offloaded',dict(prior_finished_ms=0,input_arrived_ms=10),'input_wait=0ms'),
 ('short',dict(prior_finished_ms=15,input_arrived_ms=10),'input_wait=5ms')])

add('ipc','応答の相手は、送った時と同じ世代か',
 'サービス再起動の後、同じ要求番号の古いコールバックが届く。新しい要求の結果として反映しないようにする。',
 '要求番号だけでなく接続世代も照合する。onewayは相手の成功やコールバック配送を保証しない。',
 ['要求番号は再接続後に再利用されることがある。同じ番号でも相手の世代が違う応答を通すと、以前の成功で現在の画面が更新される。接続世代と要求IDを一組として扱う。',
  '期限を越えた応答を無視するか取り込むかは機能の契約で決める。取消を送ったことも相手が停止した証拠にはならない。モデルは受信側の選別だけを検証し、Binderの死亡検出や配送は実機で確認する。'],
 [('要求IDだけを照合','小さく実装できるが再利用と再接続に弱い。'),('接続世代と要求IDを照合','古い結果を分離できる。世代更新と保留要求の扱いを明示する。')],
 [('世代1の結果を世代2で受信','stale_generation','再接続前の結果を捨てる。'),('同世代だが別ID','unmatched_request','別の操作を完了扱いにしない。'),('同世代・同ID','accept_result','受信契約を満たす。実機反映は別途観測する。')],
 [('onewayの返却で成功表示してよいか。','成功や実機反映の契約でなければ不可。受付と結果通知を別に扱う。'),('取消後のコールバックは絶対に来ないか。','契約と実装による。受信側でも世代や有効性を検査する。'),('サービス死亡時の保留要求をどうするか。','失敗または結果不明へ遷移させ、再試行の識別子と重複処理を設計する。')],
 '''
 def decide(x):
     if x['callback_generation'] != x['generation']: return 'stale_generation'
     if x['callback_id'] != x['request_id']: return 'unmatched_request'
     return 'accept_result'
 ''',[
 ('old-service',dict(generation=2,callback_generation=1,request_id=7,callback_id=7),'stale_generation'),
 ('other-request',dict(generation=2,callback_generation=2,request_id=7,callback_id=8),'unmatched_request'),
 ('current',dict(generation=2,callback_generation=2,request_id=7,callback_id=7),'accept_result')])

add('components','画面の入口と、業務操作の一意性を分ける',
 '同じ注文へのIntentが二度届き、画面も再作成された。画面のインスタンス数を使って二重処理を防ごうとしている。',
 '画面やタスクの寿命と業務要求の識別子は別。ここでは注文要求IDごとに一度だけ受理するメモリ内のモデルを使う。',
 ['Activityの再作成や起動モードの違いを業務要求の重複と同一視すると、画面が変わっただけで再注文したり、正当な別注文を落としたりする。Intentの受取は業務の入力として検査し直す。',
  'モデルの集合は同じプロセス内だけで有効であり、プロセス終了で失われる。本当に二重決済を防ぐにはサーバー側の識別子や永続記録が必要になる。画面遷移のフラグだけで外部副作用の一意性を保証しない。'],
 [('画面インスタンスで判定','UIの重複には使えても業務の一意性とは一致しない。'),('要求IDで判定','別画面からの同じ要求を扱える。保持場所と期限を設計する。')],
 [('同じIDを二回受信','accepted=1','重複する業務入力を分離する。'),('異なる二つのID','accepted=2','正当な別要求を落とさない。'),('再起動後の空の記録','accepted=1','メモリだけでは以前の履歴を証明できない。')],
 [('singleTopなら二重注文を完全に防げるか。','防げない。画面の再利用と業務操作の識別・永続性は別の契約。'),('外部からのIntentに必要な検査は。','送信元の権限、入力の形式と対象へのアクセス権を確認する。内部遷移でも信頼境界を明示する。'),('同じIDで内容が違う再送はどうするか。','既存の要求内容と照合し、不一致を拒否するなどの規則を決める。IDだけの集合では検証できない。')],
 '''
 def decide(x):
     seen = set(x['stored_ids'])
     count = 0
     for request_id in x['incoming']:
         if request_id not in seen:
             seen.add(request_id)
             count += 1
     return f'accepted={count}'
 ''',[
 ('duplicate',dict(stored_ids=[],incoming=['order-1','order-1']),'accepted=1'),
 ('distinct',dict(stored_ids=[],incoming=['order-1','order-2']),'accepted=2'),
 ('memory-lost',dict(stored_ids=[],incoming=['order-1']),'accepted=1')])

add('lifecycle','再作成とプロセス終了を、同じ復元試験にしない',
 '回転では戻る入力が、プロセス終了後には消える。ViewModelが保持する範囲と永続保存を分けて説明する。',
 'このモデルのViewModelは同じ所有者の構成変更を越えて保持され、プロセス終了は越えない。永続値は保存済みのものだけ復元する。',
 ['画面のインスタンスが変わっても、同じ所有者のViewModelが残る場合がある。一方でプロセスが失われればメモリの状態も失われる。回転の成功だけで終了後の復元を保証したとは言えない。',
  'SavedStateの復元条件と永続ストレージの寿命も分ける。onDestroyが必ず来る前提でだけ保存すると終了経路を取りこぼす。実機ではPID、画面インスタンス、保存完了時刻と復元元を記録して照合する。'],
 [('ViewModelだけに保持','画面の一時状態には適するが、プロセス終了には備えられない。'),('保存済みデータから再構成','長い寿命を扱える。保存の時点と復元の優先順位を決める。')],
 [('構成変更、メモリにdraft','restored=draft','このモデルではViewModelを保持する。'),('プロセス終了、保存済みsaved','restored=saved','メモリより永続値を使う。'),('プロセス終了、未保存','restored=empty','未保存の値を保証しない。')],
 [('回転テストだけで復元を検証できるか。','できない。プロセス終了、再起動、保存途中の終了を別ケースにする。'),('onDestroyだけで保存する案の問題は。','呼ばれない終了があるため、保存すべき時点と完了の観測を別に決める。'),('SavedStateとデータベースは同じ保証か。','違う。復元条件・量・寿命・利用目的を確認し、永続的な業務データと一時的なUI状態を分ける。')],
 '''
 def decide(x):
     if x['event'] == 'configuration_change': value = x['memory']
     else: value = x['durable']
     return 'restored=' + (value if value is not None else 'empty')
 ''',[
 ('rotate',dict(event='configuration_change',memory='draft',durable='saved'),'restored=draft'),
 ('process-death',dict(event='process_death',memory='draft',durable='saved'),'restored=saved'),
 ('not-saved',dict(event='process_death',memory='draft',durable=None),'restored=empty')])

add('boot','OSの起動と、ユーザーデータの利用開始は別',
 '再起動直後に通知処理がデータを読めない。解錠前の処理と解錠後の復元を分けたい。',
 'モデルはDEとCEの利用時点だけを表す。CEは対象ユーザーの解錠前には利用しない。DEもアクセス権や製品条件を満たす必要がある。',
 ['BOOT_COMPLETED等のイベント名だけから全データが利用可能と判断しない。解錠前の実行で使うデータを最小化し、Device Encrypted領域へ置く理由と機密性を説明する。',
  '解錠後は新しく利用できる状態を読み直す。ユーザー切替や複数ユーザーの製品では、誰の解錠状態かを識別する。モデルの許可は読み取り成功の保証ではなく、追加の権限・保存・初期化を実機で検証する。'],
 [('解錠まで処理を待つ','機密データの扱いが単純。解錠前に必要な機能は提供できない。'),('必要最小限をDEへ分離','解錠前の機能に対応できる。データ配置と機密性の設計が増える。')],
 [('lockedでCEを要求','wait_for_unlock','ユーザーの準備を待つ。'),('lockedでDEを要求','eligible','保存領域の時点の条件だけを満たす。'),('unlockedでCEを要求','eligible','別の権限や取得結果も確認する。')],
 [('起動通知を受けたらすべてのCEを読めるか。','読めない。対象ユーザーの解錠と領域の条件を確認する。'),('全データをDEへ移す案は。','解錠前の必要性と機密性を評価する。便利さだけを理由に移さない。'),('実機の再起動試験で残す情報は。','対象ユーザー、起動・解錠時刻、実行された入口、アクセスした領域と例外を記録する。')],
 '''
 def decide(x):
     return 'wait_for_unlock' if x['storage'] == 'CE' and not x['unlocked'] else 'eligible'
 ''',[
 ('locked-ce',dict(storage='CE',unlocked=False),'wait_for_unlock'),
 ('locked-de',dict(storage='DE',unlocked=False),'eligible'),
 ('unlocked-ce',dict(storage='CE',unlocked=True),'eligible')])

add('power','保持要求の寿命を、画面の寿命へ暗黙に結び付けない',
 '画面を離れた後も処理がWakeLockを保持する。成功・失敗・取消のどの経路でも、所有する保持を解放する設計にしたい。',
 'モデルのleaseは処理の所有者ごとに取得・解放する。画面OFFを、処理完了やCPU休止の証拠として使わない。',
 ['画面OFFでもleaseが残るケースを別に試す。逆にleaseがゼロでも、すべての実機条件が休止可能になったとは言えない。Androidの状態、Kernelの休止、車両やホストの状態を混ぜない。',
  '取得と解放を同じ所有範囲へ置き、例外や取消でも解放する。タイムアウトは取りこぼしを抑える補助手段であり、明示的な解放を不要にしない。実機では保持の理由・所有者・継続時間と復帰後の接続を確認する。'],
 [('画面イベントだけで制御','分かりやすいがバックグラウンド処理の寿命とずれる。'),('処理の所有者で管理','解放経路を対応づけやすい。二重取得や解放漏れを観測する必要がある。')],
 [('画面OFF、所有者jobあり','leases=1','表示と保持を分ける。'),('jobを解放','leases=0','このモデルの保持がなくなる。'),('不在の所有者を解放','invalid_release','誤った所有者の操作を検出する。')],
 [('画面OFFなら通信も止まるか。','断定できない。通信・処理・OS制約を個別に観測する。'),('期限付き取得ならfinallyは不要か。','不要とはしない。必要な範囲へ保持を限定し、正常・例外・取消の経路で解放する。'),('復帰後に何を再確認するか。','サービス接続、対象機器、観測状態の鮮度など、休止中に変化し得る条件を読み直す。')],
 '''
 def decide(x):
     owners = set(x['owners'])
     for owner in x['release']:
         if owner not in owners: return 'invalid_release'
         owners.remove(owner)
     return f'leases={len(owners)}'
 ''',[
 ('screen-off',dict(owners=['job'],release=[],screen_on=False),'leases=1'),
 ('completed',dict(owners=['job'],release=['job'],screen_on=False),'leases=0'),
 ('wrong-owner',dict(owners=['job'],release=['screen'],screen_on=False),'invalid_release')])

add('graphics','処理区間が短くても、提示が遅れることがある',
 'CPU側の描画準備を速くしたのにカクつきが残る。アプリ区間と画面提示までの遅れを分けて評価する。',
 '同じ時計上の入力から提示までを比較する。並行動作するCPU・GPU・合成の区間を単純に加算しない。',
 ['アプリの区間が四ミリ秒でも、提示が三十五ミリ秒なら後段や待ちを調べる余地がある。局所的な計測値だけでは、ユーザーが見る一枚のフレームの遅れを説明できない。',
  '表示周期、対象フレーム、入力の時刻、GPUや合成の待ちをそろえる。実習の二十ミリ秒は説明用の要求予算であり、Android全端末に共通する閾値ではない。トレースの実測とモデルの計算を区別する。'],
 [('関数単体の短縮','局所的な改善を測れるが、後段の待ちを見落とす。'),('入力から提示まで照合','体感に近い遅れを追える。フレームと時刻の対応づけが必要。')],
 [('app=4ms、入力0、提示35','late=35ms','短いアプリ区間だけで正常とは言えない。'),('提示16、予算20','within=16ms','この要求予算内に収まる。'),('入力10、提示30、予算20','within=20ms','境界を含む定義を確認する。')],
 [('CPUとGPUの時間を足せば遅延か。','並行動作する区間があるため単純には足せない。同じフレームの因果と待ちを追う。'),('二十ミリ秒をANRの閾値としてよいか。','よくない。この実習の提示予算であり、ANRの発生条件とは別。'),('比較試験で固定する条件は。','表示周期、負荷、操作、対象フレーム、端末の温度や電源条件をそろえる。')],
 '''
 def decide(x):
     duration = x['present_ms'] - x['input_ms']
     if duration < 0: return 'invalid_clock'
     return ('within=' if duration <= x['budget_ms'] else 'late=') + f'{duration}ms'
 ''',[
 ('late-after-fast-app',dict(app_ms=4,input_ms=0,present_ms=35,budget_ms=20),'late=35ms'),
 ('within',dict(app_ms=4,input_ms=0,present_ms=16,budget_ms=20),'within=16ms'),
 ('boundary',dict(app_ms=4,input_ms=10,present_ms=30,budget_ms=20),'within=20ms')])

add('audio','Focus、データ、経路、実音を別の証拠にする',
 'Focus取得とPCMの出力は確認できたが、車両のスピーカーから聞こえない。制御の成功を実音の成功へ読み替えない。',
 'この架空製品の再生条件はFocus、出力経路、ミュート解除、アンプ準備である。Android全用途の一律条件とはしない。',
 ['モデルは最初に不足する条件を返す。PCMがあってもミュートや経路の違いがあれば、音が出ない説明は成立する。制御状態、データ経路、ルーティング、物理出力を同じ一列の成功状態へ潰さない。',
  '全条件がそろってもaudibleではなくeligibleとする。実音はループバック、機器の観測、実測など要求に合う方法で確認する。AAOSではゾーン・ユーザー・製品ポリシーも結び付ける必要がある。'],
 [('Focusだけで成功表示','簡単だが実経路やミュートを見落とす。'),('条件と観測を分離','原因を説明しやすい。製品固有の情報と実測手段が必要。')],
 [('Focusあり、mute=true','blocked_mute','取得成功と実出力を区別する。'),('route=false','missing_route','送信先を確認する。'),('全条件true','eligible_not_audible_proof','実音の証拠は別に取る。')],
 [('Focus取得だけで実音を証明できるか。','できない。データ、経路、音量・ミュート、機器の条件を分ける。'),('PCMが非ゼロなら必ずスピーカーから出るか。','出力先やポリシー、アンプ等が別なので保証できない。'),('車載で追加すべき試験軸は。','対象ユーザーと音声ゾーン、電源、優先音や安全上の要求を製品条件として確認する。')],
 '''
 def decide(x):
     if not x['focus']: return 'focus_required'
     if not x['route']: return 'missing_route'
     if x['mute']: return 'blocked_mute'
     if not x['amp_ready']: return 'amp_not_ready'
     return 'eligible_not_audible_proof'
 ''',[
 ('muted',dict(focus=True,route=True,mute=True,amp_ready=True),'blocked_mute'),
 ('no-route',dict(focus=True,route=False,mute=False,amp_ready=True),'missing_route'),
 ('ready',dict(focus=True,route=True,mute=False,amp_ready=True),'eligible_not_audible_proof')])

add('network-security','接続中と、目的地へ届くことを分ける',
 '車内のローカル機器へ通信したいが、インターネット検証が失敗している。逆に接続中でも目的地へ到達できない場合がある。',
 'このモデルはリンク、経路、権限、用途別の検証を別に扱う。インターネットの検証結果をローカル通信の一律の許否にしない。',
 ['ローカル用途では外部の検証先へ出られなくても、対象への経路が存在することがある。接続中という一つのフラグから、名前解決・TLS・アプリの許可・目的地の応答まで推測しない。',
  '複数のNetworkがある場合は、どのネットワークで要求したかも記録する。モデルのeligibleは送信を試せる前提であり、到達や認証の成功ではない。実機では宛先・経路・名前解決・応答・証明書を段階ごとに照合する。'],
 [('connectedだけを見る','単純だが目的地と用途の違いを表せない。'),('用途と接続先を明示','ローカルと外部の失敗理由を分けられる。経路変更時の再評価が必要。')],
 [('local、検証false、経路あり','eligible','外部検証がなくても試行可能な例。'),('internet、検証false','internet_unvalidated','外部到達性の証拠が不足。'),('linkあり、経路なし','no_route','接続状態だけで到達を判断しない。')],
 [('INTERNET権限は経路の存在を保証するか。','しない。権限とネットワークの到達性は別。'),('ローカル用途で検証結果を無視すれば認証も不要か。','不要ではない。対象の同一性と通信の保護を別に設計する。'),('複数Networkの不具合報告に必要な情報は。','対象Network、インターフェース、宛先、経路、切替時刻、要求と応答を記録する。')],
 '''
 def decide(x):
     if not x['permission']: return 'permission_required'
     if not x['link']: return 'link_down'
     if not x['route']: return 'no_route'
     if x['purpose'] == 'internet' and not x['validated']: return 'internet_unvalidated'
     return 'eligible'
 ''',[
 ('local',dict(permission=True,link=True,route=True,purpose='local',validated=False),'eligible'),
 ('internet',dict(permission=True,link=True,route=True,purpose='internet',validated=False),'internet_unvalidated'),
 ('no-route',dict(permission=True,link=True,route=False,purpose='local',validated=True),'no_route')])

add('faults','消えたという症状から、終了原因を断定しない',
 '画面が消えた報告について、例外・ANR・メモリ圧迫による終了・原因不明を区別したい。',
 'モデルの入力は確認済みの証拠タグであり、生ログの自動診断ではない。証拠が不足すればunknownを返す。',
 ['同じ消失の症状でも、例外のスタック、ANRの記録、メモリ圧迫による終了の記録は異なる。再起動で直った事実は回復の観測であり、原因の特定ではない。',
  'PID・プロセス世代・時刻をそろえ、同じ障害に属する証拠だけを比較する。複数の原因候補や二次障害がある場合は、この小さな分類器のように一つのタグへ押し込めず、仮説と未確認事項を残す。'],
 [('症状名で分類','報告は簡単だが異なる原因を混同する。'),('証拠と仮説を分離','再現と調査を進めやすい。採取条件と欠損も記録する。')],
 [('確認済みexceptionタグ','crash_evidence','例外の証拠がある。'),('確認済みanrタグ','anr_evidence','待ちや停滞の原因は追加調査する。'),('画面消失だけ','unknown','証拠不足を原因の断定へ変えない。')],
 [('再起動で直れば原因も分かるか。','分からない。直った条件と原因の根拠を分ける。'),('ANRの一行だけで原因メソッドを決めるか。','決めない。対象時刻のスレッド、待ち先、負荷、前後の経路を確認する。'),('原因不明のまま残すべき情報は。','再現操作、ビルド、PIDと世代、時刻、採取できた証拠と欠損、次に検証する仮説。')],
 '''
 def decide(x):
     tags = set(x['verified_tags'])
     if len(tags & {'exception', 'anr', 'memory_kill'}) > 1: return 'needs_correlation'
     for tag, label in [('exception', 'crash_evidence'), ('anr', 'anr_evidence'), ('memory_kill', 'memory_kill_evidence')]:
         if tag in tags: return label
     return 'unknown'
 ''',[
 ('crash',dict(verified_tags=['exception']),'crash_evidence'),
 ('anr',dict(verified_tags=['anr']),'anr_evidence'),
 ('symptom-only',dict(verified_tags=[]),'unknown')])

add('build','変更したソースと、動いている成果物を結ぶ',
 'ビルドは成功したが実機の挙動が変わらない。ソース、製品設定、配置先、実行中イメージの取り違えを調べる。',
 'ビルドの成功だけで、対象製品への配置と採用を証明しない。期待する成果物識別子と実行中の識別子を照合する。',
 ['同じコミットでも製品やバリアント、設定が違えば別の成果物になる。ソースの変更箇所だけでなく、どの対象を作り、どこへ配置し、何を起動したかを記録する。',
  'モデルの識別子は説明用の文字列で、実際のハッシュや署名の検証はしていない。一致してもその変更が目的のコードパスで使われるかは、実行時ログや観測で確かめる。識別と動作の検証を二段階にする。'],
 [('ビルド成功だけで判定','早いが配置・製品違いを検出できない。'),('成果物と実機を対応づける','再現しやすい。ビルド・配置・起動の記録を保持する。')],
 [('期待製品と対象製品が違う','wrong_product','同じソースだけでは一致しない。'),('製品は同じ、成果物が旧版','wrong_artifact','配置と起動を追う。'),('識別子が一致','identity_match_not_behavior_proof','採用後のコードパスを検証する。')],
 [('ハッシュが一致すれば機能も正しいか。','一致は同じ成果物の根拠であり、要求通りの動作の証拠ではない。'),('プロパティ・Settings・overlayは同じ設定手段か。','役割と読込時点が違う。どの値を誰がいつ読むかを確認する。'),('再現用に残すビルド情報は。','ソース版、製品、バリアント、設定、成果物識別子、配置先、実機で採用された版。')],
 '''
 def decide(x):
     if x['expected_product'] != x['actual_product']: return 'wrong_product'
     if x['expected_artifact'] != x['running_artifact']: return 'wrong_artifact'
     return 'identity_match_not_behavior_proof'
 ''',[
 ('product',dict(expected_product='car',actual_product='phone',expected_artifact='v2',running_artifact='v2'),'wrong_product'),
 ('old-image',dict(expected_product='car',actual_product='car',expected_artifact='v2',running_artifact='v1'),'wrong_artifact'),
 ('matched',dict(expected_product='car',actual_product='car',expected_artifact='v2',running_artifact='v2'),'identity_match_not_behavior_proof')])

add('investigation','同じ要求番号でも、別の再現を混ぜない',
 'アプリ・サービス・実装のログを集めたが、古い起動のreq=41が紛れている。境界を越えた因果を正しく結びたい。',
 'モデルは起動世代と要求IDで絞る。時刻だけの近さや同じ文字列は、同じ要求の証拠として十分ではない。',
 ['同じreq=41でも起動世代が違うHALの成功を混ぜると、現在の不具合が成功に見える。相関キーをそろえた後、どの境界の観測が欠けているかを見る。',
  '実機では時計の種類と基準も照合する。ログがないことは処理されなかった証明ではなく、採取漏れや記録条件の可能性がある。計測点を追加する時は、個人情報・記録量・処理への影響を評価する。'],
 [('文字列検索だけで連結','手軽だが再起動や複数要求を混ぜやすい。'),('相関キーと時刻基準を記録','因果を追いやすい。各層に同じキーを渡す設計が必要。')],
 [('同世代のapp/service/hal','stages=app,service,hal','一つの要求の観測として並べる。'),('halだけ旧世代','stages=app,service','古い成功を除外する。'),('別IDしかない','stages=none','近い時刻でも同じ要求とはしない。')],
 [('ログが欠けたら未実行と断定するか。','しない。採取条件やログの有効化、バッファの欠損を確認する。'),('壁時計と単調時計を直接引いてよいか。','よくない。基準と対応関係を明示してから比較する。'),('調査用ログへ最低限何を入れるか。','機微情報を避け、要求ID、起動・接続世代、対象、境界、時計種別と結果を記録する。')],
 '''
 def decide(x):
     selected = [e['stage'] for e in x['events'] if e['boot'] == x['boot'] and e['req'] == x['req']]
     return 'stages=' + (','.join(selected) if selected else 'none')
 ''',[
 ('complete',dict(boot='b2',req=41,events=[dict(boot='b2',req=41,stage=s) for s in ['app','service','hal']]),'stages=app,service,hal'),
 ('old-hal',dict(boot='b2',req=41,events=[dict(boot='b2',req=41,stage='app'),dict(boot='b2',req=41,stage='service'),dict(boot='b1',req=41,stage='hal')]),'stages=app,service'),
 ('other',dict(boot='b2',req=41,events=[dict(boot='b2',req=42,stage='hal')]),'stages=none')])

add('automotive','車両・ユーザー・Androidの状態を直積で考える',
 '車両が起動しても対象ユーザーは未準備で、復帰後の機器も未接続だった。単一のreadyフラグを分解したい。',
 '架空製品の利用条件を、車両電源・ユーザー準備・機器接続の独立した入力として評価する。走行時の操作制限は別の条件である。',
 ['車両の電源イベントからアプリのデータ利用や機器の準備まで一括して推測しない。ユーザー切替、休止からの復帰、通信の再接続は異なる時点で進むことがある。',
  '全条件がそろっても安全上の許可を証明したわけではない。実車の要件、優先機能、操作制限、故障時の安全側出力を別に確認する。モデルは製品内の利用ゲートの例でありAAOS全機能の規則ではない。'],
 [('単一readyフラグ','利用側は簡単だが原因と復帰待ちを説明しにくい。'),('独立した状態軸','不足条件と試験を対応づけられる。組合せと遷移を管理する。')],
 [('車両ON、ユーザー未準備','wait_user','電源とデータ利用を分ける。'),('ユーザー準備済み、機器未接続','wait_device','復帰後の再接続を待つ。'),('全条件を満たす','eligible_not_safety_proof','安全上の要件は別に検証する。')],
 [('車両電源ONを、全ユーザーの解錠と同一視できるか。','できない。対象ユーザーの状態と利用するデータの条件を確認する。'),('復帰直後に前回の機器値を表示するなら何を添えるか。','前回値であることと鮮度を示し、新しい観測値が得られるまでは未確認として扱う。'),('走行中の操作制限をUIの気分で緩めてよいか。','よくない。製品の要件とプラットフォームの制限を確認し、安全上の判断は関係者と検証する。')],
 '''
 def decide(x):
     if not x['vehicle_on']: return 'wait_power'
     if not x['user_ready']: return 'wait_user'
     if not x['device_ready']: return 'wait_device'
     return 'eligible_not_safety_proof'
 ''',[
 ('user',dict(vehicle_on=True,user_ready=False,device_ready=True),'wait_user'),
 ('device',dict(vehicle_on=True,user_ready=True,device_ready=False),'wait_device'),
 ('ready',dict(vehicle_on=True,user_ready=True,device_ready=True),'eligible_not_safety_proof')])

add('walkthrough','画面操作から音の観測まで、一つの要求で追う',
 '再生操作の直後に画面を離れ、前の要求の成功通知が戻った。画面の表示と処理の寿命を整合させたい。',
 '再生要求の世代と現在の表示対象を照合する。取消済み要求を成功へ戻さず、制御の受付と実音の観測を分ける。',
 ['一日を追う横断例では、各層の正常応答を並べるだけでは競合を説明できない。ユーザーが離れた時点、取消の受付、古い結果の到着を同じ時間軸で追い、どの状態を誰が更新できるかを決める。',
  '取消は外部処理の完全な停止を意味するとは限らない。古い結果のUIへの反映は防ぎつつ、バックグラウンド再生を続ける機能なら画面とは別の所有者へ寿命を移す。モデルは画面内だけで完結する再生要求の例に限定する。'],
 [('画面離脱で要求を破棄','画面内の操作では単純。バックグラウンド再生にはそのまま使えない。'),('別の所有者へ処理を移す','長い再生を継続できる。UIの再接続と状態観測の責任が増える。')],
 [('旧世代から成功','ignore_stale','現在の表示を戻さない。'),('現世代だが取消済み','ignore_cancelled','取消後の結果の扱いを決める。'),('有効な要求の観測','show_observed','実測として渡された結果を表示する。')],
 [('画面を離れたらすべて停止すべきか。','用途による。画面に属する処理と、再生等の長い寿命を持つ処理を分ける。'),('取消通知を送れば結果の検査は不要か。','不要ではない。すでに進行した処理や配送済みの通知は戻る場合がある。'),('横断ログで最初にそろえるものは。','要求IDと世代、時計の基準、対象のプロセス・経路・ユーザーをそろえる。')],
 '''
 def decide(x):
     if x['result_generation'] != x['generation']: return 'ignore_stale'
     if x['cancelled']: return 'ignore_cancelled'
     return 'show_observed'
 ''',[
 ('old',dict(generation=2,result_generation=1,cancelled=False),'ignore_stale'),
 ('cancelled',dict(generation=2,result_generation=2,cancelled=True),'ignore_cancelled'),
 ('current',dict(generation=2,result_generation=2,cancelled=False),'show_observed')])

add('first-app','同じ画面に見えても、同じインスタンスではない',
 '回転とプロセス再起動のログを比べる。画面が作り直されたことを、アプリ全体の起動と取り違えない。',
 'PIDだけでなくプロセスの起動世代と画面の識別子を使う。このモデルは観測済みの識別子を分類するだけで、コールバック列を再現しない。',
 ['新しい画面IDと同じプロセス世代の組合せは、画面再作成の証拠になる。プロセス世代まで変わっていれば、以前のメモリを前提にできない。同じPIDが将来再利用される可能性にも注意する。',
  '実機ではライフサイクルのコールバックと保存・復元元を記録する。onDestroyの欠落だけで異常と決めず、OSによる終了を含む条件を分ける。モデルは例の二時点を比較するもので、原因を自動判定するものではない。'],
 [('画面IDだけを記録','画面の作り直しは見えるが、プロセスの寿命は区別できない。'),('プロセス世代も記録','メモリの連続性を調べやすい。IDの発行とログ基準をそろえる。')],
 [('同世代、新画面ID','activity_recreated','プロセスは連続している。'),('新世代、新画面ID','process_restarted','メモリの連続性を失う。'),('両方同じ','same_instance','この二時点では同じ対象。')],
 [('onCreateの回数だけでアプリ起動回数が分かるか。','分からない。画面再作成や複数Activityを含むため、プロセスの識別と分ける。'),('PIDが同じなら永遠に同じプロセスか。','違う。再利用を考慮し、起動世代や開始時刻も用いる。'),('最小アプリで追加すべき再現操作は。','回転、背面化、復帰、プロセス終了後の起動、権限変更を別々に観測する。')],
 '''
 def decide(x):
     if x['before_process'] != x['after_process']: return 'process_restarted'
     if x['before_activity'] != x['after_activity']: return 'activity_recreated'
     return 'same_instance'
 ''',[
 ('rotation',dict(before_process='p1',after_process='p1',before_activity='a1',after_activity='a2'),'activity_recreated'),
 ('restart',dict(before_process='p1',after_process='p2',before_activity='a1',after_activity='a2'),'process_restarted'),
 ('resume',dict(before_process='p1',after_process='p1',before_activity='a1',after_activity='a1'),'same_instance')])

add('app-design','遅い検索結果が、新しい検索を上書きしない設計',
 '検索Aの後に検索Bを開始し、B、Aの順に結果が戻る。取消が間に合わなくても古い結果を表示しない。',
 '結果へ要求世代を付け、現在の世代だけで表示状態を更新する。モデルは単一スレッドの状態更新へ限定する。',
 ['非同期化しただけでは結果順は開始順にならない。キャンセルの伝達と、受信結果を現在の画面へ反映してよいかの判定は別である。最新要求の識別子を保持し、古い結果を受け取っても状態を戻さない。',
  '実装ではFlowの演算子の意味、収集の寿命、ViewModelの所有者を確認する。状態更新の入口をまとめれば、読み込み中・成功・失敗の遷移を再現できる。モデルの選別がネットワークやコルーチンの取消成功を証明するわけではない。'],
 [('取消だけに依存','無駄な処理を減らせるが、取消不能や到着済みの結果が残る場合がある。'),('世代を照合して反映','表示の巻戻りを防ぎやすい。要求発行と受信を同じ規則へ集約する。')],
 [('現在2、結果は2→1','shown=B','古いAは上書きできない。'),('現在2、旧結果1だけ','shown=loading','未完了の新しい要求を成功扱いにしない。'),('現在2、結果2','shown=B','有効な結果だけを採用する。')],
 [('collectを画面の寿命へ合わせる理由は。','不要な観測や更新を続けないため。処理自体の寿命と観測の寿命は別に設計する。'),('最新結果を守る最小のテストは。','Aを開始、Bを開始、Bの結果、Aの結果という順を入力し、最終表示がBのままか確かめる。'),('失敗も世代照合するか。','する。古い要求の失敗で新しい成功をエラー表示へ戻さない。')],
 '''
 def decide(x):
     shown = 'loading'
     for generation, value in x['results']:
         if generation == x['current']: shown = value
     return 'shown=' + shown
 ''',[
 ('out-of-order',dict(current=2,results=[(2,'B'),(1,'A')]),'shown=B'),
 ('only-old',dict(current=2,results=[(1,'A')]),'shown=loading'),
 ('current',dict(current=2,results=[(2,'B')]),'shown=B')])

add('data-practice','応答を失った再送と、二重登録を分ける',
 '保存要求はサーバーへ届いたが、応答だけ失われた。同じ操作を再送して二重の注文を作らないようにしたい。',
 '同じ操作IDと同じ内容の再送は同じ記録へ対応させる。同じIDで別の内容が来た場合は拒否する。',
 ['ローカル保存済み、送信中、サーバー確認済みを別に表す。応答のタイムアウトだけではサーバーが未処理とは断定できない。モデルは受信側の識別表を使い、同じ内容の再送を新規作成へしない。',
  'この辞書はメモリ内だけのモデルである。実用では記録の永続性、操作IDの期限、並行要求、内容の照合、権限を含めた原子的な受付が必要になる。クライアントのフラグだけで外部の一度だけの実行を保証しない。'],
 [('再送ごとに新しいID','簡単だが、応答喪失で二重作成しやすい。'),('操作IDを再利用','同じ操作を照合できる。保存先の原子性と内容一致の契約が必要。')],
 [('同じID・同じ内容','replayed','前回の結果へ対応づける。'),('同じID・別内容','conflict','識別子の誤用を検出する。'),('新しいID','created','新規の操作として受け付ける。')],
 [('ローカルに保存したらサーバー反映済みか。','違う。各保存先と同期の状態を分ける。'),('操作IDの確認と挿入が別々だと何が起きるか。','同時要求が両方未登録と判断する可能性がある。受付を原子的にし、重複制約等を検討する。'),('権限が取り消された後の再送は。','操作の識別と認可を別に確認する。過去に通ったことを現在の権限の証拠にしない。')],
 '''
 def decide(x):
     records = x['records']
     key = x['id']
     if key in records:
         return 'replayed' if records[key] == x['payload'] else 'conflict'
     return 'created'
 ''',[
 ('retry',dict(records={'op1':'A'},id='op1',payload='A'),'replayed'),
 ('mismatch',dict(records={'op1':'A'},id='op1',payload='B'),'conflict'),
 ('new',dict(records={'op1':'A'},id='op2',payload='A'),'created')])

add('binder-practice','再接続は、新しいセッションの開始である',
 'サービス死亡後に接続し直したが、以前の接続の通知と保留要求が残る。再接続の状態遷移を検証する。',
 '死亡時に世代を更新し、保留要求を結果不明へ移す。新しい接続の結果だけを現在の成功として受け入れる。',
 ['再bindが成功しても、前の要求が失敗したのか処理済みなのかまでは分からない。接続を取り直す処理と、業務要求を再送してよいかの判断を分ける。',
  'モデルはdead、connect、resultを順に受ける。実機ではデス通知、unbindの所有、コールバック解除、プロセス死亡のタイミングを確認する。再送するなら同一操作の識別と重複副作用を別に設計する。'],
 [('接続し直して直ちに再送','復帰が早いが、結果不明の操作を重複させる可能性がある。'),('接続と要求の回復を分ける','不明な結果を照会できる。状態と回復手順が増える。')],
 [('死亡後に旧世代の結果','result=ignored','旧セッションへ戻らない。'),('新接続後に現世代の結果','result=accepted','接続条件と世代を照合する。'),('未接続で結果','result=ignored','配送済みの古い通知として扱う例。')],
 [('bind成功で前の要求の成否が分かるか。','分からない。以前の処理と新しい接続を別の状態として扱う。'),('画面ごとに無制限に再bindすると何が難しいか。','接続・購読・再試行の所有が散り、解放や重複通知を追いにくい。所有範囲を定める。'),('障害注入で試す時点は。','受付前、受付後、結果送信前、再接続中、旧コールバック到着の各時点を分ける。')],
 '''
 def decide(x):
     generation, connected, result = 1, True, 'none'
     for event in x['events']:
         if event[0] == 'dead': generation += 1; connected = False
         elif event[0] == 'connect': connected = True
         elif event[0] == 'result':
             result = 'accepted' if connected and event[1] == generation else 'ignored'
     return 'result=' + result
 ''',[
 ('old',dict(events=[('dead',),('connect',),('result',1)]),'result=ignored'),
 ('new',dict(events=[('dead',),('connect',),('result',2)]),'result=accepted'),
 ('disconnected',dict(events=[('dead',),('result',2)]),'result=ignored')])

add('aaos-detail','ユーザー切替で、前の人の通知を残さない',
 'ユーザー切替中に前のユーザーの結果が戻り、別ゾーンの画面へ反映される。ユーザー・接続世代・ゾーンを対応づけたい。',
 'この架空製品ではユーザーID、セッション世代、音声ゾーンが一致する通知だけを反映する。操作制限の許否は別に評価する。',
 ['電源や接続が続いていても、ユーザーが変わればデータと権限の前提が変わる。ユーザーIDだけが同じ場合も、新しいセッションへ古い結果を混ぜないよう世代を確認する。',
  'ゾーンやルーティングは製品固有の構成へ依存する。モデルの選別は情報の取違えを検証するもので、実AAOSのポリシーや安全要件を再現しない。実機では切替前後の購読解除、未完了要求、許可と出力先を確認する。'],
 [('ユーザーIDだけを見る','簡単だが再接続やゾーンの違いを落とす。'),('文脈を組として保持','取違えを検出しやすい。切替時の所有と解放を明示する。')],
 [('ユーザーが違う','ignore_context','前の人の状態を反映しない。'),('同ユーザーで旧世代','ignore_context','セッションを区別する。'),('全項目一致','accept_context','他の利用条件は別に確認する。')],
 [('ユーザー切替とアプリ画面の切替は同じか。','同じではない。データ・権限・機器やサービスの所有を製品の構成で確認する。'),('ゾーン一致で安全な音量を保証できるか。','できない。出力経路、優先音、音量制限、機器条件を別に検証する。'),('切替中の受入テストを一つ作る。','切替前の要求を保留し、切替完了後に結果を返す。新ユーザーのUIへ反映されないことを確認する。')],
 '''
 def decide(x):
     return 'accept_context' if tuple(x['current']) == tuple(x['callback']) else 'ignore_context'
 ''',[
 ('old-user',dict(current=[11,2,0],callback=[10,2,0]),'ignore_context'),
 ('old-session',dict(current=[11,2,0],callback=[11,1,0]),'ignore_context'),
 ('match',dict(current=[11,2,0],callback=[11,2,0]),'accept_context')])

add('test-lab','平均だけでは、遅い操作を隠してしまう',
 'ほとんどの操作は速いが、一部だけ大きく遅れる。平均、p95、最大値を同じ意味で使わずに比較したい。',
 '分位点はnearest-rank方式、百分位は1〜100の整数とする。標本数、分布、ウォームアップ、再現条件を併記し、p95だけで品質を断定しない。',
 ['一から十九と百の二十標本では、p95は十九、最大は百になる。p95が良くても極端な遅れがないとは言えない。どの分位点を使うかは、問題となる操作と要求から決める。',
  '標本数が少ないと上位分位点は少数の値に左右される。測定の準備や端末状態をそろえ、改善前後の同じ分布を比較する。モデルの統計計算は、Perfetto等で正しく計測できたことの証明にはならない。'],
 [('平均だけを報告','全体傾向は見えるが、尾の遅れを隠しやすい。'),('分位点と最大・標本数を報告','分布の違いを説明しやすい。計算方式と測定条件を固定する。')],
 [('20標本、p95','rank=19 value=19','ceil(0.95×20)の位置を使う。'),('同じ標本、p99','rank=20 value=100','尾の大きな値が表れる。'),('空の標本','no_samples','不足をゼロミリ秒へ変えない。')],
 [('p95の方式を記さないと何が起きるか。','補間等の方式によって値が変わり、比較を誤る可能性がある。'),('測定前のウォームアップを無視してよいか。','目的次第で分ける。コールドとウォームを混ぜず、製品で重要な条件を明記する。'),('改善の受入条件へ何を含めるか。','標本数、端末・負荷・温度等の条件、中央値や尾の分位点、最大と失敗率を要求に合わせて定める。')],
 '''
 def decide(x):
     samples = sorted(x['samples'])
     if not samples: return 'no_samples'
     percentile = x['percentile']
     if not isinstance(percentile, int) or not 1 <= percentile <= 100: return 'invalid_percentile'
     rank = (percentile * len(samples) + 99) // 100
     return f'rank={rank} value={samples[rank - 1]}'
 ''',[
 ('p95',dict(samples=list(range(1,20))+[100],percentile=95),'rank=19 value=19'),
 ('p99',dict(samples=list(range(1,20))+[100],percentile=99),'rank=20 value=100'),
 ('empty',dict(samples=[],percentile=95),'no_samples')])

add('os-integration','宣言の整合と、実装の互換性試験を分ける',
 'HALの版を更新したが、製品側の要求と提供する契約が一致しない。ビルド成功だけで互換と判定しない。',
 'モデルは架空のrequired/providedという契約集合の包含だけを検査する。実際のVINTFの書式・版規則やCTS/VTSを代行しない。',
 ['要求した契約が提供されていなければ、まず構成と版の整合を直す。一方、集合が一致してもメソッドの意味、エラー、性能、起動や更新を通した動作は未検証である。',
  'インターフェース、manifest、互換性の宣言、実装、配置先と起動した成果物を対応づける。公開された互換性試験と製品の要求試験を別の証拠として残す。簡略な比較器の合格をプラットフォームの認証へ読み替えない。'],
 [('ビルド成功のみ','構文や依存の一部は確認できるが、実行時の提供契約は保証しない。'),('宣言と実行の両方を試験','不足と振る舞いを分けて説明できる。対象版と製品条件の記録が必要。')],
 [('要求control-v2、提供v1のみ','missing=control-v2','宣言の不足を検出する。'),('要求と提供が一致','declarations_match_only','実装の挙動は別に検証する。'),('未要求の追加契約あり','declarations_match_only','追加だけで要求を失ったとはしない。')],
 [('この集合比較でVINTF互換を証明できるか。','できない。実際の書式・版と互換性規則、対象製品での試験が必要。'),('互換性試験と製品の受入試験は同じか。','異なる。プラットフォーム契約と、製品固有の利用条件・性能・故障時の振る舞いを分ける。'),('更新後に必要な確認は。','起動した版、契約の提供、クライアントとの疎通、異常・再接続、更新と復旧の経路を確認する。')],
 '''
 def decide(x):
     missing = sorted(set(x['required']) - set(x['provided']))
     return 'missing=' + ','.join(missing) if missing else 'declarations_match_only'
 ''',[
 ('missing',dict(required=['control-v2'],provided=['control-v1']),'missing=control-v2'),
 ('match',dict(required=['control-v2'],provided=['control-v2']),'declarations_match_only'),
 ('extra',dict(required=['control-v2'],provided=['control-v2','status-v1']),'declarations_match_only')])

add('capstone','期限超過を失敗と断定すると、二重操作になる',
 '機器の値変更がタイムアウトした。相手では反映済みかもしれないため、単純な再送でよいかを設計レビューする。',
 '要求中、観測一致、期限超過で結果不明、明示的失敗を分ける。モデルの時刻は同じ単調時計上の値とする。',
 ['期限を越えたことは待ちを打ち切る根拠にはなるが、相手が未実行である証拠にはならない。要求IDで状態を照会するか、再送を冪等にする案を比較する。',
  'ここでは一致の観測があれば完了、明示的な失敗があれば失敗、それ以外の期限超過はunknownとする。実機では観測の鮮度、接続世代、取消、再起動と外部副作用を含め、受入条件と期待ログを先に書く。'],
 [('期限超過で即再送','復帰しやすいが、相手で実行済みなら二重操作の危険がある。'),('照会と操作IDを併用','不明な結果を扱える。状態保持と再試行の仕様が増える。')],
 [('期限超過、観測なし','unknown','失敗と未確認を区別する。'),('一致する観測あり','confirmed','この観測に対する一致がある。'),('明示的失敗','failed','エラーの出典を残す。')],
 [('unknownをfailedへまとめると何が困るか。','未実行と実行済みの両方を同じ再送へ流し、重複副作用を起こす可能性がある。'),('状態図とテスト表を対応づけるには。','各遷移に入力、前提、更新する状態、禁止する副作用、期待する証拠を一組で書く。'),('設計案に唯一の正解はあるか。','要求する保証、故障範囲、運用できる複雑さによる。選ばなかった案の理由も説明する。')],
 '''
 def decide(x):
     if x['observed_match']: return 'confirmed'
     if x['explicit_error']: return 'failed'
     return 'unknown' if x['now'] >= x['deadline'] else 'pending'
 ''',[
 ('timeout',dict(observed_match=False,explicit_error=False,now=100,deadline=100),'unknown'),
 ('observed',dict(observed_match=True,explicit_error=False,now=101,deadline=100),'confirmed'),
 ('error',dict(observed_match=False,explicit_error=True,now=50,deadline=100),'failed')])

add('ethernet','複数の経路では、最長一致が送信先を変える',
 'Ethernetリンクは上がっているが、意図しないインターフェースへ送られる。宛先と経路表を結び付けて調べる。',
 'モデルはIPv4の最長プレフィックス一致だけを表す。同じ長さの優先度、ポリシールーティング、ARPや実機の送信成功は省略する。',
 ['宛先が同じでも、より具体的な経路があればデフォルト経路より優先される。リンクアップの表示だけでは、選ばれた経路や次の機器へ届いたことを説明できない。',
  '実機ではインターフェース、VLAN、IPとマスク、経路、近隣解決、対象ポートの応答を段階で確認する。計測のために設定を無断で変えるのでなく、まず対象と現状を記録してから仮説を検証する。'],
 [('リンク状態だけを見る','物理接続の入口は見えるが、宛先の経路は分からない。'),('宛先ごとの経路を照合','誤経路を説明できる。複数Networkと製品のポリシーを確認する。')],
 [('10.1.2.3へ/24と/0がある','route=eth1','より具体的な/24を選ぶ。'),('外部宛先、/0がある','route=eth0','デフォルト経路に一致する。'),('一致経路なし','no_route','リンクだけでは到達できない。')],
 [('最長一致で到達も保証できるか。','できない。次ホップ、近隣解決、相手や認証などを別に確認する。'),('同じ長さの経路が複数ならこのモデルで足りるか。','足りない。メトリックやポリシー等、対象環境の選択規則が必要。'),('パケット採取の前に固定する条件は。','対象インターフェース、宛先、プロトコル、時刻、再現操作と採取範囲をそろえる。')],
 '''
 def decide(x):
     import ipaddress
     destination = ipaddress.ip_address(x['destination'])
     choices = [(ipaddress.ip_network(net), name) for net, name in x['routes']]
     matching = [(net, name) for net, name in choices if destination in net]
     return 'route=' + max(matching, key=lambda item: item[0].prefixlen)[1] if matching else 'no_route'
 ''',[
 ('specific',dict(destination='10.1.2.3',routes=[('0.0.0.0/0','eth0'),('10.1.2.0/24','eth1')]),'route=eth1'),
 ('default',dict(destination='192.0.2.1',routes=[('0.0.0.0/0','eth0'),('10.1.2.0/24','eth1')]),'route=eth0'),
 ('missing',dict(destination='192.0.2.1',routes=[('10.1.2.0/24','eth1')]),'no_route')])

add('microphone','サンプル、フレーム、バイトを混同しない',
 'ステレオ録音の短い読み取りをつなぐと、保存した時間が倍になった。読み取った要素数とフレーム数を分けたい。',
 'このモデルはshort要素数を入力し、2チャンネルの一組を1フレームとする。未完の要素は次回へ持ち越し、ゼロは終端と断定しない。',
 ['shortの読み取り数をそのままフレーム数として数えると、ステレオでは二倍の時間になる。バッファの要求サイズと実際に返った数も区別し、戻った範囲だけを処理する。',
  '録音権限や初期化成功はデータの継続性の証拠ではない。短い読み取り、ゼロ、エラー、機器切替、取消を試す。モデルは数の整合だけを検証し、AudioRecordの実行や実音の取得は実機で確認する。'],
 [('要求サイズで処理','実装は短いが未取得範囲や時間を誤って扱う。'),('実際の戻り値を処理','短い取得へ対応できる。単位と端数、エラー後の復帰を定義する。')],
 [('6と2要素、2ch','frames=4 remainder=0','8要素を4フレームへ換算。'),('3要素、2ch','frames=1 remainder=1','未完のチャンネル組を持ち越す。'),('ゼロ要素','frames=0 remainder=0','このモデルでは終端と扱わない。')],
 [('16bitステレオで一フレームは何バイトか。','二チャンネル×二バイトで四バイト。サンプルレートは通常フレーム数の時間基準になる。'),('負の戻り値をサイズへ変換してよいか。','よくない。APIのエラー契約を先に判定し、継続・再作成・停止を決める。'),('取消と解放の試験で見る点は。','読み取りループの停止、機器やAudioRecordの解放、古い結果の反映、再開始の可否を確認する。')],
 '''
 def decide(x):
     total = 0
     for count in x['short_counts']:
         if count < 0: return 'read_error'
         total += count
     frames, remainder = divmod(total, x['channels'])
     return f'frames={frames} remainder={remainder}'
 ''',[
 ('short-reads',dict(short_counts=[6,2,0],channels=2),'frames=4 remainder=0'),
 ('partial-frame',dict(short_counts=[3],channels=2),'frames=1 remainder=1'),
 ('zero',dict(short_counts=[0],channels=2),'frames=0 remainder=0')])

add('hardware-control','値が近くても、古い通知なら完了ではない',
 '明るさの制御に許容差を追加した。前の要求の値がたまたま近くても、今の要求を完了扱いにしないようにする。',
 '要求IDと接続世代を照合した後で値の許容差を評価する。許容差は機能の要求として定義する。',
 ['許容差の判定だけを先に行うと、古い通知が現在の完了へ見える。何を操作したか、どの接続の結果か、値と時刻は何かを一組で確認してから一致を判定する。',
  '制御APIの返却、機器の読戻し、実際の物理量は異なる証拠になり得る。どこまでを反映完了と呼ぶか決め、未反映・期限超過・故障を別々に表す。モデルは同じ単位の整数の比較に限定する。'],
 [('値だけを照合','簡単だが古い通知や別要求を混ぜる。'),('識別子と許容差を照合','境界と非同期を扱いやすい。通知の鮮度と期限も必要になる。')],
 [('要求24、実測23、許容1','within_tolerance','境界を含めて判定する。'),('値24でも旧世代','stale','値一致を優先しない。'),('実測21、許容1','not_applied','許容差外として残す。')],
 [('許容差は実装者が勝手に決めてよいか。','要求・機器の精度・安全上の条件を根拠に決める。単にテストを通すために広げない。'),('表示値と機器値の単位が違う場合は。','変換、丸め、範囲と計測点を明示する。比較前に同じ意味の値へそろえる。'),('通知が来ない場合の復旧案は。','要求IDで照会し、不明と失敗を分ける。再送は冪等性と二重操作を検討してから行う。')],
 '''
 def decide(x):
     if (x['request_id'], x['generation']) != (x['event_id'], x['event_generation']): return 'stale'
     return 'within_tolerance' if abs(x['target'] - x['observed']) <= x['tolerance'] else 'not_applied'
 ''',[
 ('boundary',dict(request_id=4,generation=2,event_id=4,event_generation=2,target=24,observed=23,tolerance=1),'within_tolerance'),
 ('old',dict(request_id=4,generation=2,event_id=4,event_generation=1,target=24,observed=24,tolerance=1),'stale'),
 ('outside',dict(request_id=4,generation=2,event_id=4,event_generation=2,target=24,observed=21,tolerance=1),'not_applied')])

add('adb-detail','device表示は、アプリの準備完了ではない',
 'adb devicesではdeviceだが、対象アプリのデータやサービスが利用できない。接続、認証、システム準備を分ける。',
 'シリアル番号を固定し、unauthorized・offline・deviceを別に扱う。deviceは対象アプリやユーザーの準備を保証しない。',
 ['複数台を接続したまま対象を省略すると、採取したログと試した実機がずれる。まずシリアルを選び、認証とトランスポートの状態を確認する。認証を回避する手順へ流さない。',
  '接続後は端末の起動、対象ユーザー、アプリやサービスの状態を別の観測で確かめる。モデルはゲートの順序だけを表し、ADBサーバーやUSBの実装を再現しない。調査のための操作も、データを変更するか確認してから選ぶ。'],
 [('deviceだけで正常扱い','接続の入口は分かるがアプリの条件を見落とす。'),('対象と状態を段階で確認','誤採取を減らせる。シリアルと各観測の時刻を記録する。')],
 [('unauthorized','authorize_on_device','正規の端末確認を行う。'),('offline','transport_unavailable','接続とサーバー等の状態を調べる。'),('device、アプリ未準備','wait_app','トランスポートとアプリを分ける。')],
 [('複数台で対象を固定する方法は。','adb -s SERIALで対象を明示し、ログとビルド情報にも同じ端末識別を残す。'),('認証待ちを解決するため、確認を回避してよいか。','よくない。端末側の正規の確認と接続環境を調べる。'),('deviceならユーザーデータも読めるか。','保証しない。対象ユーザー、解錠、アプリの権限や実行条件を確認する。')],
 '''
 def decide(x):
     if x['transport'] == 'unauthorized': return 'authorize_on_device'
     if x['transport'] != 'device': return 'transport_unavailable'
     return 'eligible' if x['app_ready'] else 'wait_app'
 ''',[
 ('auth',dict(transport='unauthorized',app_ready=False),'authorize_on_device'),
 ('offline',dict(transport='offline',app_ready=False),'transport_unavailable'),
 ('booting',dict(transport='device',app_ready=False),'wait_app')])

add('bugreport-detail','採取された証拠と、障害の時刻を結ぶ',
 'bugreportに同じPIDの記録が複数あり、別の起動の障害を混ぜている。再現と採取の関係を保って読む。',
 'モデルはboot識別とPIDで対象を絞る。壁時計・単調時計の値や、PIDだけでは別起動の同一性を保証しない。',
 ['bugreportは複数の時点やサブシステムの情報を含む。採取時に正常だから障害時も正常だったとは言えない。再現操作、発生時刻、採取の遅延と欠損を明記して、同じ障害へ属する記録を集める。',
  '共有前には個人情報や認証情報を扱う手順を確認する。簡単な置換だけで完全な匿名化を保証しない。モデルの抽出は正規化済みの架空記録であり、実際のbugreportの全形式を解析するものではない。'],
 [('PIDと文字列だけで検索','入口には便利だが再起動や再利用を混ぜやすい。'),('再現時刻と起動情報も照合','対象を限定しやすい。時計基準と採取遅延を記録する。')],
 [('boot=b2、pid=42の記録','records=1','別起動の同PIDは含めない。'),('boot=b1、pid=42の記録','records=1','別の再現として扱う。'),('一致しない対象','records=0','不足を成功や未発生と断定しない。')],
 [('採取時に正常なら不具合なしと言えるか。','言えない。障害時の状態と採取時の状態を分ける。'),('壁時計が補正された前後をどう比べるか。','単調時計との対応や記録の基準を確認し、直接の差分へ意味を持たせない。'),('第三者へ送る前の確認は。','収集・共有の許可、個人情報・認証情報、機密な構成やログの範囲、保管先と期限を確認する。')],
 '''
 def decide(x):
     selected = [e for e in x['records'] if e['boot'] == x['boot'] and e['pid'] == x['pid']]
     return f'records={len(selected)}'
 ''',[
 ('current',dict(boot='b2',pid=42,records=[dict(boot='b1',pid=42),dict(boot='b2',pid=42)]),'records=1'),
 ('previous',dict(boot='b1',pid=42,records=[dict(boot='b1',pid=42),dict(boot='b2',pid=42)]),'records=1'),
 ('missing',dict(boot='b3',pid=42,records=[dict(boot='b2',pid=42)]),'records=0')])

add('partition-detail','書込み完了と、次回起動への採用を分ける',
 '別スロットへ更新を書いた途中で電源が切れた。未検証のスロットを次回起動へ採用しない設計を考える。',
 'この架空の二スロットモデルは、書込みと検証の両方が完了した候補だけを選ぶ。Androidの実際の更新プロトコルやAVBを代行しない。',
 ['ダウンロード完了、書込み完了、検証、起動候補への切替、初回起動の成功確認は異なる段階である。途中終了時に前の起動可能な版を残せるかを、各段階で試す。',
  '実機ではA/BやVirtual A/B等の構成、動的パーティション、検証・ロールバック、マージや電源断を対象製品で確認する。モデルの候補選択が、実ストレージの原子性や復旧可能性を保証するわけではない。'],
 [('上書きして即採用','容量を抑えられる場合があるが、途中終了の復旧が難しい。'),('検証済み候補を切り替える','前の版を残す設計が可能。メタデータと初回起動の確定が重要。')],
 [('書込み途中','boot=A','旧版を選ぶモデル。'),('書込み済み・未検証','boot=A','完了の段階を混同しない。'),('書込み・検証完了','boot=B','このモデルの候補条件を満たす。')],
 [('検証成功後に起動できなければ。','初回起動の確認とロールバック方針を別に設計する。検証だけで全機能を保証しない。'),('スロット名を決め打ちしてよいか。','実際の製品構成と更新方式を確認する。架空モデルのA/Bを全端末へ当てはめない。'),('電源断試験をどこへ入れるか。','ダウンロード、書込み、検証、メタデータ更新、初回起動、構成に応じたマージ等の境界を分ける。')],
 '''
 def decide(x):
     if x['written'] and x['verified']: return 'boot=' + x['candidate']
     return 'boot=' + x['active']
 ''',[
 ('interrupted',dict(written=False,verified=False,active='A',candidate='B'),'boot=A'),
 ('unverified',dict(written=True,verified=False,active='A',candidate='B'),'boot=A'),
 ('candidate',dict(written=True,verified=True,active='A',candidate='B'),'boot=B')])

def code_for(workbook):
    import pprint
    cases=pprint.pformat(workbook['cases'],width=88,sort_dicts=False)
    return workbook['model']+'\n\ncases = '+cases+'''\nfor name, inputs, expected in cases:
    actual = decide(inputs)
    assert actual == expected, (name, actual, expected)
    print(f"{name}: {actual}")
'''

def output_for(workbook):
    return '\n'.join(f'{name}: {expected}' for name,_,expected in workbook['cases'])

assert len(WORKBOOKS)==30
