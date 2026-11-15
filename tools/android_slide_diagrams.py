"""Authored SVG diagrams for the Android slide course (standard library only).

Numbers link roles to the four explanatory steps, not necessarily runtime order.
Each layout makes boundaries, branching, storage or concurrency explicit.
"""
from html import escape

LAYOUTS = {
    'start':'cycle', 'overview':'tree', 'layers':'layers', 'execution':'process',
    'ipc':'sequence', 'components':'components', 'lifecycle':'states', 'boot':'timeline',
    'power':'decision', 'graphics':'buffers', 'audio':'audio', 'network-security':'matrix',
    'faults':'evidence', 'build':'deployment', 'investigation':'trace', 'automotive':'feedback',
    'walkthrough':'timeline', 'first-app':'trace', 'app-design':'cycle', 'data-practice':'storage',
    'binder-practice':'reconnect', 'aaos-detail':'cockpit', 'test-lab':'evidence',
    'os-integration':'boundary', 'capstone':'feedback', 'ethernet':'network',
    'microphone':'audio', 'hardware-control':'boundary', 'adb-detail':'hosts',
    'bugreport-detail':'trace', 'partition-detail':'partitions', 'review':'cycle',
}
LABELS = {
    'cycle':'循環図：説明の番号を順に追う', 'tree':'構成図：基盤と製品の関係',
    'layers':'レイヤ図：要求の境界を追う', 'process':'包含図：プロセスと実行場所',
    'sequence':'シーケンス図：要求と応答を分ける', 'components':'コンポーネント図：解決と画面の履歴',
    'states':'状態図：前面化と離脱の代表例', 'timeline':'時間軸：代表的な場面の順序',
    'decision':'分岐図：条件を満たす場合だけ休止', 'buffers':'描画図：バッファの受渡しと合成',
    'audio':'データ経路図：制御の条件とは区別', 'matrix':'条件図：別々に観測する軸',
    'evidence':'証拠の対応図：期待と観測を比較', 'deployment':'配置図：成果物と実機を照合',
    'trace':'調査図：操作と記録を時刻で結ぶ', 'feedback':'要求・観測図：要求と結果を分ける',
    'storage':'保存図：一時状態と永続化を分ける', 'reconnect':'通信図：切断後は状態を再取得',
    'cockpit':'車載の条件図：四つの観測軸', 'boundary':'コンポーネント図：責任と境界',
    'network':'ネットワーク図：接続と到達性を区別', 'hosts':'配置図：PCと端末の境界',
    'partitions':'配置図：イメージと領域の対応',
}

class SVG:
    def __init__(self, prefix):
        self.prefix=prefix
        self.parts=[]
    def text(self,x,y,label,cls='annotation',anchor='middle'):
        self.parts.append(f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}">{escape(label)}</text>')
    def region(self,x,y,w,h,label):
        self.parts.append(f'<rect class="region" x="{x}" y="{y}" width="{w}" height="{h}" rx="16"/>')
        self.text(x+16,y+26,label,'region-label','start')
    def node(self,i,x,y,w,h,label,kind='box'):
        self.parts.append(f'<g data-step="{i}" class="role">')
        if kind=='state':
            self.parts.append(f'<rect class="node-body state-body" x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}"/>')
        elif kind=='diamond':
            self.parts.append(f'<path class="node-body" d="M{x+w/2} {y} L{x+w} {y+h/2} L{x+w/2} {y+h} L{x} {y+h/2} Z"/>')
        else:
            self.parts.append(f'<rect class="node-body" x="{x}" y="{y}" width="{w}" height="{h}" rx="{3 if kind=="file" else 10}"/>')
            if kind=='component':
                self.parts.append(f'<path class="symbol" d="M{x+w-19} {y+8}h12v16h-12z M{x+w-23} {y+11}h7v4h-7z M{x+w-23} {y+18}h7v4h-7z"/>')
            if kind=='db':
                self.parts.append(f'<ellipse class="symbol" cx="{x+w/2}" cy="{y+9}" rx="{w/2-3}" ry="9"/>')
            if kind=='device':
                self.parts.append(f'<path class="symbol" d="M{x+12} {y+h-10}h{w-24} M{x+w/2-12} {y+h+6}h24"/>')
        self.parts.append(f'<circle class="badge" cx="{x+14}" cy="{y+14}" r="12"/><text class="badge-text" x="{x+14}" y="{y+21}">{i+1}</text>')
        lines=[]
        for line in label.split('|'):
            # Wrap Japanese labels to the available width; keep API identifiers whole.
            weight=lambda t:sum(.57 if ord(c)<128 else 1 for c in t)
            limit=(w-24)/27
            if weight(line)>limit and any(ord(c)>127 for c in line):
                part=''
                for char in line:
                    if part and weight(part+char)>limit:
                        lines.append(part);part=''
                    part+=char
                if part:lines.append(part)
            else:lines.append(line)
        for j,line in enumerate(lines):
            size=min(27 if len(lines)==1 or h>=80 else 24,(w-48)/max(1,weight(line)))
            self.parts.append(f'<text class="node-label" style="font-size:{size:.2f}px" x="{x+w/2+12}" y="{y+h/2+(j-(len(lines)-1)/2)*size+size*.26}">{escape(line)}</text>')
        self.parts.append('</g>')
    def edge(self,i,d,label='',x=0,y=0,dashed=False):
        self.parts.append(f'<g data-step="{i}" class="edge"><path class="edge-path{" dashed" if dashed else ""}" d="{d}" marker-end="url(#{self.prefix}-arrow)"/><path class="signal" d="{d}" pathLength="100"/></g>')
        if label:self.text(x,y,label,'edge-label')
    def raw(self,s):self.parts.append(s)
    def finish(self):
        return f'<svg class="lesson-svg" viewBox="0 0 900 240" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><defs><marker id="{self.prefix}-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="currentColor"/></marker></defs>'+''.join(self.parts)+'</svg>'

