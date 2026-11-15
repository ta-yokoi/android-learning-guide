"""Local-only, explicit backup/restore for Android learning records across web apps."""
HTML='''<details class="progress-transfer" id="progress-transfer"><summary>学習記録の引き継ぎ・バックアップ</summary><p>古いホーム画面版で記録を保存し、新しい「Android教材」で読み込めます。古いアイコンは、記録を確認するまで残してください。Safariとホーム画面版では記録が分かれる場合があります。</p><noscript><p>記録の保存・読込にはJavaScriptが必要です。教材本文はそのまま読めます。</p></noscript><div class="transfer-actions"><button type="button" id="progress-export" disabled>記録をファイルに保存</button><label for="progress-import">記録ファイルを読み込む</label><input id="progress-import" disabled type="file" accept="application/json,.json"></div><label class="transfer-overwrite"><input type="checkbox" id="progress-overwrite" disabled>この端末の再生位置も、ファイルの位置に変更する</label><p>読了記録は統合します。上のチェックを入れなければ、この端末に保存済みの再生位置を優先します。ファイルは端末内だけで処理し、外部へ送信しません。</p><p id="progress-transfer-status" role="status" aria-live="polite"></p></details>'''
CSS=r'''
.progress-transfer{margin:20px 0;padding:14px 17px;border:1px solid var(--line,#b9ccc4);border-radius:10px;font-size:12px;line-height:1.8;color:var(--muted,#496472);background:var(--paper,transparent)}.progress-transfer summary{cursor:pointer;font-weight:600;color:var(--accent,var(--teal,#176f64))}.progress-transfer p{max-width:850px}.transfer-actions{display:flex;gap:12px;align-items:center;flex-wrap:wrap}.transfer-actions button{font:inherit;cursor:pointer;background:#235a49;color:#fff;border:1px solid #658a7b;border-radius:6px;padding:9px 12px;min-height:40px}.transfer-actions input{font:inherit;max-width:100%;min-width:0;width:240px}.transfer-overwrite{display:flex;gap:7px;align-items:flex-start;margin:14px 0}.transfer-overwrite input{margin-top:5px}.progress-transfer :focus-visible{outline:3px solid #bc8d2d;outline-offset:3px}@media print{.progress-transfer{display:none}}
'''
JS=r'''
(()=>{'use strict';
 const root=document.getElementById('progress-transfer');if(!root)return;
 const status=root.querySelector('#progress-transfer-status'),fileInput=root.querySelector('#progress-import');
 root.querySelectorAll('button,input').forEach(el=>el.disabled=false);
 const normal='android16-learning-guide-completed-v1',overview='android-animated-slides-player-v1';
 const isKey=k=>k===normal||k===overview||/^android-deep-dive-[a-z0-9-]{1,64}-v1$/.test(k);
 function valid(k,v){if(k===normal)return Array.isArray(v)&&v.length<=200&&v.every(id=>typeof id==='string'&&/^[a-z0-9-]{1,64}$/.test(id));return v!==null&&typeof v==='object'&&!Array.isArray(v)&&Number.isInteger(v.slide)&&v.slide>=0&&v.slide<(k===overview?32:6)&&[.75,1,1.25,1.5,2].includes(v.rate)}
 function clean(k,v){return k===normal?[...new Set(v)]:{slide:v.slide,rate:v.rate}}
 function read(k){const raw=localStorage.getItem(k);if(raw===null)return null;try{const v=JSON.parse(raw);return valid(k,v)?v:null}catch(_){return null}}
 root.querySelector('#progress-export').addEventListener('click',()=>{
  try{const records=Object.create(null);for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(!isKey(k))continue;const v=read(k);if(v!==null)records[k]=clean(k,v)}const count=Object.keys(records).length;if(!count){status.textContent='この表示環境に保存されたAndroidの学習記録はありません。記録のある古いアイコンやSafariから開いて保存してください。';return}
   const blob=new Blob([JSON.stringify({schema:1,subject:'android-learning',createdAt:new Date().toISOString(),records},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download='android-learning-progress.json';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);status.textContent=count+'件の記録を保存します。保存先を確認し、新しい「Android教材」で読み込んでください。';
  }catch(_){status.textContent='この環境では記録を読み出せませんでした。教材の閲覧は続けられます。'}
 });
 fileInput.addEventListener('change',async()=>{
  const file=fileInput.files?.[0];if(!file)return;fileInput.disabled=true;status.textContent='ファイルを確認しています…';
  try{if(file.size>65536)throw Error('size');const data=JSON.parse(await file.text());if(data?.schema!==1||data.subject!=='android-learning'||!data.records||typeof data.records!=='object'||Array.isArray(data.records))throw Error('format');const entries=Object.entries(data.records);if(entries.length>100||entries.some(([k,v])=>!isKey(k)||!valid(k,v)))throw Error('format');const replace=root.querySelector('#progress-overwrite').checked,writes=[];let kept=0;
   for(const [k,incoming]of entries){const old=read(k);if(k===normal){writes.push([k,JSON.stringify([...new Set([...(old||[]),...incoming])])]);continue}if(old&&!replace){kept++;continue}writes.push([k,JSON.stringify(clean(k,incoming))])}
   const originals=writes.map(([k])=>[k,localStorage.getItem(k)]);try{for(const [k,v]of writes)localStorage.setItem(k,v)}catch(error){for(const [k,v]of originals){try{v===null?localStorage.removeItem(k):localStorage.setItem(k,v)}catch(_){}}throw error}
   status.textContent=writes.length+'件を読み込みました。'+(kept?kept+'件の保存済み再生位置は保持しました。':'')+'教材を開き直すと反映されます。';
  }catch(_){status.textContent='読み込めませんでした。Android学習記録のJSONファイルと、端末への保存許可を確認してください。'}finally{fileInput.value='';fileInput.disabled=false}
 });
})();
'''
