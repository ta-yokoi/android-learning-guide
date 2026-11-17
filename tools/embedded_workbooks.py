"""Embedded design cases and portable C11 host experiments; no peripheral access."""
from textwrap import dedent
WORKBOOKS={}
HEADER='''#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <limits.h>
'''
def add(key,title,request,contract,reading,alternatives,evidence,questions,program,output):
    assert len(reading)==len(alternatives)==2 and len(evidence)==len(questions)==3
    WORKBOOKS[key]=dict(id=key,title=title,request=request,contract=contract,reading=reading,alternatives=alternatives,
        evidence=evidence,questions=questions,program=dedent(program).strip(),output='\n'.join(line.strip() for line in output.strip().splitlines()),language='c')

add('overview','平均処理時間では、期限を守る根拠にならない',
 '入力から出力まで五ミリ秒以内に完了したい。処理本体以外の待ちと割込みの影響も予算へ含める。',
 'モデルは同じ経路上の直列区間の上限を加算する。並行区間を重複加算せず、見積り値は対象機で検証する。',
 ['計算本体が一ミリ秒でも、入力待ち、ブロッキング、割込み、出力反映が残る。平均の速さを根拠にすると、まれな待ちによる期限違反を見落とす。境界ごとに上限と計測点を決める。',
  '実習は予算表の算術を検査するだけである。キャッシュ、バス競合、機器の反応の上限を測ったことにはならない。余裕を残し、各前提が変わった時に再評価する。'],
 [('平均値で見積る','典型時は見えるが期限の保証には足りない。'),('上限と余裕を設定','要求へ対応づけられる。上限の根拠を維持する必要がある。')],
 [('合計4500us、期限5000us','margin=500','待ちと出力を含める。'),('合計5500us','over-budget=1','処理本体が速くても期限を外す。'),('合計5000us','boundary=1','境界と余裕の規則を決める。')],
 [('実測最大を最悪値としてよいか。','未観測の条件があり得る。測定・解析の前提と余裕を明示する。'),('改善対象はどう選ぶか。','入力から出力の同じ時間軸で、大きな区間と変動の原因を探す。'),('並行区間も単純に加算するか。','しない。因果と時間の重なりを整理してから予算を作る。')],
 r'''
 static uint32_t total(uint32_t in,uint32_t run,uint32_t wait,uint32_t out) {
     return in+run+wait+out; /* この実習の小さな値の範囲に限定 */
 }
 int main(void) {
     uint32_t budget=5000, good=total(500,1000,2000,1000), bad=total(500,1000,3000,1000);
     assert(good==4500 && bad>budget);
     printf("margin=%" PRIu32 "\n",budget-good);
     printf("over-budget=%d\n",bad>budget);
     printf("boundary=%d\n",total(500,1000,2500,1000)<=budget);
     return 0;
 }
 ''','''margin=500
 over-budget=1
 boundary=1''')

add('hardware','チャタリングと、電気的な条件を分ける',
 'スイッチの一操作が複数の入力に見える。連続する同じ観測を待つ処理と、実回路の条件を分けて検証する。',
 '一定周期のデジタル観測で三回連続一致を安定とするモデル。電圧、しきい値、電気的なノイズ除去の保証ではない。',
 ['1、0、1、1、1では五回目で三回連続の1になる。周期を変えれば待ち時間も変わるため、回数を時間の要求へ結び付ける。',
  '安定を待つコードだけでは過電圧や浮いた入力、メタステーブルへ対処できない。データシート、プル抵抗、入力回路、配線と計測条件を確認する。配列のモデルと実信号を混同しない。'],
 [('ソフトの安定判定','設定しやすいが応答遅延が増える。'),('回路と入力機能の対策','電気的な条件を改善できる。部品と信号の仕様が必要。')],
 [('1,0,1,1,1','stable-at=5','連続の開始を取り直す。'),('1,0,1,0','unstable=0','まだ安定していない。'),('1,1,1','minimum=3','最小の安定列。')],
 [('取得周期を変えると何が変わるか。','同じ連続回数でも検出までの時間が変わる。最短パルスと許容遅延を確認する。'),('過電圧をこのコードで防げるか。','防げない。保護回路やレベル変換を部品の仕様で対策する。'),('追加する実機条件は。','ノイズ、温度、電源、入力しきい値、取得周期とパルス幅を確認する。')],
 r'''
 static size_t stable_at(const int *samples,size_t count) {
     unsigned consecutive=0; int last=-1;
     for(size_t i=0;i<count;++i) {
         consecutive=samples[i]==last?consecutive+1u:1u; last=samples[i];
         if(consecutive==3u) return i+1u;
     }
     return 0;
 }
 int main(void) {
     const int a[]={1,0,1,1,1}, b[]={1,0,1,0}, c[]={1,1,1};
     assert(stable_at(a,5)==5 && stable_at(b,4)==0 && stable_at(c,3)==3);
     printf("stable-at=%zu\n",stable_at(a,5));
     printf("unstable=%zu\n",stable_at(b,4));
     printf("minimum=%zu\n",stable_at(c,3)); return 0;
 }
 ''','''stable-at=5
 unstable=0
 minimum=3''')