def diagram(slide, static=False):
    chapter=slide['chapter'];kind=LAYOUTS[chapter];n=slide['nodes'];s=SVG(('static-' if static else 'live-')+chapter)
    if kind=='layers':
        for i,label in enumerate(n):
            s.node(i,230,8+i*57,440,46,label,'component')
            if i<3:s.edge(i,f'M700 {32+i*57} V{89+i*57}', '要求' if i==0 else '',746,65)
        s.edge(3,'M195 202 V30','状態を観測',97,125,True)
    elif kind=='process':
        s.region(15,22,370,200,'SYSTEM / 生成側');s.region(425,22,460,200,'APP PROCESS / ARTで実行')
        s.node(0,35,76,145,85,'起動要求','component');s.node(1,215,76,150,85,'Zygote','component')
        s.node(2,445,76,170,85,'アプリ|プロセス','component');s.node(3,660,76,200,85,'メインループ','state')
        s.edge(0,'M180 118 H215');s.edge(1,'M365 118 H445','生成',402,100);s.edge(2,'M615 118 H660')
        s.edge(3,'M835 162 V193 H685 V163','入力・描画',757,218,True)
    elif kind in ('sequence','reconnect'):
        for x,t in [(130,'呼出側'),(450,'Binder / 接続'),(770,'サービス')]:
            s.text(x,29,t,'node-label');s.raw(f'<path class="lifeline" d="M{x} 42 V230"/>')
        if kind=='sequence':
            s.edge(0,'M130 70 H450','① 契約に従う要求',290,60)
            s.edge(1,'M450 112 H770','② プロセス境界',610,101)
            s.node(2,683,130,175,46,'検査・処理','component')
            s.edge(3,'M770 208 H130','④ 応答 / 後からの通知',450,197,True)
        else:
            s.edge(0,'M130 65 H770','① 接続',450,55)
            s.edge(1,'M130 109 H770','② AIDL要求',450,98)
            s.raw('<path class="fault-mark" d="M755 132l30 25m0-25l-30 25"/>')
            s.text(470,157,'③ サービス死亡・切断','node-label')
            s.edge(2,'M770 171 H130','',0,0,True)
            s.edge(3,'M130 215 H770','④ 再接続 → 再登録・状態取得',450,204)
    elif kind=='components':
        s.region(480,8,400,224,'TASK / 画面と戻る履歴')
        s.node(0,18,85,170,70,'Intent','file');s.node(1,255,85,165,70,'受け手|解決','component')
        s.node(2,520,59,320,65,'Activity','component');s.node(3,520,155,320,60,'バックスタック','file')
        s.edge(0,'M188 120 H255','解決要求',220,103);s.edge(1,'M420 120 H462 V90 H520','起動',463,68)
        s.edge(2,'M680 124 V155','履歴',735,145)
    elif kind=='states':
        for i,(x,y) in enumerate([(25,30),(265,30),(505,30),(620,155)]):s.node(i,x,y,210,66,n[i],'state')
        s.edge(0,'M235 63 H265');s.edge(1,'M475 63 H505');s.edge(2,'M715 96 V155','前面を離れる',805,135)
        s.edge(3,'M620 187 H555 V99','再び前面へ',455,177,True)
        s.text(250,224,'終了時のonDestroyは保証されない')
    elif kind=='decision':
        s.node(0,15,80,170,65,n[0],'state');s.node(1,245,62,230,100,'制約・保持条件','diamond')
        s.node(2,570,25,255,65,'条件成立 → 休止','state');s.node(3,570,158,255,65,'復帰 → 再確認','state')
        s.edge(0,'M185 112 H245');s.edge(1,'M475 112 H510 V57 H570','成立',515,26)
        s.edge(2,'M825 58 H866 V190 H825','復帰',842,126)
        s.edge(1,'M360 162 V200 H245 V163','不成立：動作を継続',255,229,True)
    elif kind in ('buffers','audio','deployment'):
        positions=[(10,78,180,85),(245,78,180,85),(480,78,180,85),(715,78,175,85)]
        if kind=='buffers':
            s.raw('<rect class="region" x="261" y="53" width="180" height="85" rx="8"/><rect class="region" x="253" y="65" width="180" height="85" rx="8"/>')
            labels=['アプリ|描画','Buffer|受渡し','SurfaceFlinger|合成','表示機器'];kinds=['component','file','component','device']
            s.text(450,220,'複数レイヤを合成し、表示タイミングと同期')
        elif kind=='audio':
            labels=n;kinds=['device' if chapter=='microphone' else 'component','component','component','component' if chapter=='microphone' else 'device']
            s.raw('<path class="wave" d="M60 40q12-20 24 0t24 0t24 0t24 0 M730 200q12-20 24 0t24 0t24 0t24 0"/>')
            s.text(450,224,'音声データの向き / 権限・Focus・経路の条件は別')
        else:
            labels=['ソース|設定','ビルド|対象','イメージ|配置','実機の|観測'];kinds=['file','component','file','device']
            s.text(450,222,'成果物の版・署名・配置先を実機と照合')
        for i,((x,y,w,h),label,k) in enumerate(zip(positions,labels,kinds)):
            s.node(i,x,y,w,h,label,k)
            if i<3:s.edge(i,f'M{x+w} 120 H{positions[i+1][0]}','PCM' if kind=='audio' and i==1 else '',450,104)
    elif kind in ('matrix','cockpit'):
        if kind=='cockpit':s.region(5,3,890,234,'AAOS / 同時に見る条件')
        positions=[(25,44),(475,44),(25,148),(475,148)]
        for i,(x,y) in enumerate(positions):s.node(i,x,y,400,72,n[i],'component')
        s.raw('<path class="divider" d="M450 48V220 M30 133H870"/>')
        s.text(450,28,'別々の軸を観測' if kind=='matrix' else 'CAR / 製品ポリシーに従う','region-label')
    elif kind=='tree':
        s.node(0,20,72,220,90,'AOSP|公開ソース','file');s.node(1,330,12,230,80,'端末の実装','component')
        s.node(2,330,148,230,80,'アプリ基盤','component');s.node(3,655,72,225,90,'利用する製品','device')
        s.edge(0,'M240 117 H280 V52 H330','',0,0);s.edge(0,'M280 117 V188 H330')
        s.edge(1,'M560 52 H610 V117 H655');s.edge(2,'M560 188 H610 V117')
        s.text(170,223,'Googleサービス一式とは別')
    elif kind=='timeline':
        s.raw('<path class="timeline-axis" d="M35 130 H865"/>')
        for i,x in enumerate([30,250,470,690]):
            s.node(i,x,35 if i%2==0 else 150,180,65,n[i].replace('ユーザーの解錠','ユーザー|解錠').replace('復帰 / 再接続','復帰 /|再接続'),'state')
            s.raw(f'<path class="lifeline" d="M{x+90} {90 if i%2==0 else 150} V130"/><circle class="time-tick" cx="{x+90}" cy="130" r="7"/>')
            if i<3:s.edge(i,f'M{x+100} 130 H{x+300}')
        s.text(450,28,'起動の代表例 / 全機能の準備とは別' if chapter=='boot' else '音楽アプリの場面 / 継続条件を確認','region-label')
    elif kind=='storage':
        s.region(15,12,405,215,'PROCESS / 一時状態');s.region(490,12,395,215,'PERSISTENT / 保存領域')
        s.node(0,35,58,165,75,'操作|入力','component');s.node(1,230,58,165,75,'処理中|状態','state')
        s.node(2,535,58,310,75,'Room / DataStore','db');s.node(3,35,160,360,55,'復元した状態','state')
        s.edge(0,'M200 96 H230');s.edge(1,'M395 96 H535','保存',463,81)
        s.edge(2,'M690 133 V187 H395','読み戻す',748,183,True)
        s.edge(3,'M35 187 H25 V96 H35','',0,0,True)
    elif kind in ('cycle','feedback'):
        positions=[(20,17),(485,17),(485,155),(20,155)]
        for i,(x,y) in enumerate(positions):s.node(i,x,y,395,68,n[i],'state' if kind=='cycle' else 'component')
        s.edge(0,'M415 51 H485','',0,0);s.edge(1,'M682 85 V155','更新' if chapter=='app-design' else '要求' if kind=='feedback' else '確認',780,127)
        s.edge(2,'M485 189 H415','',0,0);s.edge(3,'M217 155 V85','観測 / 見直し',110,126,True)
        s.text(450,126,'状態 → UI' if chapter=='app-design' else '要求と観測を区別','region-label')
    elif kind=='evidence':
        s.node(0,20,80,200,75,n[0],'file');s.node(1,325,12,240,70,n[1],'state')
        s.node(2,325,155,240,70,n[2],'file');s.node(3,670,80,210,75,n[3],'diamond')
        s.edge(0,'M220 117 H265 V47 H325');s.edge(0,'M265 117 V190 H325')
        s.edge(1,'M565 47 H620 V106 H683','期待',636,35);s.edge(2,'M565 190 H620 V136 H683','観測',635,220)
    elif kind=='trace':
        s.node(0,10,10,200,70,n[0],'file');s.node(1,10,157,200,70,n[1],'file')
        s.region(270,5,610,230,'TIME / 時刻で関連付ける')
        s.raw('<path class="timeline-axis" d="M295 122 H855"/><path class="lifeline" d="M470 44V222 M700 44V222"/>')
        s.node(2,320,55,225,55,n[2],'file');s.node(3,590,152,255,55,n[3],'file')
        s.edge(0,'M210 45 H250 V80 H320','操作',242,29);s.edge(1,'M210 192 H255 V182 H590','採取',260,219)
        s.edge(2,'M470 111 V135 H700 V151','照合',591,117,True)
    elif kind in ('boundary','hosts'):
        isadb=kind=='hosts';left='PC / 開発ホスト' if isadb else 'ANDROID / 公開側';right='DEVICE / 端末' if isadb else 'PRODUCT / 実装側'
        s.region(10,12,420,215,left);s.region(470,12,420,215,right)
        for i,(x,y) in enumerate([(30,76),(240,76),(490,76),(700,76)]):s.node(i,x,y,170,92,n[i],'component' if i<3 else 'device')
        for i,(a,b) in enumerate([(200,240),(410,490),(660,700)]):s.edge(i,f'M{a} 122 H{b}','接続' if isadb and i==1 else '',450,106)
        s.edge(3,'M785 168 V207 H115 V168','応答・状態の確認',450,199,True)
    elif kind=='network':
        s.region(15,15,260,210,'ANDROID / 選択したNetwork');s.region(680,15,205,210,'PEER / 通信相手')
        s.node(0,40,65,210,65,'リンク検出','device');s.node(1,40,150,210,55,'IPの設定','file')
        s.node(2,345,85,260,75,'経路 / DNS','component');s.node(3,700,85,170,75,'対象へ通信','device')
        s.edge(0,'M145 130 V150');s.edge(1,'M250 178 H300 V123 H345');s.edge(2,'M605 123 H700')
        s.text(475,215,'インターネット検証 ≠ ローカル到達性')
    elif kind=='partitions':
        s.node(0,15,67,180,100,'イメージ|成果物','file');s.region(270,8,345,222,'DEVICE / 配置領域の例')
        s.node(1,292,53,300,60,'パーティション','db');s.node(2,292,144,300,60,'マウント / 検証','component')
        s.node(3,695,67,190,100,'起動 / 更新','device')
        s.edge(0,'M195 117 H240 V83 H292','配置',237,59);s.edge(1,'M442 113 V144','対応',503,134)
        s.edge(2,'M592 174 H652 V117 H695','利用',650,202)
        s.text(450,230,'役割の対応 / 一方向の起動順ではない','region-label')
    else:raise AssertionError(kind)
    return s.finish(), LABELS[kind]
