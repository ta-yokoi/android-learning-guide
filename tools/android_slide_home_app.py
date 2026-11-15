"""Home Screen metadata and launch behavior; no service worker or offline cache."""
HEAD='''<meta name="theme-color" content="#0a1521"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"><meta name="apple-mobile-web-app-title" content="Android学習"><link rel="manifest" href="./manifest.webmanifest"><link rel="apple-touch-icon" sizes="180x180" href="./icons/apple-touch-icon.png"><link rel="icon" type="image/png" sizes="192x192" href="./icons/icon-192.png">'''
GUIDE='''<details class="home-install" id="home-install"><summary>iPhoneでタブバーなしで開く</summary><p>このページをホーム画面に追加し、追加したアイコンから開いてください。Safariのタブバー・アドレスバーがないアプリ表示で起動します。</p><ol><li>iPhoneのSafariで、この教材ページを開きます。</li><li>共有メニューを開き、「ホーム画面に追加」を選びます。見つからない場合は共有メニュー内をスクロールしてください。</li><li>「Webアプリとして開く」のスイッチが表示された場合は、オンにして「追加」を押します。</li><li>Safariを離れ、ホーム画面の「Android学習」アイコンから起動します。横向きにすると図を大きく見られます。</li></ol><p>追加済みのアイコンでSafariが開く場合は、この最新ページから追加し直してください。起動時は停止しています。閲覧には通信が必要です。Safariとホーム画面版で学習記録が共有されない場合があります。</p></details>'''
CSS=r'''
.home-install{margin:0 0 18px;padding:12px 16px;border:1px solid var(--line);border-radius:9px;font-size:12px;color:var(--muted);background:var(--paper)}.home-install summary{font-weight:600;color:var(--accent)}.home-install ol{padding-left:22px;line-height:1.9}.home-install p{max-width:850px}.is-home-app .home-install{display:none}@media print{.home-install{display:none}}
'''
JS=r'''
 const homeMode=matchMedia('(display-mode: standalone)');let homeLaunchApplied=false;
 function initHomeApp(){
  if(homeLaunchApplied||!(homeMode.matches||navigator.standalone===true))return;
  homeLaunchApplied=true;document.documentElement.classList.add('is-home-app');
  // Installed apps already own their window. Do not request a user-gesture-only API.
  document.body.classList.add('immersive');fullState();
 }
 homeMode.addEventListener?.('change',initHomeApp);
'''