add('memory','DMA完了と、CPUから読める状態は別',
 '受信DMAは完了したが、CPUは古い値を読む。バッファの所有権とキャッシュ整合の手順を分ける。',
 '非コヒーレントな受信DMAの抽象モデル。所有権の返却と必要な整合処理後にCPUが読む。具体的な命令や順序は対象機の仕様で決める。',
 ['DMAが所有する間はCPUが同じバッファを読書きしない。完了後も古いキャッシュラインが残る構成では整合が必要になる。volatileは所有権やキャッシュ処理の代わりではない。',
  '転送方向、開始前のライン処理、完了確認、バリア、ライン境界の共有を対象仕様で確認する。モデルのsyncは状態名であり実命令ではない。コヒーレントな機種へ同じ手順を無条件に適用しない。'],
 [('無秩序な共有','コピーは減るが古い値やデータ破壊の原因になる。'),('所有権と整合点を明示','利用時点を検査できる。対象依存の処理は別に必要。')],
 [('DMA所有中','during=0','CPUの読取りを禁止。'),('完了直後、未整合','after-complete=0','完了と可視性を分ける。'),('整合してCPUへ返す','after-sync=1','モデルの利用条件を満たす。')],
 [('volatileだけで最新値が見えるか。','保証しない。キャッシュ、バス、所有権とバリアを機種の仕様で確認する。'),('ラインを別データと共有すると何が問題か。','ライン単位の処理が他のデータへ影響し得る。配置と所有権を検討する。'),('ホスト試験でDMA実装を証明できるか。','できない。実転送、整合処理、割込み順、最適化条件を対象機で検証する。')],
 r'''
 enum Owner { CPU, DEVICE, NEEDS_SYNC };
 static bool readable(enum Owner owner) { return owner==CPU; }
 int main(void) {
     enum Owner owner=DEVICE;
     assert(!readable(owner)); printf("during=%d\n",readable(owner));
     owner=NEEDS_SYNC;
     assert(!readable(owner)); printf("after-complete=%d\n",readable(owner));
     owner=CPU; /* 抽象的な整合完了。CPUの命令を実行していない */
     assert(readable(owner)); printf("after-sync=%d\n",readable(owner)); return 0;
 }
 ''','''during=0
 after-complete=0
 after-sync=1''')

