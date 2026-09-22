(()=>{
  const SUPABASE_URL='https://cgciwutqwnssdphugupq.supabase.co';
  const SUPABASE_KEY='sb_publishable_oozsLV8QMoy_ooLIqgh_qg_vvjV6IY5';
  const STORAGE_KEY='pac_sales_auth_v1';
  const API=SUPABASE_URL+'/functions/v1/patas-sales';
  const client=window.supabase?.createClient(SUPABASE_URL,SUPABASE_KEY,{auth:{storageKey:STORAGE_KEY,persistSession:true,autoRefreshToken:true,detectSessionInUrl:false}});
  if(!client)return;

  let isAdmin=false;
  let button=null;
  let busy=false;

  const icon=(enabled=false)=>enabled
    ? '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/><path d="m9 12 2 2 4-4"/></svg>'
    : '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>';

  function toast(message,error=false){
    document.querySelector('.pac-push-toast')?.remove();
    const el=document.createElement('div');
    el.className='pac-push-toast'+(error?' error':'');
    el.textContent=message;
    document.body.appendChild(el);
    setTimeout(()=>el.remove(),3600);
  }

  function styles(){
    if(document.getElementById('pac-push-style'))return;
    const s=document.createElement('style');
    s.id='pac-push-style';
    s.textContent=`
      .pac-push-button{position:relative}
      .pac-push-button.enabled{color:#20745d!important;background:#edf8f3!important}
      .pac-push-button.enabled:after{content:"";position:absolute;right:5px;top:5px;width:6px;height:6px;border-radius:50%;background:#2ca476;box-shadow:0 0 0 2px #fff}
      .pac-push-button.denied{opacity:.48}
      .pac-push-toast{position:fixed;z-index:10050;left:50%;bottom:24px;transform:translateX(-50%);max-width:min(420px,calc(100vw - 28px));background:#173f65;color:#fff;border-radius:12px;padding:11px 15px;font:700 13px/1.4 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;box-shadow:0 12px 35px rgba(15,46,74,.22)}
      .pac-push-toast.error{background:#9f3b38}
      @media(max-width:767px){.pac-push-toast{bottom:88px}}
    `;
    document.head.appendChild(s);
  }

  async function session(){
    return (await client.auth.getSession()).data.session;
  }

  async function api(action,data){
    const s=await session();
    if(!s)throw new Error('Iniciá sesión nuevamente.');
    const res=await fetch(API,{method:'POST',cache:'no-store',headers:{'Content-Type':'application/json',apikey:SUPABASE_KEY,Authorization:'Bearer '+s.access_token},body:JSON.stringify({action,data})});
    const body=await res.json().catch(()=>({}));
    if(!res.ok)throw new Error(body.error||'No pudimos completar la acción.');
    return body;
  }

  async function getViewer(){
    const s=await session();
    if(!s)return null;
    const res=await fetch(API,{cache:'no-store',headers:{apikey:SUPABASE_KEY,Authorization:'Bearer '+s.access_token}});
    if(!res.ok)return null;
    return res.json();
  }

  function toUint8(base64){
    const pad='='.repeat((4-base64.length%4)%4);
    const raw=atob((base64+pad).replace(/-/g,'+').replace(/_/g,'/'));
    return Uint8Array.from([...raw].map(c=>c.charCodeAt(0)));
  }

  async function currentSubscription(){
    if(!('serviceWorker'in navigator))return null;
    const reg=await navigator.serviceWorker.ready;
    return reg.pushManager.getSubscription();
  }

  async function syncExisting(){
    if(Notification.permission!=='granted')return;
    const sub=await currentSubscription();
    if(sub)await api('pushSubscribe',{subscription:sub.toJSON()});
  }

  async function enable(){
    if(busy)return;
    busy=true;
    try{
      if(!('serviceWorker'in navigator)||!('PushManager'in window)||!('Notification'in window))throw new Error('Este navegador no admite notificaciones push.');
      const ios=/iphone|ipad|ipod/i.test(navigator.userAgent)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
      const standalone=window.matchMedia('(display-mode: standalone)').matches||navigator.standalone===true;
      if(ios&&!standalone)throw new Error('En iPhone, primero agregá PAC Ventas a la pantalla de inicio y abrila desde el ícono.');
      let permission=Notification.permission;
      if(permission==='default')permission=await Notification.requestPermission();
      if(permission!=='granted')throw new Error('Las notificaciones quedaron bloqueadas. Podés habilitarlas desde los permisos del navegador.');
      const cfg=await api('pushConfig',{});
      const reg=await navigator.serviceWorker.ready;
      let sub=await reg.pushManager.getSubscription();
      if(!sub)sub=await reg.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:toUint8(cfg.publicKey)});
      await api('pushSubscribe',{subscription:sub.toJSON()});
      updateButton(true);
      toast('Notificaciones de pedidos activadas.');
    }catch(e){
      updateButton(false);
      toast(e.message||'No pudimos activar las notificaciones.',true);
    }finally{busy=false}
  }

  async function disable(){
    if(busy)return;
    const sub=await currentSubscription();
    if(!sub){updateButton(false);return}
    if(!confirm('¿Desactivar las notificaciones de pedidos en este dispositivo?'))return;
    busy=true;
    try{
      await api('pushUnsubscribe',{endpoint:sub.endpoint});
      await sub.unsubscribe();
      updateButton(false);
      toast('Notificaciones desactivadas en este dispositivo.');
    }catch(e){toast(e.message||'No pudimos desactivarlas.',true)}
    finally{busy=false}
  }

  function updateButton(enabled){
    if(!button)return;
    button.classList.toggle('enabled',enabled);
    button.classList.toggle('denied',Notification.permission==='denied');
    button.innerHTML=icon(enabled);
    button.title=enabled?'Notificaciones activas · tocar para desactivar':'Activar notificaciones de pedidos';
    button.setAttribute('aria-label',button.title);
  }

  async function inject(){
    if(!isAdmin)return;
    styles();
    const host=document.querySelector('.top-right');
    if(!host)return;
    if(document.querySelector('.pac-push-button')){button=document.querySelector('.pac-push-button');return}
    button=document.createElement('button');
    button.type='button';
    button.className='icon-button pac-push-button';
    host.prepend(button);
    let sub=null;
    try{sub=await currentSubscription()}catch{}
    updateButton(Boolean(sub&&Notification.permission==='granted'));
    button.addEventListener('click',async()=>{
      const active=await currentSubscription().catch(()=>null);
      if(active&&Notification.permission==='granted')disable(); else enable();
    });
  }

  async function init(){
    if(!('Notification'in window)||!('serviceWorker'in navigator))return;
    const data=await getViewer().catch(()=>null);
    isAdmin=Boolean(data?.viewer?.admin);
    if(!isAdmin)return;
    if(Notification.permission==='granted')syncExisting().catch(()=>{});
    const observer=new MutationObserver(()=>inject().catch(()=>{}));
    observer.observe(document.documentElement,{childList:true,subtree:true});
    inject().catch(()=>{});
    setTimeout(()=>observer.disconnect(),30000);
  }

  window.addEventListener('DOMContentLoaded',()=>setTimeout(init,300));
  client.auth.onAuthStateChange((event,s)=>{if(s&&event==='SIGNED_IN')setTimeout(init,500)});
})();