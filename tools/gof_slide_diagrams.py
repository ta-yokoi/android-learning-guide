"""Distinct teaching diagrams; arrow labels distinguish calls, references and transitions."""
from html import escape
from android_slide_diagrams import SVG

def relation(s,i,path,label,x,y):
    s.raw(f'<g class="edge" data-step="{i}"><path class="edge-path dashed" d="{path}" marker-end="url(#{s.prefix}-arrow)"/></g>')
    s.text(x,y,label,'edge-label')

def diagram(p,prefix):
    s=SVG(prefix);k=p['id'];labels=p['nodes']
    def node(i,x,y,w=205,h=68,label=None,kind='component'):
        s.node(i,x,y,w,h,label or labels[i],kind)
    def edge(i,path,label='',x=0,y=0):s.edge(i,path,label,x,y)
    if k=='abstract-factory':
        node(0,10,80);node(1,290,80);node(2,290,173,205,50)
        node(3,650,20,235,65,'Dark Button');node(3,650,150,235,65,'Dark Check')
        edge(0,'M215 114H290','利用',252,100)
        relation(s,2,'M392 173V148','実装',445,166)
        edge(3,'M495 98H550V52H650','button()',570,38);edge(3,'M495 131H550V182H650','check()',570,213)
        title='製品群：同じ工場から関連する二製品を得る'
    elif k=='factory-method':
        node(0,10,55,220);node(1,325,55,250);node(2,325,175,250,55);node(3,670,55,220)
        edge(1,'M230 89H325','呼出',275,75)
        relation(s,2,'M450 175V123','override',515,151)
        edge(3,'M575 89H670','生成',622,75)
        s.text(125,180,'共通手順は維持','annotation');title='生成フック：継承の差替えと製品生成を区別する'
    elif k=='prototype':
        node(0,15,35,240);node(1,340,35,225);node(2,650,35,230);node(3,340,162,350,62,'元 [base] / コピー [+urgent]')
        edge(1,'M255 69H340','呼出',298,55);edge(2,'M565 69H650','独立した複製',610,31)
        edge(3,'M765 103V195H690','コピーだけ変更',790,151)
        relation(s,0,'M135 103V195H340','元は不変',219,181);title='複製：可変のリストは共有せずコピーする'
    elif k=='singleton':
        node(0,12,75,220);node(1,330,35,255);node(2,330,160,255,62,'a == b → true');node(3,680,75,210)
        edge(1,'M232 109H280V69H330','取得',278,96);edge(3,'M680 109H630V69H585','取得',630,96)
        relation(s,2,'M457 103V160','同じ参照',530,139);title='共有参照：利用側が同じインスタンスを取得する'
    elif k=='bridge':
        s.region(5,5,420,228,'変化軸 A / 通知の種類');s.region(475,5,420,228,'変化軸 B / 送信経路')
        node(0,30,58,365,52,'Normal / Urgent');node(1,30,152,365,60,'Notice');node(2,500,58,365,52,'Channel 契約');node(3,500,152,365,60,'Mail / Sms')
        relation(s,0,'M210 110V152','通知側の継承',320,139);edge(2,'M395 180H450V84H500','委譲',450,153)
        relation(s,3,'M682 152V110','実装',739,139);title='二つの独立した変化軸を合成する'
    elif k=='composite':
        node(0,310,5,280,58);node(1,30,160,250,65);node(2,550,90,300,58);node(3,570,175,260,58)
        edge(1,'M350 63V115H155V160','size()',223,103);edge(2,'M550 63V90','size()',611,77);edge(3,'M700 148V175')
        s.text(380,213,'4 + 6 = 10','annotation');title='木構造：葉と枝が同じ契約で再帰的に集計する'
    elif k=='decorator':
        for i,label in enumerate(['呼出側','Logging|ラッパー','Upper|ラッパー','Mail 実体']):node(i,10+i*225,55,205,82,label)
        for i in range(3):edge(i+1,f'M{215+i*225} 86H{235+i*225}')
        s.text(450,28,'要求 → 外側から内側へ','annotation')
        relation(s,3,'M787 137V190H112V137','制御の復帰（戻り値なし）',450,219)
        title='入れ子：LOG ready → MAIL READY、逆順ならログも変化'
    elif k=='facade':
        node(0,10,80,180);node(1,260,80,210);node(2,545,20,330,65,'Stock.check → Payment.pay');node(3,545,153,330,65,'Shipping.ship')
        edge(1,'M190 114H260','入口',226,101);edge(2,'M470 98H510V52H545','1 → 2',524,25);edge(3,'M470 133H510V185H545','3',521,213)
        title='窓口：複数のサブシステムを利用目的でまとめる'
    elif k=='flyweight':
        node(0,10,18,250);node(1,340,75,230);node(2,650,75,235);node(3,10,165,250,60)
        edge(1,'M260 52H305V109H340','get(Serif)',302,40);edge(3,'M260 195H305V129H340','get(Serif)',302,221)
        edge(2,'M570 109H650','再利用',609,95);s.text(755,190,'font は共有 / x は引数','annotation')
        title='共有：不変な内部状態と、呼出時の外部状態を分ける'
    elif k=='proxy':
        node(0,10,65);node(1,310,65,255);node(2,310,175,255,50,'real == null ?');node(3,665,65,225)
        edge(1,'M215 99H310','read()',262,86);edge(3,'M565 99H665','委譲',615,86)
        relation(s,2,'M437 133V175','初回だけ生成',526,159);title='代理：実体の生成時点を読み出しまで遅らせる'
    elif k=='chain-of-responsibility':
        for i in range(4):node(i,10+i*225,65,205,85)
        for i in range(3):edge(i+1,f'M{215+i*225} 107H{235+i*225}')
        s.text(450,28,'処理できなければ次へ / 処理できれば停止','annotation');s.text(450,210,'600 → department / 2000 → rejected','annotation')
        title='連鎖：担当の選択と、未処理の終端を明示する'
    elif k=='command':
        node(0,10,25,250);node(1,335,25,230);node(2,650,25,235);node(3,335,175,230,53)
        edge(1,'M260 59H335','execute',297,46);edge(2,'M565 59H650','append',607,46)
        relation(s,3,'M135 93V201H335','履歴に保持',224,188);edge(3,'M565 201H767V93','undo → 元の長さ',708,175)
        title='要求のオブジェクト化：実行、履歴、受け手を分ける'
    elif k=='interpreter':
        node(0,15,20,250);node(1,350,20,250);node(2,210,165,285,62);node(3,570,165,305,62)
        edge(1,'M265 54H350','eval',310,42);edge(2,'M420 88V121H352V165','left',365,111);edge(3,'M530 88V121H722V165','right（短絡あり）',678,111)
        title='構文木：終端の判定と、複合式の評価を組み合わせる'
    elif k=='iterator':
        node(0,10,18,230);node(1,330,18,240);node(2,660,18,230)
        edge(1,'M240 52H330','iterator()',285,39);edge(2,'M570 52H660','独立した位置',615,39)
        for j,t in enumerate(['intro','finale','終端']):node(3,310+j*195,168,175,60,t,kind='file')
        edge(3,'M775 86V132H397V168','hasNext / next',560,122);title='走査：内部の配列を公開せず、位置を反復子が持つ'
    elif k=='mediator':
        node(0,10,75,230);node(1,335,75,230);node(2,335,175,230,50);node(3,660,75,230)
        edge(1,'M240 109H335','changed()',285,95);edge(3,'M565 109H660','状態更新',612,95)
        relation(s,2,'M450 143V175','ルールを集約',546,164);title='仲介：部品間の直接参照を減らし、協調ルールを集める'
    elif k=='memento':
        node(0,10,75,230);node(1,330,15,235);node(2,650,75,240);node(3,330,172,235,54)
        edge(1,'M240 92H280V49H330','保存',284,76);edge(2,'M565 49H615V109H650','保持だけ',614,76)
        edge(3,'M650 126H610V199H565','復元依頼',608,156);edge(3,'M330 199H125V143','状態を戻す',222,185)
        title='保存と復元：内部状態の扱いは所有者へ閉じ込める'
    elif k=='observer':
        node(0,10,75,210);node(1,290,75,215)
        node(2,630,8,260,50,'paid → mail');node(2,630,76,260,50,'paid → audit');node(3,630,171,260,58,'shipped →|audit のみ')
        edge(1,'M220 109H290','購読一覧',256,96);edge(2,'M505 92H560V33H630','今回の通知',552,27);edge(2,'M505 109H630')
        edge(3,'M505 131H560V200H630','mail 解除後',558,230)
        s.text(710,151,'例外の購読者は捕捉して継続','annotation');title='通知：解除前と解除後を分ける（順序・配送の保証ではない）'
    elif k=='state':
        node(0,10,5,260,53)
        for i,(x,label) in enumerate(zip([15,340,665],['Unpaid|未払い','Paid|支払い済み','Shipped|発送済み']),1):node(i,x,122,220,77,label,kind='state')
        edge(1,'M140 58V122','初期状態',220,91);edge(2,'M235 160H340','pay',287,144);edge(3,'M560 160H665','ship',612,144)
        s.text(450,227,'未払いで ship → 拒否 / 発送済みで ship → すでに発送済み','annotation');title='状態遷移：同じ操作の結果を、現在の状態が決める'
    elif k=='strategy':
        node(0,10,10,280,60);node(1,10,156,280,70);node(2,390,156,230,70);node(3,710,50,180,116,'Member|Regular')
        relation(s,0,'M150 70V156','方策を選んで注入',277,117);edge(2,'M290 191H390','計算を委譲',341,175)
        relation(s,3,'M710 132H665V191H620','実装',670,222);title='方策：選ぶ組立側と、実行を委譲するContextを区別する'
    elif k=='template-method':
        for i in range(4):node(i,10+i*225,70,205,75)
        for i in range(3):edge(i+1,f'M{215+i*225} 107H{235+i*225}')
        s.text(450,28,'親の手順：begin → body → end','annotation');relation(s,2,'M562 215V145','JsonExporter が body を override',565,232)
        title='固定手順：継承で差し替えるのは一部の操作だけ'
    elif k=='visitor':
        for x,label in [(135,'利用側'),(450,'Shape'),(765,'Visitor')]:
            s.text(x,25,label,'region-label');s.raw(f'<path class="lifeline" d="M{x} 36V231"/>')
        for i,(a,b,y,label) in enumerate([(135,450,68,'accept(describe)'),(450,765,118,'Circle → visit(Circle)'),(765,450,165,'円の説明を返す'),(450,765,217,'Rectangle → visit(Rectangle)')]):
            edge(i,f'M{a} {y}H{b}',label,(a+b)/2,y-10)
        title='二段階の呼出し：要素の型と訪問者に応じた処理を選ぶ'
    else:
        for i in range(4):node(i,10+i*225,65,205,85)
        for i in range(3):edge(i+1,f'M{215+i*225} 107H{235+i*225}')
        title='組立手順：操作の順と完成品を分ける'
    return s.finish(),title

def code_diagram(parts,prefix):
    return '<div class="code-sequence" tabindex="0" aria-label="Javaコードの抜粋。全体はスライドの下にあります">'+''.join(
        f'<section class="code-part role" data-step="{i}"><p>{i+1:02d} / {escape(label)}</p><pre><code>{escape(code)}</code></pre></section>'
        for i,(label,code) in enumerate(parts))+'</div>'
