(()=>{
  const isStandalone=()=>window.matchMedia('(display-mode: standalone)').matches||window.navigator.standalone===true;
  const isiOS=()=>/iphone|ipad|ipod/i.test(navigator.userAgent)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
  let deferredPrompt=null;

  function styles(){
    if(document.getElementById('pac-sales-install-style'))return;
    const s=document.createElement('style');
    s.id='pac-sales-install-style';
    s.textContent=`
      .pac-install-launcher{position:fixed;right:18px;bottom:18px;z-index:9998;border:0;border-radius:999px;background:#183f6b;color:#fff;padding:12px 16px;font:700 13px/1 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;box-shadow:0 10px 28px rgba(18,49,82,.24);cursor:pointer;display:flex;gap:8px;align-items:center}
      .pac-install-launcher:active{transform:translateY(1px)}
      .pac-install-overlay{position:fixed;inset:0;z-index:9999;background:rgba(11,29,49,.52);display:grid;place-items:end center;padding:18px}
      .pac-install-card{width:min(460px,100%);background:#fff;border-radius:20px;padding:22px;box-shadow:0 22px 80px rgba(0,0,0,.22);font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#183f6b}
      .pac-install-card h2{margin:0 0 8px;font-size:21px}.pac-install-card p{margin:0 0 16px;color:#60758d;line-height:1.55;font-size:14px}
      .pac-install-steps{display:grid;gap:10px;margin:14px 0 18px}.pac-install-step{display:flex;gap:11px;align-items:flex-start;background:#f5f8fc;border:1px solid #e4ebf4;border-radius:12px;padding:12px;font-size:14px;line-height:1.45}
      .pac-install-num{width:25px;height:25px;flex:0 0 25px;border-radius:50%;background:#e6effa;color:#285d91;display:grid;place-items:center;font-weight:800}
      .pac-install-actions{display:flex;gap:10px}.pac-install-actions button{min-height:44px;border-radius:11px;padding:0 15px;font-weight:700;cursor:pointer}
      .pac-install-close{border:1px solid #dce5ef;background:#fff;color:#49637f}.pac-install-native{border:0;background:#183f6b;color:#fff;flex:1}
      @media(min-width:900px){.pac-install-launcher{bottom:22px}} @media(max-width:600px){.pac-install-launcher{left:16px;right:16px;justify-content:center;bottom:calc(82px + env(safe-area-inset-bottom));font-size:14px}}
    `;
    document.head.appendChild(s);
  }

  function modal(nativePossible=false){
    document.querySelector('.pac-install-overlay')?.remove();
    const ios=isiOS();
    const overlay=document.createElement('div');
    overlay.className='pac-install-overlay';
    const card=document.createElement('div');
    card.className='pac-install-card';
    const steps=ios
      ? [
          ['Abrí esta página en Safari','Si estás dentro de WhatsApp, Instagram o Chrome, tocá Compartir y elegí “Abrir en Safari”.'],
          ['Tocá Compartir','Es el cuadrado con la flecha hacia arriba.'],
          ['Elegí “Agregar a pantalla de inicio”','Después tocá “Añadir”. Va a quedar como “PAC Ventas”.']
        ]
      : [
          ['Abrí el menú del navegador','En Chrome tocá los tres puntos ⋮.'],
          ['Elegí “Instalar app” o “Agregar a pantalla principal”','El nombre será “PAC Ventas”.']
        ];
    card.innerHTML=`<h2>Instalar acceso de Ventas</h2><p>Así queda un ícono en el inicio del celular y abre directamente este panel, sin ChatGPT.</p><div class="pac-install-steps">${steps.map((x,i)=>`<div class="pac-install-step"><span class="pac-install-num">${i+1}</span><div><strong>${x[0]}</strong><br>${x[1]}</div></div>`).join('')}</div><div class="pac-install-actions"><button class="pac-install-close" type="button">Cerrar</button>${nativePossible?'<button class="pac-install-native" type="button">Instalar ahora</button>':''}</div>`;
    overlay.appendChild(card);document.body.appendChild(overlay);
    card.querySelector('.pac-install-close').onclick=()=>overlay.remove();
    overlay.addEventListener('click',e=>{if(e.target===overlay)overlay.remove()});
    const native=card.querySelector('.pac-install-native');
    if(native)native.onclick=async()=>{if(!deferredPrompt)return;deferredPrompt.prompt();await deferredPrompt.userChoice;deferredPrompt=null;overlay.remove();refresh()};
  }

  function refresh(){
    document.querySelector('.pac-install-launcher')?.remove();
    if(isStandalone())return;
    styles();
    const b=document.createElement('button');
    b.type='button';b.className='pac-install-launcher';
    b.innerHTML='<span aria-hidden="true">⬇</span> Instalar acceso de Ventas';
    b.onclick=async()=>{
      if(deferredPrompt&&!isiOS()){deferredPrompt.prompt();await deferredPrompt.userChoice;deferredPrompt=null;refresh()}
      else modal(Boolean(deferredPrompt&&!isiOS()));
    };
    document.body.appendChild(b);
  }

  window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredPrompt=e;refresh()});
  window.addEventListener('appinstalled',()=>{deferredPrompt=null;refresh()});
  window.addEventListener('DOMContentLoaded',()=>{
    if('serviceWorker'in navigator)navigator.serviceWorker.register('/ventas/sw.js',{scope:'/ventas/'}).catch(()=>{});
    refresh();
  });
})();
