"""Fullscreen stage and accessible, transient overlay controls (inlined at build time)."""
CSS=r'''
/* Fullscreen owns the entire viewport. Chrome is an overlay, never a layout row. */
.player.fullscreen-active{display:block;padding:0;width:100%;height:100vh;height:100dvh;border:0;border-radius:0;box-shadow:none;position:relative;background:#0a1521}
.immersive .player.fullscreen-active{position:fixed;inset:0}
.player.fullscreen-active .screen-wrap{position:absolute;inset:0;display:block;width:100%;height:100%;min-height:0}
.player.fullscreen-active .stage{width:100%;height:100%;aspect-ratio:auto;grid-template-rows:auto minmax(0,1fr) auto;gap:clamp(6px,1.2cqw,16px);padding:clamp(12px,2.5cqw,32px);padding-top:max(clamp(12px,2.5cqw,32px),env(safe-area-inset-top));padding-right:max(clamp(12px,2.5cqw,32px),env(safe-area-inset-right));padding-bottom:max(clamp(12px,2.5cqw,32px),env(safe-area-inset-bottom));padding-left:max(clamp(12px,2.5cqw,32px),env(safe-area-inset-left));border-radius:0}
.player.fullscreen-active .portrait-hint{display:none!important}
.player.fullscreen-active .controls{position:absolute;inset:auto 0 0;z-index:20;max-height:65%;overflow:auto;margin:0;border-top:1px solid #749b9955;background:linear-gradient(#0c1b2bf5,#091522fc);padding:10px max(14px,env(safe-area-inset-right)) max(10px,env(safe-area-inset-bottom)) max(14px,env(safe-area-inset-left));opacity:0;visibility:hidden;pointer-events:none;transform:translateY(8px);transition:opacity .18s ease,transform .18s ease,visibility .18s}
.player.fullscreen-active .slide-foot{position:absolute;z-index:20;left:max(14px,env(safe-area-inset-left));right:max(14px,env(safe-area-inset-right));bottom:calc(var(--controls-height,100px) + 8px);padding:7px 9px;border:1px solid #638a8c66;border-radius:8px;background:#0b1d2cf2;opacity:0;visibility:hidden;pointer-events:none;transition:opacity .18s ease,visibility .18s}
.player.fullscreen-active.controls-open .controls,.player.fullscreen-active.controls-open .slide-foot{opacity:1;visibility:visible;pointer-events:auto;transform:none}
.player.fullscreen-active:not(.controls-open){cursor:none}
.cinema-help{display:none}.hide-controls{display:none!important}
.player.fullscreen-active .cinema-help{display:block;margin:0 0 3px;color:#b3d0d2;font-size:10px;line-height:1.5}
.player.fullscreen-active .hide-controls{display:inline-block!important}
.player.fullscreen-active .cue-box{margin:0}.player.fullscreen-active .button-row{flex-wrap:wrap}
.player.fullscreen-active .opening{padding-bottom:max(38px,env(safe-area-inset-bottom))}
.player.fullscreen-active .phone-mock{width:min(80%,180px);height:auto;aspect-ratio:.57;max-height:100%}
.player.fullscreen-active .wave-display{max-height:180px}
@media(orientation:portrait){.player.fullscreen-active .chapter-picker{min-width:140px}}
@media(max-height:500px) and (orientation:landscape){.player.fullscreen-active .controls{padding-top:5px;padding-bottom:max(5px,env(safe-area-inset-bottom))}.player.fullscreen-active .cinema-help{font-size:9px}.player.fullscreen-active .slide-foot{bottom:calc(var(--controls-height,90px) + 5px);padding:4px 7px}.player.fullscreen-active .stage{gap:6px;padding-top:max(10px,env(safe-area-inset-top));padding-bottom:max(10px,env(safe-area-inset-bottom))}}
@media(prefers-reduced-motion:reduce){.player.fullscreen-active .controls,.player.fullscreen-active .slide-foot{transition:none}}
'''
JS=r'''
 let chromeTimer=0,wasFullscreen=false,movingChromeFocus=false;
 const chromeFoot=stage.querySelector('.slide-foot');
 function scheduleChrome(){clearTimeout(chromeTimer);if(isFull())chromeTimer=setTimeout(()=>hideChrome(),2600)}
 function showChrome(){if(!isFull())return;player.classList.add('controls-open');controls.inert=false;chromeFoot.inert=false;controls.removeAttribute('aria-hidden');chromeFoot.removeAttribute('aria-hidden');scheduleChrome()}
 function hideChrome(force=false){
  clearTimeout(chromeTimer);if(!isFull())return;
  const active=document.activeElement,inChrome=controls.contains(active)||chromeFoot.contains(active);
  if(!force&&inChrome&&active.matches(':focus-visible'))return;
  if(inChrome){movingChromeFocus=true;stage.focus({preventScroll:true});movingChromeFocus=false}
  clearTimeout(chromeTimer);player.classList.remove('controls-open');controls.inert=true;chromeFoot.inert=true;controls.setAttribute('aria-hidden','true');chromeFoot.setAttribute('aria-hidden','true');
 }
 function syncCinema(full){
  player.classList.toggle('fullscreen-active',full);
  if(full&&!wasFullscreen){wasFullscreen=true;stage.focus({preventScroll:true});showChrome();message('全画面表示です。タップかマウス移動、Tabキーで操作バーを表示できます。');return}
  if(!full){const exited=wasFullscreen;wasFullscreen=false;clearTimeout(chromeTimer);player.classList.remove('controls-open');controls.inert=false;chromeFoot.inert=false;controls.removeAttribute('aria-hidden');chromeFoot.removeAttribute('aria-hidden');player.style.removeProperty('--controls-height');if(exited)$('fullscreen').focus({preventScroll:true})}
 }
 player.addEventListener('pointermove',e=>{if(e.pointerType==='mouse'&&isFull())showChrome()});
 player.addEventListener('focusin',()=>{if(!movingChromeFocus&&isFull())showChrome()});
 player.addEventListener('focusout',()=>{if(isFull())scheduleChrome()});
 document.addEventListener('keydown',e=>{if(isFull()&&e.key!=='Escape')showChrome()},true);
 $('hide-controls').addEventListener('click',()=>hideChrome(true));
 window.addEventListener('pagehide',()=>clearTimeout(chromeTimer));
'''
