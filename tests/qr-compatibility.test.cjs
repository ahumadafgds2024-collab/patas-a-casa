const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { stripTypeScriptTypes } = require('node:module');
const QRCode = require('qrcode');
const jsQR = require('jsqr');
const { PNG } = require('pngjs');

function canvas() {
  const c = { width: 0, height: 0 };
  c.getContext = () => {
    c.data = new Uint8ClampedArray(c.width*c.height*4);
    const ctx = { fillStyle: '#ffffff', fillRect(x,y,w,h) {
      const v = this.fillStyle === '#ffffff' ? 255 : 0;
      for(let row=y;row<y+h;row++) for(let col=x;col<x+w;col++) {
        const i=(row*c.width+col)*4;
        c.data.set([v,v,v,255],i);
      }
    }};
    return ctx;
  };
  c.toDataURL = () => 'data:image/png;base64,'+PNG.sync.write({width:c.width,height:c.height,data:Buffer.from(c.data)}).toString('base64');
  return c;
}
function admin() {
  const html = fs.readFileSync('admin.html','utf8');
  const source = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/gi)].map(x=>x[1]).join('\n');
  const context = vm.createContext({ QRCode, URL, TextEncoder, document: {
    getElementById: () => ({addEventListener(){}}),
    createElement: type => {assert.equal(type,'canvas');return canvas();},
  }});
  vm.runInContext(source, context);
  return context;
}
function decodePng(data) {
  const png=PNG.sync.read(Buffer.from(data.split(',')[1],'base64'));
  return jsQR(new Uint8ClampedArray(png.data),png.width,png.height)?.data;
}
function decodeSvg(svg) {
  // Rasterize the production SVG's module runs with a white quiet zone.
  assert.match(svg,/viewBox="0 0 25 25"/);
  const c=canvas();c.width=c.height=330;const ctx=c.getContext('2d');
  ctx.fillRect(0,0,330,330);ctx.fillStyle='#000000';
  for(const m of svg.matchAll(/M(\d+) (\d+)h(\d+)v1h-\d+z/g))ctx.fillRect((+m[1]+4)*10,(+m[2]+4)*10,+m[3]*10,10);
  return jsQR(c.data,330,330)?.data;
}
test('legacy/current responses preserve aliases and normalize only scheme/host',()=>{
  const a=admin();
  assert.equal(a.payload({qr_payload:'HTTPS://PAC.S.GY/ETSU95TB'}),'https://pac.s.gy/ETSU95TB');
  assert.equal(a.payload({short_url:'https://pac.s.gy/aBcD1234',qr_payload:'HTTPS://PAC.S.GY/ABCD1234'}),'https://pac.s.gy/aBcD1234');
});
test('PNG and both actual SVG exports decode to the complete HTTPS URL',()=>{
  const a=admin(),url='https://pac.s.gy/ETSU95TB',q=a.createQr(url);
  assert.equal(q.version,2);assert.equal(q.modules.size,25);
  assert.equal(q.segments.length,1);assert.equal(q.segments[0].mode.id,'Byte');
  const assets=a.qrAssets(url);
  assert.equal(decodePng(assets.png),url);
  for(const [svg,size] of [[assets.small,15],[assets.large,21.5]]) {
    assert.ok(svg.includes(`width="${size}mm"`));assert.equal(decodeSvg(svg),url);
  }
  assert.equal(assets.small.replaceAll('15mm','21.5mm'),assets.large);
});
test('32-byte capacity boundary and invalid URL forms fail closed',()=>{
  const a=admin(),url='https://abcdefghij.s.gy/ABCDEFGH';
  assert.equal(Buffer.byteLength(url),32);assert.equal(a.createQr(url).modules.size,25);
  for(const bad of [url+'A','HTTPS://PAC.S.GY/ABCDE','pac.s.gy/ABCDE','http://pac.s.gy/ABCDE','https://pac.s.gy/ABCDE?x=1','https://pac.s.gy/ABCDE#x','https://evil.com/ABCDE','https://user@pac.s.gy/ABCDE'])assert.throws(()=>a.createQr(bad),bad);
});
test('CSV and output labels describe V2 without changing activation or sizes',()=>{
  const csv=admin().csvText([{short_url:'https://pac.s.gy/ABCDEFGH',pin:'PAC2011'}]);
  assert.match(csv,/25x25 V2-L/);assert.match(csv,/PAC2011/);
  assert.doesNotMatch(fs.readFileSync('admin.html','utf8'),/21×21|21x21|V1-L|version:1|toUpperCase/);
});
function backend(fetch) {
  const source=fs.readFileSync('supabase/functions/patas-admin-shortio/index.ts','utf8').replace(/^import .*;\r?\n/,'');
  let handler;
  const context=vm.createContext({URL,TextEncoder,Request,Response,AbortController,crypto,performance,
    setTimeout: fn=>setTimeout(fn,0), clearTimeout,console:{log(){},error(){}},fetch,
    Deno:{env:{get:key=>key==='SUPABASE_URL'?'https://db.test':'test-only-key'},serve: fn=>{handler=fn;}}
  });
  vm.runInContext(stripTypeScriptTypes(source),context);
  return {context,handler};
}
test('frontend/backend domain limits agree with actual encoder capacity',()=>{
  const b=backend(()=>{throw Error('unexpected network');}).context,a=admin();
  for(const n of [1,3,10,13]) {
    const {domain,slugLength}=b.normalizeDomain('a'.repeat(n)+'.s.gy');
    assert.equal(slugLength,Math.min(8,32-('https://'+domain+'/').length));
    a.createQr(`https://${domain}/${'A'.repeat(slugLength)}`);
  }
  assert.equal(b.normalizeDomain('pac.s.gy').slugLength,8);
  assert.throws(()=>b.normalizeDomain('a'.repeat(14)+'.s.gy'));
});
async function batch(wrongRedirect=false, collision=false) {
  const calls=[];let slug,attempts=0;
  const {handler}=backend(async(url,init={})=>{
    calls.push({url,init});
    if(init.method==='DELETE')return new Response(null,{status:204});
    if(url.endsWith('/rpc/generate_tag_batch'))return Response.json([{public_code:'TEST1234',activation_pin:'PAC2011'}]);
    if(url==='https://api.short.io/links') {
      const body=JSON.parse(init.body);slug=body.path;
      assert.equal(body.domain,'pac.s.gy');assert.equal(body.originalURL,'https://www.patasacasa.com.ar/?tag=TEST1234');
      assert.equal(body.allowDuplicates,false);assert.equal(slug.length,8);
      if(collision&&attempts++===0)return Response.json({error:'conflict'},{status:409});
      return Response.json({path:slug,idString:'test-id',secureShortURL:`https://pac.s.gy/${slug}`,originalURL:body.originalURL});
    }
    if(url.startsWith('https://pac.s.gy/'))return new Response(null,{status:302,headers:{location:wrongRedirect?'https://www.patasacasa.com.ar/?tag=WRONG':'https://www.patasacasa.com.ar/?tag=TEST1234'}});
    if(url.endsWith('/short_links'))return new Response(null,{status:201});
    throw Error('Unexpected request '+url);
  });
  const res=await handler(new Request('https://edge.test',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'generate_batch',admin_key:'test',shortio_api_key:'test',shortio_domain:'pac.s.gy',count:1})}));
  return {res,data:await res.json(),calls};
}
test('full batch verifies exact encoded URL, keeps Short.io and PAC2011',async()=>{
  const {res,data,calls}=await batch(false,true);
  assert.equal(res.status,200);assert.equal(data.provider,'shortio');
  const item=data.items[0];assert.equal(item.pin,'PAC2011');assert.equal(item.qr_payload,item.short_url);
  assert.match(item.qr_payload,/^https:\/\/pac\.s\.gy\/[A-Z2-9]{8}$/);
  assert.ok(calls.some(x=>x.url===item.qr_payload&&x.init.redirect==='manual'));
  assert.equal(decodePng(admin().qrAssets(item.qr_payload).png),item.short_url);
});
test('wrong destination returns no QR and rolls back tag and Short.io link',async()=>{
  const {res,data,calls}=await batch(true);
  assert.equal(res.status,502);assert.equal(data.items,undefined);
  assert.ok(calls.some(x=>x.url==='https://api.short.io/links/test-id'&&x.init.method==='DELETE'));
  assert.ok(calls.some(x=>x.url.includes('/tags?')&&x.init.method==='DELETE'));
});