add('language','範囲検査の加算も、オーバーフローする',
 '外部入力の長さでバッファへ追記する。used+nの計算で容量検査をすり抜けないようにする。',
 'used<=capacityを確認してからnをcapacity-usedと比較する。コピー元・先の有効性や重なりは別の前提。',
 ['符号なし加算は最大値を越えると剰余で小さくなる。used+n<=capacityだけでは大きなnに対する判定が壊れ得る。引算の前提を先に確認して残容量と比較する。',
  '実習は容量の算術を検査する。ポインターの範囲、元データの長さ、重なり、検査後の並行変更は実装で別に確認する。C++で所有権やコンテナーを使っても外部入力の境界は残る。'],
 [('加算して判定','自然に見えるが加算の桁あふれを見落とす。'),('残容量で比較','加算を避けられる。usedの妥当性を先に確かめる。')],
 [('used=8、n=0、capacity=8','boundary=1','空の追加は算術上許容。'),('n=SIZE_MAX','huge=0','加算せず拒否。'),('used=9、capacity=8','invalid-used=0','引算のアンダーフローを防ぐ。')],
 [('size_tなら加算は安全か。','未定義動作にならなくても剰余で小さくなり、検査を誤る。'),('これだけでmemcpyは安全か。','違う。ポインターと元データの範囲、重なり、並行変更も確認する。'),('追加する境界値は。','ゼロ、残容量ちょうど、一つ越え、SIZE_MAX、usedが容量を越えた値。')],
 r'''
 static bool fits(size_t used,size_t n,size_t capacity) {
     return used<=capacity && n<=capacity-used;
 }
 int main(void) {
     assert(fits(8,0,8) && fits(7,1,8));
     assert(!fits(7,SIZE_MAX,8) && !fits(9,0,8) && !fits(7,2,8));
     printf("boundary=%d\n",fits(8,0,8));
     printf("huge=%d\n",fits(7,SIZE_MAX,8));
     printf("invalid-used=%d\n",fits(9,0,8)); return 0;
 }
 ''','''boundary=1
 huge=0
 invalid-used=0''')

add('boot-build','エントリー値を、対象アーキテクチャの意味で検査する',
 'Cortex-Mの説明用イメージで初期SPとリセットベクターの取り違えを検出する。',
 'この構成ではRAM範囲内の8バイト整列SPと、Flash内のThumbエントリーを要求する。他の機種へ一律に一般化しない。',
 ['単なる整数としてアドレスを見ると、領域、整列、命令状態の条件を落とす。リンカースクリプト、マップ、起動コードと書込先を対応づける。',
  '検査が通っても起動成功の証明にはならない。ベクター配置、初期化、クロック、割込み、ブートローダーとの契約を対象機で確認する。ホストで例のアドレスへ実アクセスしない。'],
 [('生の値を目視','確認の入口だが領域や命令状態を落としやすい。'),('対象仕様から条件を生成','受入検査を自動化できる。対象とリンカー設定の一致が必要。')],
 [('正しい領域・整列・Thumb','valid=1','この例の条件を満たす。'),('SP未整列','bad-sp=0','起動前の条件違反。'),('Thumbビット0','bad-entry=0','命令状態の条件違反。')],
 [('ホストでこの番地を読んでよいか。','いけない。数値だけを検査するモデルである。'),('領域を決め打ちして使い回せるか。','対象機のメモリマップとリンカー設定から導出し、版と一緒に管理する。'),('合格後の実機確認は。','初期化、エントリーへの到達、配置、割込み、起動失敗時の復旧を確認する。')],
 r'''
 static bool valid_vector(uint32_t sp,uint32_t reset) {
     uint32_t entry=reset & ~UINT32_C(1);
     bool stack=sp>UINT32_C(0x20000000) && sp<=UINT32_C(0x20002000) && sp%8u==0u;
     bool code=(reset&1u)!=0u && entry>=UINT32_C(0x08000000) && entry<UINT32_C(0x08010000);
     return stack && code;
 }
 int main(void) {
     assert(valid_vector(UINT32_C(0x20002000),UINT32_C(0x08000101)));
     assert(!valid_vector(UINT32_C(0x20000003),UINT32_C(0x08000101)));
     assert(!valid_vector(UINT32_C(0x20002000),UINT32_C(0x08000100)));
     printf("valid=%d\n",valid_vector(UINT32_C(0x20002000),UINT32_C(0x08000101)));
     printf("bad-sp=%d\n",valid_vector(UINT32_C(0x20000003),UINT32_C(0x08000101)));
     printf("bad-entry=%d\n",valid_vector(UINT32_C(0x20002000),UINT32_C(0x08000100))); return 0;
 }
 ''','''valid=1
 bad-sp=0
 bad-entry=0''')

