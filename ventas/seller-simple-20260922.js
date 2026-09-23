(function sellerApp(){
  const SUPABASE_URL='https://cgciwutqwnssdphugupq.supabase.co';
  const SUPABASE_KEY='sb_publishable_oozsLV8QMoy_ooLIqgh_qg_vvjV6IY5';
  const ADMIN_BUNDLE='/ventas/assets/index-admin-20260921.js';
  const STORAGE_KEY='pac_sales_auth_v1';
  const models=['Circular grande · 31 mm','Circular chica · 25 mm','Cara de gato'];
  const colors=['Naranja','Celeste','Rosado','Negro','Blanco','Verde','Morado','Amarillo'];
  const colorHex={Naranja:'#ff8700',Celeste:'#78c9ef',Rosado:'#f2a5c2',Negro:'#1f2937',Blanco:'#ffffff',Verde:'#55b86d',Morado:'#8b5cf6',Amarillo:'#f4cf42'};
  const shopStates=['Pendiente','Interesado','Volver a visitar','Cliente','No interesado','Cerrado'];
  const visitResults=['Interesado','Hizo pedido','Volver a visitar','No interesado','Cerrado'];
  const orderStates=['Recibido','Confirmado','Preparado','Entregado','Cancelado'];
  const svgs={
    home:'<path d="M3 11.5 12 4l9 7.5"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/>',
    store:'<path d="M3 9l2-5h14l2 5"/><path d="M5 13v7h14v-7"/><path d="M3 9a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0"/><path d="M9 20v-5h6v5"/>',
    map:'<path d="m3 6 5-3 8 3 5-3v15l-5 3-8-3-5 3z"/><path d="M8 3v15M16 6v15"/>',
    pin:'<path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/>',
    clip:'<rect x="6" y="4" width="12" height="17" rx="2"/><path d="M9 4.5h6M9 9h6M9 13h6M9 17h4"/>',
    bag:'<path d="M6 8h12l1 12H5L6 8Z"/><path d="M9 9V6a3 3 0 0 1 6 0v3"/>',
    wallet:'<path d="M4 6h14a2 2 0 0 1 2 2v10H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h12"/><path d="M16 11h5v4h-5a2 2 0 0 1 0-4Z"/>',
    box:'<path d="m12 3 8 4-8 4-8-4 8-4Z"/><path d="m4 7 8 4 8-4v10l-8 4-8-4Z"/><path d="M12 11v10"/>',
    plus:'<path d="M12 5v14M5 12h14"/>',
    search:'<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    nav:'<path d="m3 11 18-8-8 18-2-8-8-2Z"/>',
    phone:'<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.2-1.2a2 2 0 0 1 2.1-.5c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.7 2Z"/>',
    calendar:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/>',
    chevron:'<path d="m9 18 6-6-6-6"/>',
    refresh:'<path d="M20 6v5h-5"/><path d="M4 18v-5h5"/><path d="M18.5 9a7 7 0 0 0-12-2L4 11M5.5 15a7 7 0 0 0 12 2L20 13"/>',
    logout:'<path d="M10 17l5-5-5-5M15 12H3"/><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>',
    menu:'<path d="M4 7h16M4 12h16M4 17h16"/>',
    x:'<path d="m6 6 12 12M18 6 6 18"/>',
    check:'<path d="m5 12 4 4L19 6"/>',
    clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    user:'<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    more:'<circle cx="5" cy="12" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="19" cy="12" r="1.5"/>'
  };
  const icon=(name,size=18)=>'<svg class="sp-svg" width="'+size+'" height="'+size+'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+(svgs[name]||svgs.more)+'</svg>';
  const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const money=n=>new Intl.NumberFormat('es-AR',{style:'currency',currency:'ARS',maximumFractionDigits:0}).format(Number(n)||0);
  const date=s=>s?new Date(s.includes('T')?s:s+'T12:00:00').toLocaleDateString('es-AR',{day:'2-digit',month:'short'}):'Sin fecha';
  const today=()=>new Date().toLocaleDateString('sv-SE',{timeZone:'America/Argentina/Mendoza'});
  const makeId=prefix=>prefix+Array.from(crypto.getRandomValues(new Uint8Array(8)),b=>b.toString(16).padStart(2,'0')).join('').toUpperCase();
  const mapCoords=s=>{const m=String(s?.map_url||'').match(/[?&]q=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)/);return m?{lat:Number(m[1]),lng:Number(m[2])}:null};
  const distanceKm=(a,b)=>{const R=6371,toRad=v=>v*Math.PI/180,dLat=toRad(b.lat-a.lat),dLng=toRad(b.lng-a.lng),x=Math.sin(dLat/2)**2+Math.cos(toRad(a.lat))*Math.cos(toRad(b.lat))*Math.sin(dLng/2)**2;return 2*R*Math.asin(Math.sqrt(x))};
  const supabase=window.supabase.createClient(SUPABASE_URL,SUPABASE_KEY,{auth:{storageKey:STORAGE_KEY,persistSession:true,autoRefreshToken:true,detectSessionInUrl:false}});
  let reactLoaded=false;
  function loadReact(){
    if(reactLoaded)return;
    reactLoaded=true;
    const s=document.createElement('script');
    s.type='module';s.src=ADMIN_BUNDLE;s.crossOrigin='anonymous';
    document.head.appendChild(s);
  }
  async function workspace(init={}){
    const {data:{session}}=await supabase.auth.getSession();
    if(!session)return new Response(JSON.stringify({error:'Iniciá sesión para entrar.'}),{status:401,headers:{'Content-Type':'application/json'}});
    return fetch(SUPABASE_URL+'/functions/v1/patas-sales',{...init,cache:'no-store',headers:{'Content-Type':'application/json',apikey:SUPABASE_KEY,Authorization:'Bearer '+session.access_token,...(init.headers||{})}});
  }
  async function boot(){
    const {data:{session}}=await supabase.auth.getSession();
    if(!session){
      supabase.auth.onAuthStateChange((event,next)=>{if(next&&event==='SIGNED_IN')setTimeout(()=>location.reload(),120)});
      const loginWatch=setInterval(()=>{try{const raw=localStorage.getItem(STORAGE_KEY)||'';if(raw.includes('access_token')){clearInterval(loginWatch);location.reload()}}catch{}},900);
      setTimeout(()=>clearInterval(loginWatch),15*60*1000);
      loadReact();return;
    }
    try{
      const r=await workspace();
      const data=await r.json();
      if(!r.ok||data?.viewer?.admin){loadReact();return}
      document.documentElement.classList.add('sp-seller-mode');
      startSeller(data);
    }catch{loadReact()}
  }
  function startSeller(initial){
    const root=document.getElementById('root');
    const state={data:initial,section:'home',query:'',filter:'',geo:null,geoLoading:false,drawer:false,modal:null,form:{},items:[],orderModel:models[0],newShop:false,busy:false};
    const shops=()=>state.data.shops||[];
    const visits=()=>state.data.visits||[];
    const orders=()=>state.data.orders||[];
    const payments=()=>state.data.payments||[];
    const commissions=()=>state.data.commissions||[];
    const kits=()=>state.data.kits||[];
    const settings=()=>state.data.settings||{price:7000};
    const shop=id=>shops().find(x=>x.id===id);
    const paid=o=>payments().filter(p=>p.order_id===o.id).reduce((a,p)=>a+Number(p.amount||0),0);
    const due=o=>o.status==='Cancelado'?0:Math.max(0,Number(o.total||0)-paid(o));
    const payState=o=>o.status==='Cancelado'?'Cancelado':paid(o)>=o.total?'Cobrado':paid(o)>0?'Parcial':'Pendiente';
    const commission=()=>{
      const sellerId=state.data.viewer.sellerId;
      const paidUnits=orders().filter(o=>o.seller_id===sellerId&&o.status!=='Cancelado'&&paid(o)>=o.total).reduce((a,o)=>a+Number(o.units||0),0);
      const earned=Math.floor(paidUnits/4)*7000;
      const already=commissions().filter(c=>c.seller_id===sellerId).reduce((a,c)=>a+Number(c.amount||0),0);
      return{units:paidUnits,earned,paid:already,due:earned-already,remainder:paidUnits%4};
    };
    const shopStats=id=>{
      const os=orders().filter(o=>o.shop_id===id&&o.status!=='Cancelado');
      return{orders:os.length,units:os.reduce((a,o)=>a+Number(o.units||0),0),sales:os.reduce((a,o)=>a+Number(o.total||0),0),last:os.slice().sort((a,b)=>String(b.created).localeCompare(String(a.created)))[0]};
    };
    const lastVisit=id=>visits().filter(v=>v.shop_id===id).sort((a,b)=>String(b.created).localeCompare(String(a.created)))[0];
    const directions=s=>s.map_url||('https://www.google.com/maps/dir/?api=1&destination='+encodeURIComponent(s.address||s.name));
    const whatsapp=s=>'https://wa.me/'+String(s.phone||'').replace(/\D/g,'');
    const shopDistance=s=>{if(!state.geo)return null;const p=mapCoords(s);return p?distanceKm(state.geo,p):null};
    const matchingShops=()=>{
      const q=state.query.trim().toLowerCase();
      const arr=shops().filter(s=>(!state.filter||s.status===state.filter)&&(!q||(s.name+' '+s.address+' '+s.zone+' '+s.contact).toLowerCase().includes(q)));
      return arr.sort((a,b)=>{const ad=a.next_visit&&a.next_visit<=today()?0:1,bd=b.next_visit&&b.next_visit<=today()?0:1;return ad-bd||String(a.next_visit||'9999').localeCompare(String(b.next_visit||'9999'))||String(a.name).localeCompare(String(b.name));});
    };
    const matchingOrders=()=>{
      const q=state.query.trim().toLowerCase();
      return orders().filter(o=>(!state.filter||o.status===state.filter)&&(!q||(o.id+' '+(shop(o.shop_id)?.name||'')).toLowerCase().includes(q))).sort((a,b)=>String(b.created).localeCompare(String(a.created)));
    };
    const attention=()=>shops().filter(s=>(s.next_visit&&s.next_visit<=today())||['Pendiente','Interesado','Volver a visitar'].includes(s.status)).sort((a,b)=>String(a.next_visit||'9999').localeCompare(String(b.next_visit||'9999')));
    const badge=value=>{
      const cls=['Cliente','Entregado','Cobrado','Hizo pedido'].includes(value)?'green':['Interesado','Preparado','Parcial','Volver a visitar'].includes(value)?'amber':['Cancelado','No interesado','Cerrado'].includes(value)?'gray':'blue';
      return '<span class="sp-badge '+cls+'">'+esc(value)+'</span>';
    };
    const toast=(msg,type='ok')=>{
      let el=document.querySelector('.sp-toast');
      if(!el){el=document.createElement('div');el.className='sp-toast';document.body.appendChild(el)}
      el.className='sp-toast '+type;el.textContent=msg;el.classList.add('show');
      clearTimeout(el._t);el._t=setTimeout(()=>el.classList.remove('show'),2600);
    };
    async function reload(){
      const r=await workspace();const j=await r.json();if(!r.ok)throw new Error(j.error||'No pudimos actualizar');state.data=j;
    }
    async function mutate(action,data){
      const r=await workspace({method:'POST',body:JSON.stringify({action,data})});const j=await r.json();if(!r.ok)throw new Error(j.error||'No pudimos guardar');await reload();return j;
    }
    function pageMeta(){
      return{
        home:['Mi jornada','Todo lo importante para vender hoy.'],
        shops:['Mis locales','Tu cartera, contactos, seguimientos y ventas en un solo lugar.'],
        routes:['Mi recorrido','Ordená visitas y llegá rápido a cada local.'],
        visits:['Mis visitas','Historial de conversaciones y próximos pasos.'],
        orders:['Mis pedidos','Estado, cobro y detalle de cada venta.'],
        money:['Mis números','Ventas, cobros y comisión sin cuentas manuales.'],
        material:['Mi material','Muestras y elementos que tenés asignados.']
      }[state.section]||['Ventas','Patas a Casa'];
    }
    function navButton(id,label,ico){
      return '<button class="sp-nav-btn '+(state.section===id?'active':'')+'" data-nav="'+id+'">'+icon(ico,18)+'<span>'+label+'</span></button>';
    }
    function renderShell(content){
      const meta=pageMeta();
      return '<div class="sp-app">'+
        '<aside class="sp-sidebar"><div class="sp-brand"><img src="/ventas/logo.svg" alt="Patas a Casa"><div><strong>Patas a Casa</strong><span>VENTAS</span></div></div><nav>'+
        navButton('home','Inicio','home')+navButton('shops','Locales','store')+navButton('routes','Recorrido','map')+navButton('visits','Visitas','clip')+navButton('orders','Pedidos','bag')+
        '</nav><div class="sp-sidebar-foot"><div class="sp-user"><span>'+esc((state.data.viewer.name||'V').slice(0,2).toUpperCase())+'</span><div><strong>'+esc(state.data.viewer.name||'Vendedor')+'</strong><small>Vendedor</small></div></div><button data-action="logout" class="sp-icon-btn" title="Cerrar sesión">'+icon('logout',18)+'</button></div></aside>'+
        '<main class="sp-main"><header class="sp-top"><button class="sp-mobile-menu" data-action="drawer">'+icon('menu',20)+'</button><div class="sp-top-title"><span>GESTIÓN COMERCIAL</span><strong>'+esc(meta[0])+'</strong></div><div class="sp-top-actions"><button class="sp-icon-btn" data-action="refresh" title="Actualizar">'+icon('refresh',18)+'</button><span class="sp-private">● Privado</span></div></header>'+
        '<div class="sp-content"><div class="sp-page-head"><div><span class="sp-eyebrow">PATAS A CASA · VENTAS</span><h1>'+esc(meta[0])+'</h1><p>'+esc(meta[1])+'</p></div><button class="sp-btn primary sp-desktop-cta" data-action="new-order">'+icon('plus',17)+' Nuevo pedido</button></div>'+content+'</div></main>'+
        renderBottom()+renderDrawer()+renderModal()+'</div>';
    }
    function renderBottom(){
      return '<nav class="sp-bottom"><button class="'+(state.section==='home'?'active':'')+'" data-nav="home">'+icon('home',19)+'<span>Inicio</span></button><button class="'+(state.section==='shops'?'active':'')+'" data-nav="shops">'+icon('store',19)+'<span>Locales</span></button><button class="sp-bottom-primary" data-action="new-order">'+icon('plus',23)+'<span>Pedido</span></button><button class="'+(state.section==='routes'?'active':'')+'" data-nav="routes">'+icon('map',19)+'<span>Recorrido</span></button><button class="'+(state.section==='orders'?'active':'')+'" data-nav="orders">'+icon('bag',19)+'<span>Pedidos</span></button></nav>';
    }
    function renderDrawer(){
      if(!state.drawer)return '';
      return '<div class="sp-drawer-backdrop" data-action="close-drawer"><aside class="sp-drawer" data-stop><div class="sp-drawer-head"><div class="sp-user"><span>'+esc((state.data.viewer.name||'V').slice(0,2).toUpperCase())+'</span><div><strong>'+esc(state.data.viewer.name||'Vendedor')+'</strong><small>Mi espacio de ventas</small></div></div><button class="sp-icon-btn" data-action="close-drawer">'+icon('x',20)+'</button></div><div class="sp-drawer-nav">'+navButton('visits','Historial de visitas','clip')+'</div><button class="sp-logout" data-action="logout">'+icon('logout',18)+' Cerrar sesión</button></aside></div>';
    }
    function kpi(title,value,detail,ico,tone,nav=''){
      return '<article class="sp-kpi '+tone+(nav?' clickable':'')+'"'+(nav?' data-nav="'+nav+'" role="button" tabindex="0" aria-label="'+esc(title)+': '+esc(value)+'. Ver detalle"':'')+'><div class="sp-kpi-top"><span>'+esc(title)+'</span><i>'+icon(ico,18)+'</i></div><strong>'+esc(value)+'</strong><small>'+esc(detail)+'</small>'+(nav?'<span class="sp-kpi-link">Ver detalle '+icon('chevron',13)+'</span>':'')+'</article>';
    }
    function quick(action,title,desc,ico,disabled){
      return '<button class="sp-quick" data-action="'+action+'" '+(disabled?'disabled':'')+'><i>'+icon(ico,20)+'</i><span><strong>'+esc(title)+'</strong><small>'+esc(desc)+'</small></span>'+icon('chevron',17)+'</button>';
    }
    function renderHome(){
      const active=orders().filter(o=>!['Entregado','Cancelado'].includes(o.status));
      const c=commission();
      const att=attention();
      const firstName=esc((state.data.viewer.name||'').split(' ')[0]||'vendedor');
      const hasShops=shops().length>0;
      let html='<section class="sp-welcome"><div><span class="sp-eyebrow light">MI JORNADA</span><h2>Hola, '+firstName+'</h2><p>'+(hasShops?'Tené a mano solo lo que necesitás para salir a vender.':'Empezá cargando el primer petshop que visites. El resto se ordena solo.')+'</p></div><div class="sp-welcome-actions"><button class="sp-btn white" data-action="new-shop">'+icon('store',17)+' '+(hasShops?'Nuevo local':'Cargar primer local')+'</button>'+(hasShops?'<button class="sp-btn orange" data-action="new-order">'+icon('bag',17)+' Nuevo pedido</button>':'')+'</div></section>';
      if(!hasShops){
        html+='<section class="sp-first-run"><div class="sp-first-run-copy"><span class="sp-tag">EMPEZAR</span><h2>Tu trabajo arranca con cada local que visitás</h2><p>No necesitás tener una base armada. Cargás el petshop cuando llegás y dejás marcado cómo quedó la conversación.</p></div><div class="sp-first-steps"><div><b>1</b><span><strong>Cargá el local</strong><small>Nombre y ubicación. Nada más es obligatorio.</small></span></div><div><b>2</b><span><strong>Marcá cómo quedó</strong><small>Interesado, volver a visitar, cliente o no interesado.</small></span></div><div><b>3</b><span><strong>Si compra, hacé el pedido</strong><small>Elegís tamaño, color y cantidad.</small></span></div></div><button class="sp-btn primary sp-first-cta" data-action="new-shop">'+icon('plus',17)+' Cargar primer local</button></section>';
        return html;
      }
      html+='<section class="sp-panel sp-attention"><div class="sp-panel-head"><div><span class="sp-tag">PARA HOY</span><h2>Qué tenés que atender</h2><p>Solo seguimientos y oportunidades que requieren una acción.</p></div><span class="sp-count">'+att.length+'</span></div>';
      if(att.length){
        html+='<div class="sp-attention-list">'+att.slice(0,3).map(s=>{
          const overdue=s.next_visit&&s.next_visit<=today();
          return '<div class="sp-attention-row"><i>'+icon('store',18)+'</i><div class="grow"><div class="sp-row-title"><button data-action="shop-detail" data-id="'+esc(s.id)+'">'+esc(s.name)+'</button>'+badge(s.status)+'</div><small>'+esc(s.zone||s.address||'Sin zona')+(s.next_visit?' · '+(overdue?'visita pendiente ':'próxima ')+date(s.next_visit):'')+'</small></div><div class="sp-row-actions">'+((s.map_url||s.address)?'<a class="sp-icon-btn" href="'+esc(directions(s))+'" target="_blank" rel="noreferrer" title="Cómo llegar">'+icon('nav',16)+'</a>':'')+'<button class="sp-btn secondary tiny" data-action="new-visit" data-id="'+esc(s.id)+'">Registrar visita</button><button class="sp-btn tiny" data-action="new-order" data-id="'+esc(s.id)+'">Pedido</button></div></div>';
        }).join('')+'</div>';
        if(att.length>3)html+='<button class="sp-home-more" data-nav="shops">Ver '+(att.length-3)+' seguimiento'+(att.length-3===1?'':'s')+' más '+icon('chevron',14)+'</button>';
      }else html+='<div class="sp-good">'+icon('check',21)+'<div><strong>Todo al día</strong><span>No tenés seguimientos pendientes ahora.</span></div></div>';
      html+='</section>';
      html+='<section class="sp-home-summary"><button data-nav="shops"><span>'+icon('store',17)+' Locales</span><strong>'+shops().length+'</strong></button><button data-nav="orders"><span>'+icon('bag',17)+' Pedidos activos</span><strong>'+active.length+'</strong></button><button data-nav="money"><span>'+icon('user',17)+' Mi comisión</span><strong>'+money(c.due)+'</strong></button></section>';
      return html;
    }
    function filters(kind){
      const statuses=kind==='orders'?orderStates:shopStates;
      return '<div class="sp-tools"><label class="sp-search">'+icon('search',17)+'<input data-search placeholder="'+(kind==='orders'?'Buscar pedido o comercio…':'Buscar local, zona o contacto…')+'" value="'+esc(state.query)+'"></label></div><div class="sp-chips"><button class="'+(!state.filter?'active':'')+'" data-filter="">Todos</button>'+statuses.filter(x=>x!=='Cancelado').map(x=>'<button class="'+(state.filter===x?'active':'')+'" data-filter="'+esc(x)+'">'+esc(x==='Volver a visitar'?'Volver':x)+'</button>').join('')+'</div>';
    }
    function renderShopCards(list,compact=false){
      if(!list.length)return '<div class="sp-empty">'+icon('store',28)+'<h3>No hay locales para mostrar</h3><p>Cambiá los filtros o cargá un local nuevo.</p><button class="sp-btn primary" data-action="new-shop">'+icon('plus',16)+' Nuevo local</button></div>';
      return '<div class="sp-shop-grid '+(compact?'compact':'')+'">'+list.map(s=>{
        const st=shopStats(s.id),last=lastVisit(s.id),overdue=!!s.next_visit&&s.next_visit<=today();
        return '<article class="sp-shop-card"><div class="sp-shop-head"><div class="sp-shop-title"><i>'+icon('store',19)+'</i><div><button data-action="shop-detail" data-id="'+esc(s.id)+'">'+esc(s.name)+'</button><small>'+icon('pin',12)+esc(s.zone||s.address||'Ubicación pendiente')+'</small></div></div>'+badge(s.status)+'</div><div class="sp-shop-metrics"><span><strong>'+st.orders+'</strong> pedidos</span><span><strong>'+st.units+'</strong> chapitas</span></div>'+(s.next_visit?'<div class="sp-next '+(overdue?'overdue':'')+'">'+icon('calendar',15)+'<span>'+(overdue?'Seguimiento pendiente':'Próxima visita')+' <strong>'+date(s.next_visit)+'</strong></span></div>':'<div class="sp-next neutral">'+icon('calendar',15)+'<span>Sin próxima visita</span></div>')+(last?'<div class="sp-last">'+icon('clock',13)+' Última visita: '+date(last.created)+' · '+esc(last.result)+'</div>':'')+(s.notes?'<p class="sp-note">'+esc(s.notes)+'</p>':'')+'<div class="sp-card-actions">'+((s.map_url||s.address)?'<a class="sp-btn secondary" href="'+esc(directions(s))+'" target="_blank" rel="noreferrer">'+icon('nav',15)+' Llegar</a>':'')+'<button class="sp-btn secondary" data-action="new-visit" data-id="'+esc(s.id)+'">'+icon('clip',15)+' Visita</button><button class="sp-btn primary" data-action="new-order" data-id="'+esc(s.id)+'">'+icon('bag',15)+' Pedido</button></div><button class="sp-card-foot" data-action="shop-detail" data-id="'+esc(s.id)+'">Ver ficha completa '+icon('chevron',15)+'</button></article>';
      }).join('')+'</div>';
    }
    function renderShops(){
      return filters('shops')+renderShopCards(matchingShops(),false);
    }
    function renderRoutes(){
      const list=matchingShops();
      let html='<section class="sp-route-hero"><div><span class="sp-eyebrow light">MI RECORRIDO</span><h2>Abrí el recorrido directamente en Google Maps</h2><p>Usamos tu ubicación y los locales guardados para armarte un recorrido. La lista de abajo queda solo como referencia.</p></div><button class="sp-btn orange" data-action="maps-route">'+icon('map',17)+' Abrir recorrido en Maps</button></section>'+filters('shops');
      if(!list.length)return html+'<div class="sp-empty">'+icon('map',28)+'<h3>No hay locales para mostrar</h3><p>Cargá un local o cambiá los filtros.</p></div>';
      html+='<div class="sp-route-list">'+list.map((s,i)=>{
        const st=shopStats(s.id),overdue=!!s.next_visit&&s.next_visit<=today();
        return '<article class="sp-route-card"><span class="sp-seq">'+(i+1)+'</span><div class="sp-route-main"><div class="sp-route-title"><div><button data-action="shop-detail" data-id="'+esc(s.id)+'">'+esc(s.name)+'</button><small>'+icon('pin',12)+esc(s.zone||s.address||'Ubicación pendiente')+'</small></div>'+badge(s.status)+'</div><div class="sp-pills">'+(s.next_visit?'<span class="'+(overdue?'overdue':'')+'">'+icon('calendar',13)+(overdue?' Pendiente ':' Visita ')+date(s.next_visit)+'</span>':'')+'<span>'+icon('bag',13)+' '+st.orders+' pedidos</span>'+(st.units?'<span>'+st.units+' chapitas</span>':'')+'</div>'+(s.notes?'<p>'+esc(s.notes)+'</p>':'')+'</div><div class="sp-route-actions">'+((s.map_url||s.address)?'<a class="sp-btn primary" href="'+esc(directions(s))+'" target="_blank" rel="noreferrer">'+icon('nav',16)+' Cómo llegar</a>':'<button class="sp-btn secondary" data-action="edit-shop" data-id="'+esc(s.id)+'">'+icon('pin',16)+' Ubicación</button>')+'<button class="sp-btn secondary" data-action="new-visit" data-id="'+esc(s.id)+'">'+icon('clip',16)+' Visita</button><button class="sp-btn secondary" data-action="new-order" data-id="'+esc(s.id)+'">'+icon('bag',16)+' Pedido</button></div></article>';
      }).join('')+'</div>';
      return html;
    }
    function renderVisits(){
      const q=state.query.trim().toLowerCase();
      const list=visits().filter(v=>!q||((shop(v.shop_id)?.name||'')+' '+v.notes).toLowerCase().includes(q)).sort((a,b)=>String(b.created).localeCompare(String(a.created)));
      let html='<div class="sp-tools"><label class="sp-search">'+icon('search',17)+'<input data-search placeholder="Buscar comercio o nota…" value="'+esc(state.query)+'"></label><button class="sp-btn primary" data-action="new-visit">'+icon('plus',16)+' Registrar visita</button></div><section class="sp-panel sp-visits"><div class="sp-panel-head"><div><h2>Historial de visitas</h2><p>Qué hablaste y cuál es el próximo paso.</p></div><span class="sp-count">'+list.length+'</span></div><div class="sp-timeline">';
      if(!list.length)html+='<div class="sp-empty">'+icon('clip',28)+'<h3>Todavía no registraste visitas</h3><p>Cuando salgas de un comercio, anotá qué pasó.</p></div>';
      else html+=list.map(v=>{const s=shop(v.shop_id);return '<article class="sp-visit"><span class="sp-dot"></span><div><div class="sp-visit-title"><div><button data-action="shop-detail" data-id="'+esc(v.shop_id)+'">'+esc(s?.name||v.shop_id)+'</button><small>'+date(v.created)+' · '+esc(s?.zone||s?.address||'Sin zona')+'</small></div>'+badge(v.result)+'</div><p>'+esc(v.notes||'Sin observaciones.')+'</p>'+(v.next_visit?'<div class="sp-next '+(v.next_visit<=today()?'overdue':'')+'">'+icon('calendar',14)+' Volver: <strong>'+date(v.next_visit)+'</strong></div>':'')+'<div class="sp-text-actions">'+(s&&(s.map_url||s.address)?'<a href="'+esc(directions(s))+'" target="_blank" rel="noreferrer">'+icon('nav',14)+' Cómo llegar</a>':'')+(s?'<button data-action="new-order" data-id="'+esc(s.id)+'">'+icon('bag',14)+' Nuevo pedido</button><button data-action="new-visit" data-id="'+esc(s.id)+'">'+icon('clip',14)+' Nueva visita</button>':'')+'</div></div></article>'}).join('');
      return html+'</div></section>';
    }
    function renderOrders(){
      const list=matchingOrders();
      let html=filters('orders');
      if(!list.length)return html+'<div class="sp-empty">'+icon('bag',28)+'<h3>'+(orders().length?'No hay pedidos con esos filtros':'Listo para tu primera venta')+'</h3><p>Elegí el comercio, tipo y color. El total se calcula solo.</p><button class="sp-btn primary" data-action="new-order">'+icon('plus',16)+' Nuevo pedido</button></div>';
      html+='<div class="sp-order-grid">'+list.map(o=>{const s=shop(o.shop_id);return '<article class="sp-order-card"><div class="sp-order-head"><div><button data-action="order-detail" data-id="'+esc(o.id)+'">'+esc(s?.name||o.shop_id)+'</button><small>'+esc(o.id)+' · '+date(o.created)+'</small></div><strong>'+money(o.total)+'</strong></div><div class="sp-order-status"><span><small>Preparación</small>'+badge(o.status)+'</span><span><small>Cobro</small>'+badge(payState(o))+'</span><span><small>Entrega</small><b>'+date(o.delivery)+'</b></span></div><div class="sp-item-pills">'+(o.items||[]).slice(0,3).map(i=>'<span><i style="background:'+esc(colorHex[i.color]||'#ccc')+'"></i><b>'+esc(i.quantity)+'</b> '+esc(i.model.startsWith('Circular grande')?'grandes':i.model.startsWith('Circular chica')?'chicas':'gato')+' '+esc(String(i.color).toLowerCase())+'</span>').join('')+((o.items||[]).length>3?'<span>+'+((o.items||[]).length-3)+' líneas</span>':'')+'</div><div class="sp-order-summary"><span><small>Chapitas</small><strong>'+esc(o.units)+'</strong></span><span><small>Cobrado</small><strong>'+money(paid(o))+'</strong></span><span><small>Pendiente</small><strong>'+money(due(o))+'</strong></span></div><div class="sp-card-actions three"><button class="sp-btn secondary" data-action="order-detail" data-id="'+esc(o.id)+'">Ver detalle</button>'+(s&&(s.map_url||s.address)?'<a class="sp-btn secondary" href="'+esc(directions(s))+'" target="_blank" rel="noreferrer">'+icon('nav',15)+' Llegar</a>':'')+(s?'<button class="sp-btn primary" data-action="new-order" data-id="'+esc(s.id)+'">'+icon('plus',15)+' Otro pedido</button>':'')+'</div></article>'}).join('')+'</div>';
      return html;
    }
    function renderMoney(){
      const valid=orders().filter(o=>o.status!=='Cancelado'),sales=valid.reduce((a,o)=>a+Number(o.total||0),0),collected=payments().reduce((a,p)=>a+Number(p.amount||0),0),c=commission(),pending=orders().filter(o=>due(o)>0);
      let html='<div class="sp-kpis">'+kpi('Vendido',money(sales),valid.length+' pedidos válidos','bag','blue')+kpi('Cobrado',money(collected),payments().length+' pagos registrados','check','teal')+kpi('Falta cobrar',money(pending.reduce((a,o)=>a+due(o),0)),pending.length+' pedidos con saldo','wallet','orange')+kpi('Mi comisión',money(c.due),'Pendiente de pago','user','purple')+'</div>';
      html+='<section class="sp-panel sp-commission"><div class="sp-commission-main"><div><span class="sp-tag">MI COMISIÓN</span><h2>'+money(c.due)+' <small>pendiente</small></h2><p>Se generan $7.000 por cada 4 chapitas de pedidos cobrados por completo.</p></div><div class="sp-progress-box"><strong>'+c.remainder+'/4</strong><span>hacia el próximo grupo</span></div></div><div class="sp-progress"><span style="width:'+(c.remainder/4*100)+'%"></span></div><div class="sp-commission-grid"><span><small>Chapitas cobradas</small><strong>'+c.units+'</strong></span><span><small>Generado</small><strong>'+money(c.earned)+'</strong></span><span><small>Ya abonado</small><strong>'+money(c.paid)+'</strong></span><span><small>Faltan para otros $7.000</small><strong>'+(c.remainder===0?4:4-c.remainder)+'</strong></span></div></section>';
      html+='<section class="sp-panel sp-spaced"><div class="sp-panel-head"><div><h2>Pedidos con saldo</h2><p>Lo que administración todavía tiene pendiente de registrar como cobrado.</p></div><span class="sp-count">'+pending.length+'</span></div>';
      if(pending.length)html+='<div class="sp-balance-list">'+pending.map(o=>'<button class="sp-balance" data-action="order-detail" data-id="'+esc(o.id)+'"><i>'+icon('wallet',17)+'</i><span class="grow"><strong>'+esc(shop(o.shop_id)?.name||o.shop_id)+'</strong><small>'+esc(o.id)+' · cobrado '+money(paid(o))+' de '+money(o.total)+'</small></span><span><small>Pendiente</small><strong>'+money(due(o))+'</strong></span>'+icon('chevron',15)+'</button>').join('')+'</div>';
      else html+='<div class="sp-good">'+icon('check',21)+'<div><strong>Todo cobrado</strong><span>No tenés pedidos con saldo pendiente.</span></div></div>';
      html+='</section><section class="sp-panel sp-spaced"><div class="sp-panel-head"><div><h2>Mis movimientos</h2><p>Cobros de tus ventas y pagos de comisión.</p></div></div><div class="sp-movements">';
      const moves=[...payments().map(p=>({...p,kind:'Cobro',name:shop(orders().find(o=>o.id===p.order_id)?.shop_id)?.name||p.order_id})),...commissions().map(c=>({...c,kind:'Comisión',name:'Comisión abonada'}))].sort((a,b)=>String(b.created).localeCompare(String(a.created)));
      html+=moves.length?moves.map(m=>'<div class="sp-movement"><i>'+icon('wallet',17)+'</i><div class="grow"><strong>'+esc(m.kind)+' · '+esc(m.name)+'</strong><small>'+date(m.created)+(m.reference?' · '+esc(m.reference):'')+'</small></div><strong>'+money(m.amount)+'</strong></div>').join(''):'<div class="sp-empty small"><p>Todavía no hay movimientos registrados.</p></div>';
      return html+'</div></section>';
    }
    function renderMaterial(){
      const list=kits();
      if(!list.length)return '<div class="sp-empty">'+icon('box',30)+'<h3>No tenés material asignado</h3><p>Cuando administración te entregue muestras, tarjetas o packaging aparecerán acá.</p></div>';
      return '<div class="sp-material-grid">'+list.map(k=>'<article class="sp-material-card"><i>'+icon('box',22)+'</i><div><strong>'+esc(k.description)+'</strong><small>Entregado '+date(k.created)+'</small></div><span><strong>'+esc(k.quantity)+'</strong><small>cantidad</small></span><b class="'+(Number(k.returned)>=Number(k.quantity)?'done':'')+'">'+(Number(k.returned)>=Number(k.quantity)?'Devuelto':'En tu poder')+'</b></article>').join('')+'</div>';
    }
    function renderPage(){
      state.query=state.query||'';
      let content='';
      if(state.section==='home')content=renderHome();
      else if(state.section==='shops')content=renderShops();
      else if(state.section==='routes')content=renderRoutes();
      else if(state.section==='visits')content=renderVisits();
      else if(state.section==='orders')content=renderOrders();
      else if(state.section==='money')content=renderMoney();
      else if(state.section==='material')content=renderMaterial();
      return renderShell(content);
    }
    function renderModal(){
      if(!state.modal)return '';
      const close='<button class="sp-modal-close" type="button" data-action="close-modal">'+icon('x',20)+'</button>';
      if(state.modal==='shop-detail'){
        const s=shop(state.form.id),st=s?shopStats(s.id):null,last=s?lastVisit(s.id):null;
        if(!s)return '';
        return '<div class="sp-modal-backdrop" data-action="close-modal"><div class="sp-modal sp-detail-modal" data-stop><div class="sp-modal-head"><div><span class="sp-tag">COMERCIO</span><h2>'+esc(s.name)+'</h2></div>'+close+'</div><div class="sp-detail-status">'+badge(s.status)+(s.next_visit?'<span>'+icon('calendar',14)+' Próxima visita '+date(s.next_visit)+'</span>':'')+'</div><div class="sp-detail-kpis"><span><small>Pedidos</small><strong>'+st.orders+'</strong></span><span><small>Chapitas</small><strong>'+st.units+'</strong></span><span><small>Vendido</small><strong>'+money(st.sales)+'</strong></span></div><dl class="sp-detail-list"><dt>Zona</dt><dd>'+esc(s.zone||'Sin zona')+'</dd><dt>Dirección</dt><dd>'+esc(s.address||'Sin dirección')+'</dd><dt>Contacto</dt><dd>'+esc(s.contact||'Sin contacto')+'</dd><dt>WhatsApp</dt><dd>'+esc(s.phone||'Sin teléfono')+'</dd>'+(last?'<dt>Última visita</dt><dd>'+date(last.created)+' · '+esc(last.result)+'</dd>':'')+'</dl>'+(s.notes?'<div class="sp-detail-note">'+esc(s.notes)+'</div>':'')+'<div class="sp-detail-actions">'+((s.map_url||s.address)?'<a class="sp-btn secondary" href="'+esc(directions(s))+'" target="_blank" rel="noreferrer">'+icon('nav',16)+' Cómo llegar</a>':'')+(s.phone?'<a class="sp-btn secondary" href="'+esc(whatsapp(s))+'" target="_blank" rel="noreferrer">'+icon('phone',16)+' WhatsApp</a>':'')+'<button class="sp-btn secondary" data-action="edit-shop" data-id="'+esc(s.id)+'">Editar</button><button class="sp-btn secondary" data-action="new-visit" data-id="'+esc(s.id)+'">Registrar visita</button><button class="sp-btn primary" data-action="new-order" data-id="'+esc(s.id)+'">'+icon('bag',16)+' Nuevo pedido</button></div></div></div>';
      }
      if(state.modal==='order-detail'){
        const o=orders().find(x=>x.id===state.form.id),s=o?shop(o.shop_id):null;if(!o)return '';
        return '<div class="sp-modal-backdrop" data-action="close-modal"><div class="sp-modal sp-detail-modal" data-stop><div class="sp-modal-head"><div><span class="sp-tag">PEDIDO</span><h2>'+esc(s?.name||o.shop_id)+'</h2><p>'+esc(o.id)+' · '+date(o.created)+'</p></div>'+close+'</div><div class="sp-detail-status">'+badge(o.status)+badge(payState(o))+'</div><div class="sp-detail-lines">'+(o.items||[]).map(i=>'<div><span><i style="background:'+esc(colorHex[i.color]||'#ccc')+'"></i><strong>'+esc(i.model)+'</strong><small>'+esc(i.color)+' · '+esc(i.quantity)+' × '+money(i.price)+'</small></span><strong>'+money(Number(i.quantity)*Number(i.price))+'</strong></div>').join('')+'</div><div class="sp-order-total"><span>Total <strong>'+money(o.total)+'</strong></span><span>Cobrado <strong>'+money(paid(o))+'</strong></span><span>Pendiente <strong>'+money(due(o))+'</strong></span></div>'+(o.delivery?'<p class="sp-detail-inline">'+icon('calendar',15)+' Entrega solicitada: '+date(o.delivery)+'</p>':'')+(o.notes?'<div class="sp-detail-note">'+esc(o.notes)+'</div>':'')+'<div class="sp-detail-actions"><button class="sp-btn secondary" data-action="close-modal">Cerrar</button>'+(s&&(s.map_url||s.address)?'<a class="sp-btn secondary" href="'+esc(directions(s))+'" target="_blank" rel="noreferrer">'+icon('nav',16)+' Cómo llegar</a>':'')+(s?'<button class="sp-btn primary" data-action="new-order" data-id="'+esc(s.id)+'">'+icon('plus',16)+' Otro pedido</button>':'')+'</div></div></div>';
      }
      if(state.modal==='shop'){
        const f=state.form;
        return '<div class="sp-modal-backdrop"><div class="sp-modal" data-stop><div class="sp-modal-head"><div><span class="sp-tag">LOCAL</span><h2>'+(f.id?'Editar local':'Nuevo local')+'</h2><p>Cargá lo básico y dejá marcado cómo quedó la visita.</p></div>'+close+'</div><form class="sp-form" data-form="shop"><div class="sp-form-grid"><label class="wide"><span>Nombre del local *</span><input required minlength="2" name="name" data-field="name" value="'+esc(f.name||'')+'" placeholder="Ej.: Mundo Mascota"></label><label><span>Zona o barrio</span><input name="zone" data-field="zone" value="'+esc(f.zone||'')+'" placeholder="Ej.: Godoy Cruz"></label><div class="wide sp-status-field"><span class="sp-field-label">¿Cómo quedó este local?</span><div class="sp-status-choices">'+shopStates.filter(x=>x!=='Cerrado'||f.id).map(x=>'<label class="'+((f.status||'Pendiente')===x?'selected':'')+'"><input type="radio" name="status" data-field="status" value="'+esc(x)+'" '+((f.status||'Pendiente')===x?'checked':'')+'><span>'+esc(x==='Pendiente'?'Solo cargado':x==='Volver a visitar'?'Volver a visitar':x)+'</span></label>').join('')+'</div><small>Marcá el resultado real de la visita. Después lo podés cambiar.</small></div><label class="wide"><span>Dirección</span><input name="address" data-field="address" value="'+esc(f.address||'')+'" placeholder="Calle, número o referencia"></label><div class="sp-geo wide"><button type="button" class="sp-btn secondary" data-action="capture-shop-location">'+icon('pin',16)+(f.map_url?' Actualizar ubicación':' Usar mi ubicación actual')+'</button><small>'+(f.map_url?'✓ Ubicación guardada':'Ideal si estás parado en el local.')+'</small></div><label><span>Persona de contacto</span><input name="contact" data-field="contact" value="'+esc(f.contact||'')+'" placeholder="Nombre del encargado"></label><label><span>WhatsApp</span><input name="phone" data-field="phone" value="'+esc(f.phone||'')+'" inputmode="tel" placeholder="549261…"></label><label><span>Próxima visita</span><input type="date" name="next_visit" data-field="next_visit" value="'+esc(f.next_visit||'')+'"></label><label class="wide"><span>Notas</span><textarea name="notes" data-field="notes" rows="3" placeholder="Horario, qué le interesa, con quién hablar…">'+esc(f.notes||'')+'</textarea></label></div><div class="sp-form-actions"><button type="button" class="sp-btn secondary" data-action="close-modal">Cancelar</button><button class="sp-btn primary" type="submit" '+(state.busy?'disabled':'')+'>'+(state.busy?'Guardando…':'Guardar local')+'</button></div></form></div></div>';
      }
      if(state.modal==='visit'){
        const f=state.form;
        return '<div class="sp-modal-backdrop"><div class="sp-modal" data-stop><div class="sp-modal-head"><div><span class="sp-tag">VISITA</span><h2>Registrar visita</h2><p>Dejá el próximo paso listo antes de irte.</p></div>'+close+'</div><form class="sp-form" data-form="visit"><div class="sp-form-grid"><label class="wide"><span>Comercio *</span><select required name="shop_id" data-field="shop_id"><option value="">Seleccioná un local</option>'+shops().map(s=>'<option value="'+esc(s.id)+'" '+(f.shop_id===s.id?'selected':'')+'>'+esc(s.name)+'</option>').join('')+'</select></label><label><span>Resultado *</span><select name="result" data-field="result">'+visitResults.map(x=>'<option '+((f.result||'Interesado')===x?'selected':'')+'>'+esc(x)+'</option>').join('')+'</select></label><label><span>Volver a visitar</span><input type="date" name="next_visit" data-field="next_visit" value="'+esc(f.next_visit||'')+'"></label><label class="wide"><span>¿Qué conversaron?</span><textarea name="notes" data-field="notes" rows="5" placeholder="Con quién hablaste, qué pidió y cuál es el próximo paso…">'+esc(f.notes||'')+'</textarea></label></div><div class="sp-form-actions"><button type="button" class="sp-btn secondary" data-action="close-modal">Cancelar</button><button class="sp-btn primary" type="submit" '+(state.busy?'disabled':'')+'>'+(state.busy?'Guardando…':'Guardar visita')+'</button></div></form></div></div>';
      }
      if(state.modal==='order'){
        const f=state.form,total=state.items.reduce((a,i)=>a+i.quantity*i.price,0),units=state.items.reduce((a,i)=>a+i.quantity,0);
        return '<div class="sp-modal-backdrop"><div class="sp-modal sp-order-modal" data-stop><div class="sp-modal-head"><div><span class="sp-tag">PEDIDO</span><h2>Nuevo pedido</h2><p>Elegí local, tipo y color. El total se arma solo.</p></div>'+close+'</div><form class="sp-form" data-form="order"><section class="sp-order-shop"><div class="sp-between"><strong>Local del pedido</strong>'+(shops().length?'<button type="button" class="sp-link" data-action="toggle-new-shop">'+(state.newShop?'Elegir existente':'¿No está? Crear local')+'</button>':'')+'</div>'+(state.newShop?'<div class="sp-form-grid"><label><span>Nombre del local *</span><input required minlength="2" data-field="new_shop_name" value="'+esc(f.new_shop_name||'')+'" placeholder="Ej.: Mundo Mascota"></label><label><span>Zona</span><input data-field="new_shop_zone" value="'+esc(f.new_shop_zone||'')+'" placeholder="Godoy Cruz"></label><label class="wide"><span>Dirección</span><input data-field="new_shop_address" value="'+esc(f.new_shop_address||'')+'" placeholder="Opcional"></label><div class="sp-geo wide"><button type="button" class="sp-btn secondary" data-action="capture-new-location">'+icon('pin',16)+(f.new_shop_map_url?' Actualizar ubicación':' Guardar ubicación de este local')+'</button><small>'+(f.new_shop_map_url?'✓ Ubicación lista':'Ideal si estás parado en el comercio.')+'</small></div></div>':'<label class="sp-select-only"><select required data-field="shop_id"><option value="">Seleccioná un local</option>'+shops().map(s=>'<option value="'+esc(s.id)+'" '+(f.shop_id===s.id?'selected':'')+'>'+esc(s.name)+'</option>').join('')+'</select></label>')+'</section><section class="sp-picker"><div class="sp-picker-head"><div><span class="sp-tag">ARMAR PEDIDO</span><strong>Elegí tipo y color</strong></div><small>Tocá un color para sumar una chapita.</small></div><div class="sp-model-tabs">'+models.map(m=>'<button type="button" class="'+(state.orderModel===m?'active':'')+'" data-model="'+esc(m)+'">'+esc(m.startsWith('Circular grande')?'Grandes':m.startsWith('Circular chica')?'Chicas':'Gatos')+'</button>').join('')+'</div><div class="sp-color-grid">'+colors.map(col=>{const line=state.items.find(i=>i.model===state.orderModel&&i.color===col);return '<button type="button" class="'+(line?'selected':'')+'" data-color="'+esc(col)+'"><i style="background:'+esc(colorHex[col])+'"></i><span>'+esc(col)+'</span><b>'+(line?line.quantity:'+')+'</b></button>'}).join('')+'</div></section><section class="sp-cart"><div class="sp-cart-head"><div><span class="sp-tag">TU PEDIDO</span><h3>'+units+' chapitas</h3></div><strong>'+money(total)+'</strong></div>'+(state.items.length?'<div class="sp-cart-lines">'+state.items.map((i,n)=>'<div class="sp-cart-line"><span><i style="background:'+esc(colorHex[i.color])+'"></i><span><strong>'+esc(i.model.startsWith('Circular grande')?'Grande':i.model.startsWith('Circular chica')?'Chica':'Gato')+' · '+esc(i.color)+'</strong><small>'+money(i.price)+' c/u</small></span></span><div><button type="button" data-qty="-1" data-index="'+n+'">−</button><b>'+i.quantity+'</b><button type="button" data-qty="1" data-index="'+n+'">+</button></div></div>').join('')+'</div>':'<div class="sp-cart-empty">Todavía no agregaste chapitas.</div>')+'</section><div class="sp-form-grid sp-order-extra"><label><span>Entrega solicitada</span><input type="date" data-field="delivery" value="'+esc(f.delivery||'')+'"></label><label class="wide"><span>Observaciones</span><textarea data-field="notes" rows="2" placeholder="Horario de entrega o pedido especial">'+esc(f.notes||'')+'</textarea></label></div><div class="sp-form-actions sticky"><button type="button" class="sp-btn secondary" data-action="close-modal">Cancelar</button><button class="sp-btn primary" type="submit" '+(state.busy||!state.items.length?'disabled':'')+'>'+(state.busy?'Guardando…':'Guardar pedido · '+money(total))+'</button></div></form></div></div>';
      }
      return '';
    }
    function openShop(s){
      state.form=s?{...s}:{name:'',address:'',zone:'',contact:'',phone:'',status:'Pendiente',next_visit:'',map_url:'',notes:''};
      state.modal='shop';render();
    }
    function openVisit(shopId=''){
      state.form={id:makeId('VIS-'),shop_id:shopId,result:'Interesado',notes:'',next_visit:''};state.modal='visit';render();
    }
    function openOrder(shopId=''){
      state.form={id:makeId('PED-'),shop_id:shopId,delivery:'',notes:'',new_shop_name:'',new_shop_zone:'',new_shop_address:'',new_shop_map_url:''};
      state.items=[];state.orderModel=models[0];state.newShop=!shops().length&&!shopId;state.modal='order';render();
    }
    async function useCurrentLocation(field){
      if(!navigator.geolocation){toast('Este dispositivo no permite obtener la ubicación.','err');return}
      navigator.geolocation.getCurrentPosition(pos=>{state.form[field]='https://maps.google.com/?q='+pos.coords.latitude.toFixed(6)+','+pos.coords.longitude.toFixed(6);toast('Ubicación guardada');render()},err=>toast(err.code===1?'Dale permiso de ubicación para continuar.':'No pudimos obtener tu ubicación.','err'),{enableHighAccuracy:true,timeout:12000,maximumAge:0});
    }
    function openRouteInMaps(){
      const candidates=matchingShops().map(s=>{const p=mapCoords(s);return{s,point:p?(p.lat+','+p.lng):(s.address||'')}}).filter(x=>x.point);
      if(!candidates.length){toast('Guardá la ubicación o dirección de algún comercio para abrir el recorrido.','err');return}
      const tab=window.open('about:blank','_blank');
      const launch=origin=>{
        let list=candidates.slice();
        if(origin)list.sort((a,b)=>{const pa=mapCoords(a.s),pb=mapCoords(b.s);if(pa&&pb)return distanceKm(origin,pa)-distanceKm(origin,pb);if(pa)return-1;if(pb)return 1;return 0});
        list=list.slice(0,8);
        const destination=list[list.length-1].point;
        const waypoints=list.slice(0,-1).map(x=>x.point).join('|');
        const url='https://www.google.com/maps/dir/?api=1'+(origin?'&origin='+encodeURIComponent(origin.lat+','+origin.lng):'')+'&destination='+encodeURIComponent(destination)+(waypoints?'&waypoints='+encodeURIComponent(waypoints):'')+'&travelmode=driving';
        if(tab)tab.location.href=url;else location.href=url;
      };
      if(navigator.geolocation)navigator.geolocation.getCurrentPosition(pos=>launch({lat:pos.coords.latitude,lng:pos.coords.longitude}),()=>launch(null),{enableHighAccuracy:true,timeout:10000,maximumAge:30000});
      else launch(null);
    }
    async function submitForm(form){
      if(state.busy)return;
      state.busy=true;render();
      try{
        if(state.modal==='shop'){
          const d={...state.form,id:state.form.id||undefined,name:String(state.form.name||'').trim(),address:String(state.form.address||'').trim(),zone:String(state.form.zone||'').trim(),contact:String(state.form.contact||'').trim(),phone:String(state.form.phone||'').trim(),seller_id:state.data.viewer.sellerId,status:state.form.status||'Pendiente',next_visit:state.form.next_visit||'',map_url:state.form.map_url||'',notes:String(state.form.notes||'').trim()};
          if(!d.name)throw new Error('Poné el nombre del comercio.');
          await mutate('shop',d);toast('Local guardado');
        }else if(state.modal==='visit'){
          const d={id:state.form.id||makeId('VIS-'),shop_id:state.form.shop_id||'',result:state.form.result||'Interesado',notes:String(state.form.notes||'').trim(),next_visit:state.form.next_visit||''};
          if(!d.shop_id)throw new Error('Elegí un local.');
          await mutate('visit',d);toast('Visita guardada');
        }else if(state.modal==='order'){
          let shopId=state.form.shop_id||'';
          if(state.newShop){
            if(!String(state.form.new_shop_name||'').trim())throw new Error('Poné el nombre del local.');
            const created=await mutate('quickShop',{name:String(state.form.new_shop_name).trim(),address:String(state.form.new_shop_address||'').trim(),zone:String(state.form.new_shop_zone||'').trim(),map_url:String(state.form.new_shop_map_url||'').trim()});shopId=created.id;
          }
          if(!shopId)throw new Error('Elegí un local.');
          if(!state.items.length)throw new Error('Agregá al menos una chapita.');
          await mutate('order',{id:state.form.id||makeId('PED-'),shop_id:shopId,items:state.items,delivery:state.form.delivery||'',notes:String(state.form.notes||'').trim()});toast(state.newShop?'Local y pedido guardados':'Pedido guardado');
        }
        state.modal=null;state.busy=false;render();
      }catch(e){state.busy=false;toast(e.message||'No pudimos guardar.','err');render()}
    }
    function render(){
      root.innerHTML=renderPage();
      document.body.classList.add('sp-body');
    }
    root.addEventListener('input',e=>{
      const field=e.target?.dataset?.field;if(field)state.form[field]=e.target.value;
      if(e.target?.matches?.('[data-search]')){state.query=e.target.value;const pos=e.target.selectionStart;render();const inp=root.querySelector('[data-search]');if(inp){inp.focus();inp.setSelectionRange(pos,pos)}}
    });
    root.addEventListener('change',e=>{const field=e.target?.dataset?.field;if(field)state.form[field]=e.target.value});
    root.addEventListener('submit',e=>{if(e.target.matches('.sp-form')){e.preventDefault();submitForm(e.target)}});
    root.addEventListener('click',async e=>{
      const target=e.target.closest('button,a,[data-action],[data-nav],[data-filter],[data-model],[data-color],[data-qty]');
      if(!target)return;
      if(target.matches('a'))return;
      const nav=target.dataset.nav;
      if(nav){state.section=nav;state.query='';state.filter='';state.drawer=false;render();return}
      if(target.dataset.filter!==undefined){state.filter=target.dataset.filter;render();return}
      if(target.dataset.model){state.orderModel=target.dataset.model;render();return}
      if(target.dataset.color){const col=target.dataset.color,idx=state.items.findIndex(i=>i.model===state.orderModel&&i.color===col);if(idx<0)state.items.push({model:state.orderModel,color:col,quantity:1,price:Number(settings().price||7000)});else state.items[idx].quantity++;render();return}
      if(target.dataset.qty){const idx=Number(target.dataset.index),delta=Number(target.dataset.qty);if(state.items[idx]){state.items[idx].quantity+=delta;if(state.items[idx].quantity<=0)state.items.splice(idx,1)}render();return}
      const action=target.dataset.action;
      if(!action)return;
      if((target.classList.contains('sp-modal-backdrop')||target.classList.contains('sp-drawer-backdrop'))&&e.target!==target)return;
      if(action==='drawer'){state.drawer=true;render()}
      else if(action==='close-drawer'){state.drawer=false;render()}
      else if(action==='close-modal'){state.modal=null;state.busy=false;render()}
      else if(action==='new-shop')openShop();
      else if(action==='edit-shop')openShop(shop(target.dataset.id));
      else if(action==='new-visit')openVisit(target.dataset.id||'');
      else if(action==='new-order')openOrder(target.dataset.id||'');
      else if(action==='shop-detail'){state.form={id:target.dataset.id};state.modal='shop-detail';render()}
      else if(action==='order-detail'){state.form={id:target.dataset.id};state.modal='order-detail';render()}
      else if(action==='toggle-new-shop'){state.newShop=!state.newShop;if(state.newShop)state.form.shop_id='';render()}
      else if(action==='capture-shop-location')useCurrentLocation('map_url');
      else if(action==='capture-new-location')useCurrentLocation('new_shop_map_url');
      else if(action==='maps-route')openRouteInMaps();
      else if(action==='refresh'){try{await reload();toast('Datos actualizados');render()}catch(err){toast(err.message,'err')}}
      else if(action==='logout'){await supabase.auth.signOut();location.reload()}
    });
    render();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();