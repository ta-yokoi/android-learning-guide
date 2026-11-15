"""One Android Home Screen app shared by the guide, overview and focused courses."""
from android_progress_transfer import HTML as TRANSFER_HTML,CSS as TRANSFER_CSS,JS as TRANSFER_JS

def head_for(android_relative='..',player=True):
    p=android_relative
    return f'''<!-- android-home-app-head --><meta name="theme-color" content="#0a1521"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="{'black-translucent' if player else 'default'}"><meta name="apple-mobile-web-app-title" content="Android教材"><link rel="manifest" href="{p}/manifest.webmanifest"><link rel="apple-touch-icon" sizes="180x180" href="{p}/slides/icons/apple-touch-icon.png"><link rel="icon" type="image/png" sizes="192x192" href="{p}/slides/icons/icon-192.png"><!-- /android-home-app-head -->'''

def guide_for(android_relative='..'):
    home=android_relative+'/index.html'
    return f'''<details class="home-install" id="home-install"><summary>「Android教材」をホーム画面に追加する</summary><p>アイコン1つから、通常教材・簡易版スライド・詳細版の深掘り講座を選べます。Safariのタブバー・アドレスバーがないアプリ表示で起動します。</p><ol><li>iPhoneのSafariで<a href="{home}">Androidの共通入口</a>を開きます。</li><li>共有メニューから「ホーム画面に追加」を選びます。</li><li>「Webアプリとして開く」が表示された場合はオンにして、「Android教材」として追加します。</li><li>ホーム画面の「Android教材」アイコンから起動し、教材を選びます。動画は停止状態で開きます。</li></ol><p>以前の「Android学習」「Android深掘り」アイコンは自動統合されません。記録がある場合は、このページの「学習記録の引き継ぎ・バックアップ」でファイルに保存してから、新しいアプリで読み込んでください。全画面のときは「全画面を終了」で記録の操作を表示できます。記録を確認するまで古いアイコンは残してください。閲覧には通信が必要です。</p></details>'''
HEAD=head_for('..')
GUIDE=guide_for('..')
CSS=r'''
.home-install{margin:0 0 18px;padding:12px 16px;border:1px solid var(--line,#b9ccc4);border-radius:9px;font-size:12px;color:var(--muted,#496472);background:var(--paper,transparent)}.home-install summary{font-weight:600;color:var(--accent,var(--teal,#176f64))}.home-install ol{padding-left:22px;line-height:1.9}.home-install p{max-width:850px}.is-home-app .home-install{display:none}@media(display-mode:standalone){.home-install{display:none}}@media print{.home-install{display:none}}
'''+TRANSFER_CSS
JS=r'''
 const homeMode=matchMedia('(display-mode: standalone)');let homeLaunchApplied=false;
 function initHomeApp(){
  if(homeLaunchApplied||!(homeMode.matches||navigator.standalone===true))return;
  homeLaunchApplied=true;document.documentElement.classList.add('is-home-app');
  document.body.classList.add('immersive');fullState();
 }
 homeMode.addEventListener?.('change',initHomeApp);
'''