add('interrupts','平均負荷が低くても、待ちで期限を外す',
 '低優先の処理が持つ資源を待ち、周期処理が遅れる。実行時間、ブロッキングと高優先の干渉を応答時間へ含める。',
 '単一コア・固定優先度・プリエンプティブ、独立した周期の高優先タスク一つ。ジッタは省略し、切替費用などは実用で見積りへ含める。',
 ['Rの初期値をC+Bとし、Rの次値をC+B+ceil(R/T)×Hとして固定点まで加える。Hは高優先処理の実行時間、Tは周期。応答は実行時間だけではなく、低い平均負荷でも長い資源待ちで期限を外す。',
  'この例は一つの干渉タスクに限定する。複数タスク、入れ子割込み、共有資源、周期の揺れを対象に合わせて拡張する。優先度継承があっても待ちの上限が自動で要求を満たすとは限らない。'],
 [('CPU負荷率だけを見る','全体傾向には有用だが個別の応答上限を示さない。'),('応答とブロッキングを解析','期限へ対応づく。実行時間と干渉の仮定の検証が必要。')],
 [('C=1000、B=500、H=500、T=2000us','response=2000','固定点まで反復。'),('B=1800へ増加','blocked-response=3800','資源待ちの影響。'),('期限2500us','late=1','待ちによる期限違反。')],
 [('実行時間だけ最適化すれば十分か。','待ちや干渉が支配的なら足りない。上限を増やす項を確認する。'),('収束しなければ無限に計算するか。','しない。解析の打切りと期限違反を扱い、仮定した負荷が成立するか調べる。'),('実機で照合するには。','割込み、開始・終了、待ちを同じ時計で測り、最悪の経路と条件を確認する。')],
 r'''
 static uint32_t response(uint32_t c,uint32_t b,uint32_t h,uint32_t period) {
     assert(period>0u);
     uint32_t r=c+b;
     for(unsigned i=0;i<32u;++i) {
         uint32_t next=c+b+((r+period-1u)/period)*h;
         if(next==r) return r;
         r=next; /* この例の小さな値と一つの干渉タスクに限定 */
     }
     return UINT32_MAX;
 }
 int main(void) {
     uint32_t good=response(1000,500,500,2000), bad=response(1000,1800,500,2000);
     assert(good==2000 && bad==3800);
     printf("response=%" PRIu32 "\n",good);
     printf("blocked-response=%" PRIu32 "\n",bad);
     printf("late=%d\n",bad>2500u); return 0;
 }
 ''','''response=2000
 blocked-response=3800
 late=1''')

add('rtos','満杯時の方針を、キューの仕様に含める',
 '処理よりイベントの到着が速い。容量二で三件目をどう扱うか、欠落を観測できるようにする。',
 '満杯なら新しいイベントを拒否しFIFOを保つモデル。単一スレッドで方針を検証し、ISR用APIや排他は実装しない。',
 ['送れた二件だけの試験では、三件目が消える条件を見落とす。破棄、上書き、集約、待機は異なる仕様なので、イベントの意味と発生上限から選ぶ。',
  '実RTOSではISRから使えるAPI、割込み優先度、起床とスケジューラを確認する。満杯時の無制限待機をISRへ持ち込まない。拒否の件数を観測し、処理が追いつかない状態を検出する。'],
 [('満杯で拒否','FIFOを保つ。拒否の観測と回復が必要。'),('最新値へ集約','状態の通知には有効な場合がある。全件必要な操作には使えない。')],
 [('1と2を追加','二件を保持','容量内のFIFO。'),('3を追加','dropped=1','拒否を返す。'),('二件取り出す','fifo=1,2 / empty=1','既存順を保つ。')],
 [('容量を増やせば必ず解決か。','平均的に処理が追いつかなければ再び満杯になる。発生率と処理上限を確認する。'),('状態通知と操作要求で破棄方針を同じにしてよいか。','最新値だけでよい状態と、一件ずつ必要な操作を分ける。'),('単一スレッド試験で排他も正しいと言えるか。','言えない。割込み・タスク間の競合とRTOSの契約を別に検証する。')],
 r'''
 struct Queue { int data[2]; unsigned head,tail,count; };
 static bool push(struct Queue *q,int value) {
     if(q->count==2u) return false;
     q->data[q->tail]=value; q->tail=(q->tail+1u)%2u; ++q->count; return true;
 }
 static bool pop(struct Queue *q,int *value) {
     if(q->count==0u) return false;
     *value=q->data[q->head]; q->head=(q->head+1u)%2u; --q->count; return true;
 }
 int main(void) {
     struct Queue q={0}; int a=0,b=0,unused=0;
     assert(push(&q,1) && push(&q,2)); bool dropped=!push(&q,3);
     assert(pop(&q,&a) && pop(&q,&b));
     printf("dropped=%d\n",dropped); printf("fifo=%d,%d\n",a,b);
     printf("empty=%d\n",!pop(&q,&unused)); return 0;
 }
 ''','''dropped=1
 fifo=1,2
 empty=1''')

