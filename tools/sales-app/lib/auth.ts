const URL='https://cgciwutqwnssdphugupq.supabase.co';
const KEY='sb_publishable_oozsLV8QMoy_ooLIqgh_qg_vvjV6IY5';
export const auth=(window as any).supabase.createClient(URL,KEY,{auth:{storageKey:'pac_sales_auth_v1',persistSession:true,autoRefreshToken:true,detectSessionInUrl:false}}).auth;
export async function workspaceRequest(init:RequestInit={}){
 const{data:{session}}=await auth.getSession();
 if(!session)return Response.json({error:'Iniciá sesión para entrar.'},{status:401});
 return fetch(URL+'/functions/v1/patas-sales',{...init,cache:'no-store',headers:{'Content-Type':'application/json',apikey:KEY,Authorization:'Bearer '+session.access_token,...init.headers}});
}
export async function publicRequest(body:unknown){const r=await fetch(URL+'/functions/v1/patas-sales',{method:'POST',headers:{'Content-Type':'application/json',apikey:KEY},body:JSON.stringify(body)});const data=await r.json();if(!r.ok)throw new Error(data.error||'No pudimos completar la solicitud.');return data;}
