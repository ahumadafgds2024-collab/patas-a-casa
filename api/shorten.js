const SERVICES = [
  'https://is.gd/create.php',
  'https://v.gd/create.php'
];

function code5(){
  const chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let out='';
  for(let i=0;i<5;i++) out+=chars[Math.floor(Math.random()*chars.length)];
  return out;
}

async function tryService(base, target){
  for(let attempt=0; attempt<7; attempt++){
    const shorturl=code5();
    const u=new URL(base);
    u.searchParams.set('format','json');
    u.searchParams.set('url',target);
    u.searchParams.set('shorturl',shorturl);
    const controller=new AbortController();
    const timer=setTimeout(()=>controller.abort(),4500);
    try{
      const r=await fetch(u,{headers:{'User-Agent':'QR-Simple/1.0'},signal:controller.signal});
      const text=await r.text();
      let data={};
      try{ data=JSON.parse(text); }catch{}
      if(r.ok && data.shorturl){
        return { shorturl:data.shorturl, payload:String(data.shorturl).toUpperCase(), service:new URL(base).hostname };
      }
      // errorcode 2 = custom alias already used; retry a new 5-char code
      if(Number(data.errorcode)===2) continue;
      if(Number(data.errorcode)===3) break; // rate limit, move to fallback service
      if(Number(data.errorcode)===1) throw new Error(data.errormessage||'La URL no es válida.');
    }catch(e){
      if(e?.name==='AbortError') break;
      if(String(e?.message||'').includes('URL no es válida')) throw e;
      break;
    }finally{ clearTimeout(timer); }
  }
  return null;
}

export default async function handler(req,res){
  res.setHeader('Cache-Control','no-store');
  if(req.method!=='POST') return res.status(405).json({error:'Método no permitido'});
  const target=String(req.body?.url||'').trim();
  let parsed;
  try{ parsed=new URL(target); }catch{ return res.status(400).json({error:'Pegá una URL completa que empiece con http:// o https://'}); }
  if(!['http:','https:'].includes(parsed.protocol)) return res.status(400).json({error:'La URL debe empezar con http:// o https://'});
  if(target.length>4000) return res.status(400).json({error:'La URL es demasiado larga'});

  try{
    for(const service of SERVICES){
      const result=await tryService(service,target);
      if(result) return res.status(200).json(result);
    }
    return res.status(503).json({error:'Los acortadores están ocupados. Probá de nuevo en unos segundos.'});
  }catch(e){
    return res.status(400).json({error:e?.message||'No se pudo acortar la URL'});
  }
}
