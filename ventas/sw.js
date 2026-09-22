const SCOPE='/ventas/';
self.addEventListener('install',()=>self.skipWaiting());
self.addEventListener('activate',event=>event.waitUntil(self.clients.claim()));
self.addEventListener('fetch',event=>{
  const url=new URL(event.request.url);
  if(event.request.method!=='GET'||url.origin!==self.location.origin||!url.pathname.startsWith(SCOPE))return;
  if(event.request.mode==='navigate'){
    event.respondWith(fetch(event.request).catch(()=>new Response(
      '<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sin conexión</title><body style="font-family:system-ui;padding:32px;color:#18324d"><h1>Patas a Casa Ventas</h1><p>Necesitás conexión a internet para abrir el panel de ventas.</p></body></html>',
      {headers:{'Content-Type':'text/html; charset=utf-8'}}
    )));
    return;
  }
  event.respondWith(fetch(event.request));
});

self.addEventListener('push',event=>{
  let data={};
  try{data=event.data?event.data.json():{}}catch{}
  const title=data.title||'Patas a Casa';
  const options={
    body:data.body||'Tenés una novedad en Ventas.',
    icon:'/ventas/icon-192.svg',
    badge:'/ventas/icon-192.svg',
    tag:data.tag||'patas-ventas',
    renotify:true,
    data:{url:data.url||'/ventas/',orderId:data.orderId||''}
  };
  event.waitUntil(self.registration.showNotification(title,options));
});
self.addEventListener('notificationclick',event=>{
  event.notification.close();
  const target=new URL(event.notification.data?.url||'/ventas/',self.location.origin).href;
  event.waitUntil((async()=>{
    const list=await self.clients.matchAll({type:'window',includeUncontrolled:true});
    for(const client of list){
      if(client.url.startsWith(self.location.origin+'/ventas/')){
        await client.focus();
        if('navigate'in client&&client.url!==target)await client.navigate(target);
        return;
      }
    }
    await self.clients.openWindow(target);
  })());
});