add('linux','部分I/Oと、割込み・再待機を区別する',
 'デバイスへ三バイト書く要求が、二バイト、割込み、一バイトに分かれる。一回のwrite相当処理で全部終わる前提を外す。',
 '仮想I/Oでは正の戻りだけoffsetを進め、割込みは同じ位置で再試行、would-blockは待機へ戻す。ゼロは進捗なしとし、書込みの終了と断定しない。実errnoやカーネルを再現しない。',
 ['戻った数を無視して先頭から再送すると二重データになり、要求数だけ進めると欠落する。正の戻り値が残りの範囲内かを検査し、進んだ分だけ保存する。',
  'would-blockで忙しく再試行するとCPUを使い続ける。実LinuxではAPIの契約、EINTR、EAGAIN、poll等の待機、期限、終了と取消を確認する。このコードの負値はモデル専用であり実errnoと対応づけない。'],
 [('一回で全部送る前提','短いが部分I/Oで欠落や二重化を起こす。'),('進捗を持って継続','分割と待機を扱える。期限、終了と取消も管理する。')],
 [('2、割込み、1','sent=3 calls=3','割込みで進捗を変えない。'),('1の後にwould-block','deferred-offset=1','進捗を残して待機へ戻る。'),('書込みの戻り値0','zero=no-progress','読取りのEOFと同じ意味にしない。')],
 [('負の戻りをsize_tへ変換してよいか。','いけない。エラーの分岐を先に行い、正の範囲だけ進捗へ反映する。'),('部分書込み後に取消されたら。','送信済みの部分は取り消せない場合がある。上位プロトコルの要求境界や復旧を設計する。'),('/devの実装へそのまま当てはめられるか。','対象ドライバーとAPIの戻り値・待機・終了の契約を確認する。モデルの規則を一律に使わない。')],
 r'''
 enum Status { PROGRESS, COMPLETE, RETRY, DEFERRED, NO_PROGRESS, INVALID };
 enum MockResult { IO_INTERRUPTED=-1, IO_WOULD_BLOCK=-2 };
 static enum Status advance(size_t *offset,size_t total,int result) {
     if(result==IO_INTERRUPTED) return RETRY;
     if(result==IO_WOULD_BLOCK) return DEFERRED;
     if(result<0 || *offset>total) return INVALID;
     if(result==0) return NO_PROGRESS;
     if((size_t)result>total-*offset) return INVALID;
     *offset+=(size_t)result; return *offset==total?COMPLETE:PROGRESS;
 }
 int main(void) {
     const int results[]={2,IO_INTERRUPTED,1}; size_t offset=0;
     for(size_t i=0;i<3;++i) {
         enum Status s=advance(&offset,3,results[i]);
         assert(s==(i==0?PROGRESS:i==1?RETRY:COMPLETE));
     }
     printf("sent=%zu calls=3\n",offset);
     offset=1; assert(advance(&offset,3,IO_WOULD_BLOCK)==DEFERRED);
     printf("deferred-offset=%zu\n",offset);
     assert(advance(&offset,3,0)==NO_PROGRESS); puts("zero=no-progress"); return 0;
 }
 ''','''sent=3 calls=3
 deferred-offset=1
 zero=no-progress''')

CRC8=r'''
static uint8_t crc8(const uint8_t *data,size_t n) {
    uint8_t crc=0;
    for(size_t i=0;i<n;++i) {
        crc=(uint8_t)(crc^data[i]);
        for(unsigned bit=0;bit<8u;++bit)
            crc=(uint8_t)((crc&0x80u)?(((unsigned)crc<<1)^0x07u):((unsigned)crc<<1));
    }
    return crc;
}
'''

