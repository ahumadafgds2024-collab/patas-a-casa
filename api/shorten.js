function code4(){
  const chars='ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let out='';
  for(let i=0;i<4;i++) out+=chars[Math.floor(Math.random()*chars.length)];
  return out;
}

async function trySpoo(target){
  for(let attempt=0; attempt<6; attempt++){
    const alias=code4();
    const controller=new AbortController();
    const timer=setTimeout(()=>controller.abort(),7000);
    try{
      const r=await fetch('https://spoo.me/api/v1/shorten',{
        method:'POST',
        headers:{'Content-Type':'application/json','Accept':'application/json'},
        body:JSON.stringify({long_url:target,alias}),
        signal:controller.signal
      });
      const data=await r.json().catch(()=>({}));
      if(r.ok && data?.short_url){
        const short=String(data.short_url);
        return {shorturl:short,payload:short.toUpperCase(),service:'spoo.me'};
      }
      if(r.status===409 || r.status===422) continue;
      if(r.status===429) break;
      if(r.status>=400 && r.status<500) throw new Error(data?.detail||data?.error||'La URL no es válida.');
      break;
    }catch(e){
      if(e?.name==='AbortError') break;
      if(String(e?.message||'').includes('URL no es válida')) throw e;
      break;
    }finally{clearTimeout(timer)}
  }
  return null;
}

async function tryCleanUri(target){
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),7000);
  try{
    const body=new URLSearchParams({url:target});
    const r=await fetch('https://cleanuri.com/api/v1/shorten',{
      method:'POST',
      headers:{'Content-Type':'application/x-www-form-urlencoded','Accept':'application/json'},
      body,
      signal:controller.signal
    });
    const data=await r.json().catch(()=>({}));
    if(r.ok && data?.result_url){
      const short=String(data.result_url);
      return {shorturl:short,payload:short,service:'cleanuri.com'};
    }
  }catch(e){}finally{clearTimeout(timer)}
  return null;
}

export default async function handler(req,res){
  res.setHeader('Cache-Control','no-store');
  if(req.method!=='POST') return res.status(405).json({error:'Método no permitido'});
  const target=String(req.body?.url||'').trim();
  let parsed;
  try{parsed=new URL(target)}catch{return res.status(400).json({error:'Pegá una URL completa que empiece con http:// o https://'})}
  if(!['http:','https:'].includes(parsed.protocol)) return res.status(400).json({error:'La URL debe empezar con http:// o https://'});
  if(target.length>4000) return res.status(400).json({error:'La URL es demasiado larga'});

  try{
    const spoo=await trySpoo(target);
    if(spoo) return res.status(200).json(spoo);

    const clean=await tryCleanUri(target);
    if(clean) return res.status(200).json(clean);

    return res.status(503).json({error:'No pude acortar el enlace ahora. Probá otra vez en unos segundos.'});
  }catch(e){
    return res.status(400).json({error:e?.message||'No se pudo acortar la URL'});
  }
}
