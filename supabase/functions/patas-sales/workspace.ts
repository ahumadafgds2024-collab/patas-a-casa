import {z} from 'npm:zod@3.25.76';
import {defaults,sellerSchema,shopSchema,visitSchema,orderSchema,settingsSchema,orderStates,commissionSummary} from './domain.ts';
export type Row=Record<string,any>;
export const fail=(message:string,status=400):never=>{throw Object.assign(new Error(message),{status})};
export function access(state:Row,user:Row){
 const email=String(user.email||'').toLowerCase();
 const admin=user.id===state.owner_id||(state.settings.adminEmails||'').toLowerCase().split(/[;,\n]+/).map((s:string)=>s.trim()).includes(email);
 const seller=admin?null:state.sellers.find((s:Row)=>s.active===1&&s.email===email);
 if(!admin&&!seller)fail('Tu correo no está habilitado. Pedile acceso a la administración de Patas a Casa.',403);
 return {admin,seller,email};
}
export function visible(state:Row,user:Row){
 const {admin,seller,email}=access(state,user);const result:Row={viewer:{name:admin?'Administración':seller.name,email,admin,sellerId:seller?.id||''},settings:{...state.settings}};
 if(!admin)result.settings.adminEmails='';
 for(const key of ['sellers','shops','visits','orders','payments','commissions','kits'])result[key]=state[key];
 if(!admin){result.sellers=state.sellers.filter((s:Row)=>s.id===seller.id);for(const k of ['shops','visits','orders','commissions','kits'])result[k]=state[k].filter((r:Row)=>r.seller_id===seller.id);const ids=new Set(result.orders.map((o:Row)=>o.id));result.payments=state.payments.filter((p:Row)=>ids.has(p.order_id));}
 return result;
}
export function change(state:Row,user:Row,action:string,input:unknown,now=new Date().toISOString()){
 const {admin,seller}=access(state,user);const mustAdmin=()=>{if(!admin)fail('Esta acción corresponde a administración.',403)};
 const validSeller=(id:string)=>{if(id&&!state.sellers.some((s:Row)=>s.id===id&&s.active===1))fail('Elegí un vendedor activo.')};
 const getShop=(id:string)=>{const s=state.shops.find((s:Row)=>s.id===id);if(!s)fail('No encontramos el comercio.',404);if(!admin&&s.seller_id!==seller.id)fail('Comercio no asignado a tu cuenta.',403);return s;};
 const upsert=(key:string,row:Row)=>{const n=state[key].findIndex((x:Row)=>x.id===row.id);if(n<0)state[key].push(row);else state[key][n]={...state[key][n],...row}};
 const existing=(key:string,id:string)=>state[key].find((r:Row)=>r.id===id);
 const paid=(orderId:string)=>state.payments.filter((p:Row)=>p.order_id===orderId).reduce((n:number,p:Row)=>n+p.amount,0);
 if(action==='seller'){mustAdmin();const s=sellerSchema.parse(input);if(s.email===state.owner_email)fail('Ese correo pertenece a administración.');if(state.sellers.some((r:Row)=>r.email===s.email&&r.id!==s.id))fail('Ya hay un vendedor con ese correo.');const id=s.id||crypto.randomUUID();upsert('sellers',{...s,id});return {id};}
 if(action==='shop'){mustAdmin();const s=shopSchema.parse(input);validSeller(s.seller_id);const id=s.id||'PAC-'+crypto.randomUUID().slice(0,8).toUpperCase();upsert('shops',{...s,id,created:existing('shops',id)?.created||now});return {id};}
 if(action==='visit'){const v=visitSchema.parse(input),s=getShop(v.shop_id);const prior=existing('visits',v.id);if(prior){if(!admin&&prior.seller_id!==seller.id)fail('Registro no disponible.',403);return{id:v.id};}state.visits.push({...v,seller_id:admin?s.seller_id:seller.id,created:now});s.status=v.result==='Hizo pedido'?'Cliente':v.result;s.next_visit=v.next_visit;return{id:v.id};}
 if(action==='order'){const o=orderSchema.parse(input),s=getShop(o.shop_id);const prior=existing('orders',o.id);if(prior){if(!admin&&prior.seller_id!==seller.id)fail('Registro no disponible.',403);return{id:o.id};}if(!admin&&o.items.some(i=>i.price!==state.settings.price))fail('El precio debe ser el establecido por administración.');const units=o.items.reduce((n,i)=>n+i.quantity,0),total=o.items.reduce((n,i)=>n+i.quantity*i.price,0);if(total>1000000000)fail('El importe supera el límite por pedido.');state.orders.push({...o,seller_id:admin?s.seller_id:seller.id,units,total,status:'Recibido',created:now});s.status='Cliente';return{id:o.id};}
 if(action==='orderStatus'){mustAdmin();const x=z.object({id:z.string(),status:z.enum(orderStates)}).parse(input),o=existing('orders',x.id);if(!o)fail('Pedido no encontrado.',404);if(o.status==='Cancelado')fail('Un pedido cancelado queda cerrado. Creá un pedido nuevo.');if(x.status==='Cancelado'&&paid(o.id)>0)fail('No se puede cancelar un pedido con cobros registrados.');o.status=x.status;return{ok:true};}
 if(action==='payment'){mustAdmin();const x=z.object({id:z.string().min(1).max(100),order_id:z.string(),amount:z.number().int().positive().max(1000000000),method:z.enum(['Transferencia','Efectivo','Otro']),reference:z.string().trim().max(1000)}).parse(input);if(existing('payments',x.id))return{id:x.id};const o=existing('orders',x.order_id);if(!o||o.status==='Cancelado'||x.amount>o.total-paid(o.id))fail('El importe supera el saldo pendiente o el pedido está cancelado.');state.payments.push({...x,created:now});return{id:x.id};}
 if(action==='commission'){mustAdmin();const x=z.object({id:z.string().min(1).max(100),seller_id:z.string(),amount:z.number().int().positive().max(1000000000),reference:z.string().trim().max(1000)}).parse(input);if(existing('commissions',x.id))return{id:x.id};if(!existing('sellers',x.seller_id))fail('Vendedor no encontrado.');const summary=commissionSummary(state.orders,state.payments,state.commissions,x.seller_id);if(x.amount>summary.due)fail('El importe supera la comisión disponible para abonar.');state.commissions.push({...x,created:now});return{id:x.id};}
 if(action==='kit'){mustAdmin();const x=z.object({id:z.string().min(1).max(100),seller_id:z.string(),description:z.string().trim().min(2).max(1000),quantity:z.number().int().min(1).max(10000)}).parse(input);validSeller(x.seller_id);if(!existing('kits',x.id))state.kits.push({...x,returned:0,created:now});return{id:x.id};}
 if(action==='kitReturn'){mustAdmin();const x=z.object({id:z.string()}).parse(input),kit=existing('kits',x.id);if(!kit)fail('Material no encontrado.');kit.returned=kit.quantity;return{ok:true};}
 if(action==='settings'){mustAdmin();state.settings=settingsSchema.parse(input);return{ok:true};}
 fail('Acción no reconocida.');
}