add('communication','長さ、内容、CRCの順に境界を検査する',
 '受信フレームの長さ欄が壊れた。先にデータを読むパーサーを、範囲外参照しない順序へ変えたい。',
 'フレームは長さ1バイト、データ、CRC8の構造。先に実長と長さ欄の整合を検査し、範囲が確定してからCRCを調べる。暗号学的認証ではない。',
 ['先に長さ欄だけを信じて読むと、CRCの検査へ到達する前に範囲外アクセスする。最小長、長さ欄と実データ長、CRCの順で確認し、不足・余剰の扱いも定める。',
  'CRC8は偶発的な破損を検出するための小さな例で、攻撃者による改ざんや再送を防がない。実用ではエンディアン、要求ID、再送・重複、フレームの同期回復、認証を用途に応じて追加する。'],
 [('長さ欄を先に信頼','簡単だが壊れた入力で範囲外を読む。'),('段階で妥当性を確認','解析範囲を限定できる。異常入力と同期回復の仕様が必要。')],
 [('正常フレーム','valid=1','長さとCRCが一致。'),('データを一ビット変更','bad-crc=0','CRC不一致で拒否する。'),('長さ欄だけ200へ変更','bad-length=0','CRC計算前に拒否する。')],
 [('CRCが一致すれば正しい送信者か。','証明できない。認証や改ざん対策は別の仕組みを使う。'),('受信がフレーム単位で返ると考えてよいか。','ストリームでは分割・連結され得る。蓄積と境界の検出、上限を設計する。'),('既知のCRCベクターを試す理由は。','生成と検査が同じ誤りを共有しても相互に通る可能性がある。独立した既知値で規則を確認する。')],
 CRC8+r'''
 static bool valid(const uint8_t *frame,size_t n) {
     if(n<2u) return false;
     if((size_t)frame[0]!=n-2u) return false;
     return crc8(frame,n-1u)==frame[n-1u];
 }
 int main(void) {
     const uint8_t known[]="123456789";
     assert(crc8(known,9)==0xf4u); /* CRC-8/SMBUS: poly 07, init 00, xorout 00 */
     uint8_t frame[]={2,0x10,0x20,0}; frame[3]=crc8(frame,3);
     assert(valid(frame,4)); printf("valid=%d\n",valid(frame,4));
     frame[1]^=1u; assert(!valid(frame,4)); printf("bad-crc=%d\n",valid(frame,4));
     frame[0]=200; assert(!valid(frame,4)); printf("bad-length=%d\n",valid(frame,4));
     return 0;
 }
 ''','''valid=1
 bad-crc=0
 bad-length=0''')

add('power-state','復帰した時点と、出力を許可する時点を分ける',
 'スリープからCPUは復帰したが、バスと周辺機器は未準備だった。以前の出力を即座に再開しない状態機械にする。',
 '抽象状態RESTORINGでは出力を禁止し、確認済みのREADYだけで許可する。許可フラグが実際の安全を証明するものではない。',
 ['割込みで目が覚めることと、周辺機器の再初期化や状態確認が終わることは違う。前回の値を再利用するなら、その鮮度と復元順を定める。',
  '復帰途中の失敗はFAULTへ移し、要求に合う安全側の出力を実機で検証する。ソフトウェアの禁止フラグだけに頼らず、回路や機器側の条件、ウォッチドッグ、リセット時の出力も評価する。'],
 [('起床と同時に出力','復帰は速いが未準備の機器へ操作する。'),('復帰準備を独立状態にする','禁止期間を検査できる。期限と失敗時の回復を設計する。')],
 [('復帰してRESTORING','restoring=0','まだ許可しない。'),('機器確認後READY','ready=1','モデルの利用条件を満たす。'),('故障を検出','fault=0','再び禁止する。')],
 [('復帰割込みだけで何が分かるか。','CPU側の復帰契機を示すが、全機器の準備や値の鮮度は証明しない。'),('安全側の出力を一律にゼロにしてよいか。','用途による。危険分析や機器の意味に基づいて定め、実際の回路と出力を確認する。'),('失敗注入をどこへ入れるか。','クロック・バス・周辺機器の初期化、観測の再取得、出力許可の直前等を分ける。')],
 r'''
 enum State { SLEEP, RESTORING, READY, FAULT };
 static bool output_allowed(enum State s) { return s==READY; }
 int main(void) {
     enum State state=SLEEP;
     state=RESTORING; assert(!output_allowed(state)); printf("restoring=%d\n",output_allowed(state));
     state=READY; assert(output_allowed(state)); printf("ready=%d\n",output_allowed(state));
     state=FAULT; assert(!output_allowed(state)); printf("fault=%d\n",output_allowed(state)); return 0;
 }
 ''','''restoring=0
 ready=1
 fault=0''')

