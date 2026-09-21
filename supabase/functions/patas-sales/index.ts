import {createClient} from 'npm:@supabase/supabase-js@2.112.4';
import {z} from 'npm:zod@3.25.76';
import {access,visible,change,fail} from './workspace.ts';
const URL=Deno.env.get('SUPABASE_URL')!;
const db=createClient(URL,Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,{auth:{persistSession:false,autoRefreshToken:false}});
const origins=new Set(['https://www.patasacasa.com.ar','https://patasacasa.com.ar']);
const headers=(origin:string)=>({'Content-Type':'application/json','Cache-Control':'no-store','Access-Control-Allow-Origin':origins.has(origin)?origin:'https://www.patasacasa.com.ar','Access-Control-Allow-Headers':'authorization,apikey,content-type,x-client-info','Access-Control-Allow-Methods':'GET,POST,OPTIONS','Vary':'Origin'});
const hash=async(token:string)=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(token))),b=>b.toString(16).padStart(2,'0')).join('');
async function workspace(){const{data,error}=await db.from('sales_workspace').select('state,version').eq('id',1).single();if(error||!data)fail('El panel no está disponible. Intentá nuevamente.',503);return data;}
async function invite(token:string){if(!/^[a-f0-9]{64}$/.test(token))fail('El enlace no es válido o ya venció.',400);const{data,error}=await db.from('sales_invites').select('*').eq('token_hash',await hash(token)).is('used_at',null).gt('expires_at',new Date().toISOString()).maybeSingle();if(error||!data)fail('El enlace no es válido o ya venció.',400);const{state}=await workspace();const seller=state.sellers.find((s:any)=>s.id===data.seller_id&&s.active===1&&s.email===data.email);if(!seller)fail('Este acceso ya no está habilitado.',403);return {...data,name:seller.name};}
Deno.serve(async(req:Request)=>{
 const origin=req.headers.get('origin')||'';const reply=(data:any,status=200)=>new Response(JSON.stringify(data),{status,headers:headers(origin)});
 if(req.method==='OPTIONS')return new Response(null,{status:204,headers:headers(origin)});
 try{
  if(origin&&!origins.has(origin))fail('Origen no permitido.',403);
  if(!['GET','POST'].includes(req.method))fail('Método no permitido.',405);
  let body:any={};if(req.method==='POST'){const text=await req.text();if(text.length>100000)fail('La solicitud es demasiado grande.',413);try{body=JSON.parse(text)}catch{fail('Solicitud inválida.');}}
  if(req.method==='POST'&&body.action==='invitationInfo'){const i=await invite(String(body.token||''));return reply({name:i.name,email:i.email});}
  if(req.method==='POST'&&body.action==='activate'){
   const password=z.string().min(10,'Usá al menos 10 caracteres.').max(128).parse(body.password);const i=await invite(String(body.token||''));
   const{data:used,error:consumeError}=await db.from('sales_invites').update({used_at:new Date().toISOString()}).eq('token_hash',i.token_hash).is('used_at',null).select('token_hash').maybeSingle();
   if(consumeError||!used)fail('Este enlace ya fue utilizado.');
   const{error}=await db.auth.admin.createUser({email:i.email,password,email_confirm:true});
   if(error){if(['email_exists','user_already_exists'].includes(error.code||'')||/already (been registered|registered|exists)/i.test(error.message))return reply({existing:true,email:i.email});
    // Permit retry only if account creation did not succeed; token retains its original expiry.
    await db.from('sales_invites').update({used_at:null}).eq('token_hash',i.token_hash);
    fail('No pudimos crear la cuenta. Volvé a intentarlo.',503);
   }
   return reply({ok:true,email:i.email});
  }
  const authorization=req.headers.get('authorization')||'';if(!authorization.startsWith('Bearer '))fail('Iniciá sesión para entrar.',401);
  const{data:{user},error:authError}=await db.auth.getUser(authorization.slice(7));
  if(authError||!user||!user.email||!user.email_confirmed_at)fail('Tu sesión venció. Volvé a ingresar.',401);
  const initial=await workspace();const permissions=access(initial.state,user);
  if(req.method==='GET')return reply(visible(initial.state,user));
  if(body.action==='accessLink'){
   if(!permissions.admin)fail('Esta acción corresponde a administración.',403);
   const seller=initial.state.sellers.find((s:any)=>s.id===body.data?.seller_id&&s.active===1);if(!seller)fail('Elegí un vendedor activo.');
   const token=Array.from(crypto.getRandomValues(new Uint8Array(32)),b=>b.toString(16).padStart(2,'0')).join('');
   const{error}=await db.from('sales_invites').upsert({seller_id:seller.id,email:seller.email,token_hash:await hash(token),expires_at:new Date(Date.now()+7*86400000).toISOString(),used_at:null},{onConflict:'seller_id'});
   if(error)fail('No pudimos generar el acceso.',503);
   return reply({url:'https://www.patasacasa.com.ar/ventas/#alta='+token,email:seller.email});
  }
  for(let attempt=0;attempt<5;attempt++){
   const{state,version}=attempt===0?initial:await workspace();
   const result=change(state,user,body.action,body.data);
   const{data,error}=await db.from('sales_workspace').update({state,version:version+1,updated_at:new Date().toISOString()}).eq('id',1).eq('version',version).select('version').maybeSingle();
   if(error)fail('No pudimos guardar el registro. Intentá nuevamente.',503);
   if(data)return reply(result);
  }
  fail('Otra persona está guardando cambios. Intentá nuevamente.',409);
 }catch(e:any){if(e instanceof z.ZodError)return reply({error:e.issues[0]?.message||'Revisá los datos.'},400);return reply({error:e.status?e.message:'No pudimos completar la solicitud.'},e.status||503);}
});
