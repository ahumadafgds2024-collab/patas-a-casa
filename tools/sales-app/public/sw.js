const SCOPE='/ventas/';
self.addEventListener('install',()=>self.skipWaiting());
self.addEventListener('activate',event=>event.waitUntil(self.clients.claim()));
self.addEventListener('fetch',event=>{
  const url=new URL(event.request.url);
  if(event.request.method!=='GET'||url.origin!==self.location.origin||!url.pathname.startsWith(SCOPE))return;
  event.respondWith(fetch(event.request).catch(()=>new Response(
    '<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sin conexión</title><body style="font-family:system-ui;padding:32px;color:#18324d"><h1>Patas a Casa Ventas</h1><p>Necesitás conexión a internet para abrir el panel de ventas.</p></body></html>',
    {headers:{'Content-Type':'text/html; charset=utf-8'}}
  )));
});