add('storage-update','電源断の後、どのコピーを採用できるか',
 '二つの保存領域へ交互に設定を記録する。新しいコピーの途中で電源が落ちても、前の有効な設定を選びたい。',
 'モデルはコミット済みでCRCが一致する記録だけを候補にし、世代の大きい方を採用する。世代の周回は扱わず、実Flashの原子性は保証しない。',
 ['データ、検査値、採用を示す記録を別の段階に分ける。新コピーが途中なら旧コピーを使い、両方有効なら新しい世代を選ぶ。構造体の生バイトをCRCへ渡すとパディング等に依存するため、例では明示的に符号化する。',
  '実機では消去・書込単位、ビット遷移、途中書込の読出し、寿命、ECC、コミット値の書込みを検証する。CRCは認証ではない。更新では署名とロールバック防止、初回起動の確定も別に必要になる。'],
 [('一箇所へ上書き','単純で容量は小さいが、途中終了で旧値も失い得る。'),('有効コピーを選択','旧値を残せる。メタデータ、消耗と両方無効時の方針が必要。')],
 [('新コピー未コミット','power-cut=4','旧世代を選ぶ。'),('新コピーの検査と確定が完了','committed=5','新世代を採用する。'),('新コピーの内容が破損','corrupt=4','旧値へ戻るモデル。')],
 [('CRCを構造体のsizeof範囲へそのまま計算してよいか。','パディング、エンディアン、形式の版で変わる。保存形式を明示する。'),('世代番号が周回する場合は。','単純な大小比較を使えない。比較可能な更新幅と番号規則、初期化や復旧の方針を定める。'),('ホストの電源断モデルで実Flashの耐性を保証できるか。','できない。実電源断を各書込段階へ注入し、機器の保証と復旧結果を照合する。')],
 CRC8+r'''
 struct Record { uint32_t generation; uint8_t value,crc; bool committed; };
 static uint8_t checksum(const struct Record *r) {
     uint8_t encoded[5]={(uint8_t)r->generation,(uint8_t)(r->generation>>8),
         (uint8_t)(r->generation>>16),(uint8_t)(r->generation>>24),r->value};
     return crc8(encoded,5);
 }
 static bool valid_record(const struct Record *r) { return r->committed && r->crc==checksum(r); }
 static const struct Record *select_record(const struct Record *a,const struct Record *b) {
     bool av=valid_record(a),bv=valid_record(b);
     if(!av && !bv) return NULL;
     if(!av) return b;
     if(!bv) return a;
     return a->generation>=b->generation?a:b;
 }
 int main(void) {
     struct Record old={4,10,0,true}, next={5,20,0,false};
     old.crc=checksum(&old); next.crc=checksum(&next);
     assert(select_record(&old,&next)==&old);
     printf("power-cut=%" PRIu32 "\n",select_record(&old,&next)->generation);
     next.committed=true; assert(select_record(&old,&next)==&next);
     printf("committed=%" PRIu32 "\n",select_record(&old,&next)->generation);
     next.value^=1u; assert(select_record(&old,&next)==&old);
     printf("corrupt=%" PRIu32 "\n",select_record(&old,&next)->generation);
     old.committed=false; assert(select_record(&old,&next)==NULL); return 0;
 }
 ''','''power-cut=4
 committed=5
 corrupt=4''')

add('debug-test','タイマーの周回を、経過時間の計算へ含める',
 '長時間稼働後だけタイムアウトが壊れる。32ビットの単調カウンターが周回する境界を試験したい。',
 'uint32_tの剰余差を用い、経過が一周未満と分かる範囲で比較する。時計の停止、再起動、複数周回は別に扱う。',
 ['現在値が開始値より小さくても、周回した後なら経過時間は正である。符号付きへ変換したり、開始値に期限を足して単純比較すると、境界付近で意味を誤る場合がある。',
  'この差の計算が成立するのは、二時点が同じ時計で一周未満という前提があるため。長い休止、周回回数、再起動後の基準を含め、計測の条件と取得方法を決める。ログで時間を使う場合も時計の種類を記す。'],
 [('絶対値を単純比較','短い動作では通っても周回で壊れ得る。'),('剰余差と範囲を明示','境界を試験できる。周回回数と時計の寿命の仮定が必要。')],
 [('fffffff0から00000020','elapsed=48','一回の周回を越えた差。'),('期限32','timed-out=1','定義した範囲で判定する。'),('開始と現在が同じ','same=0','本当に零か複数周回かは前提が必要。')],
 [('同じ値なら必ず経過零か。','一周以上を許すなら断定できない。観測間隔の上限や周回数の拡張を設計する。'),('異なる時計の値を引いてよいか。','よくない。基準と単位、停止・再起動の条件を確認する。'),('実機の計測へ何を残すか。','時計の型、分解能、周回周期、取得の原子性、測定区間と取得による負荷を記録する。')],
 r'''
 static uint32_t elapsed(uint32_t start,uint32_t now) { return now-start; }
 int main(void) {
     uint32_t delta=elapsed(UINT32_C(0xfffffff0),UINT32_C(0x20));
     assert(delta==48u);
     printf("elapsed=%" PRIu32 "\n",delta);
     printf("timed-out=%d\n",delta>=32u);
     printf("same=%" PRIu32 "\n",elapsed(10,10)); return 0;
 }
 ''','''elapsed=48
 timed-out=1
 same=0''')

add('security-process','検証済みでも、製品と版の条件を外してはいけない',
 '更新候補に正しい署名があっても、別製品用や古い版なら適用しない。セキュリティの受入条件を分解する。',
 'モデルのverifiedは信頼した検証器の結果を入力する前提。署名検証を実装せず、製品一致と最低版の規則だけを検査する。',
 ['署名が有効でも、対象製品や用途へ結び付いていなければ適用してよいとは限らない。古い正規版の再投入も、許可するかを要件として定める。ハッシュの一致だけを送信元の認証と混同しない。',
  '真偽値を外部のメタデータからそのまま信用してはいけない。実用では信頼の起点、署名対象、鍵の管理と失効、ロールバック防止の保存、更新失敗時の復旧を確認する。モデル合格を暗号の正しさや製品の安全性の証明へ読み替えない。'],
 [('ハッシュだけで判定','破損検知には使えても、正規の発行者や適用可否を証明しない。'),('認証と適用条件を分離','どの根拠で許可するかを説明できる。鍵と版の永続管理が必要。')],
 [('検証済み・製品一致・版4以上','allowed=1','このモデルの条件を満たす。'),('未検証','unverified=0','認証前提を満たさない。'),('正規版だが古い版、または別製品','rollback=0 / wrong-product=0','認証後も適用条件を検査する。')],
 [('verifiedを受信データから読んでよいか。','いけない。信頼できる検証手順の結果でなければ、攻撃者が許可値を作れてしまう。'),('最低版を通常の設定だけに保存すればよいか。','改ざん・巻戻しや電源断を含む要件による。信頼する保存と更新方法を定める。'),('開発工程へ必要な検証は。','脅威・故障の想定、鍵と依存の管理、正常・異常・電源断の試験、更新と復旧の記録を追跡可能にする。')],
 r'''
 static bool allowed(bool verified,bool product_matches,uint32_t version,uint32_t minimum) {
     return verified && product_matches && version>=minimum;
 }
 int main(void) {
     assert(allowed(true,true,4,4));
     assert(!allowed(false,true,4,4) && !allowed(true,true,3,4) && !allowed(true,false,4,4));
     printf("allowed=%d\n",allowed(true,true,4,4));
     printf("unverified=%d\n",allowed(false,true,4,4));
     printf("rollback=%d\n",allowed(true,true,3,4));
     printf("wrong-product=%d\n",allowed(true,false,4,4)); return 0;
 }
 ''','''allowed=1
 unverified=0
 rollback=0
 wrong-product=0''')

def code_for(workbook):return HEADER+'\n'+workbook['program']+'\n'
def output_for(workbook):return workbook['output']
assert len(WORKBOOKS)==13
