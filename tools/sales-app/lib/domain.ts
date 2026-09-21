import {z} from 'zod';
export const shopStates=['Pendiente','Interesado','Volver a visitar','Cliente','No interesado','Cerrado'] as const;
export const visitResults=['Interesado','Hizo pedido','Volver a visitar','No interesado','Cerrado'] as const;
export const orderStates=['Recibido','Confirmado','Preparado','Entregado','Cancelado'] as const;
export const colors=['Naranja','Celeste','Rosado','Negro','Blanco','Verde','Morado','Amarillo'];
export const models=['Circular grande · 31 mm','Circular chica · 25 mm','Cara de gato'];
const short=z.string().trim().max(300);const note=z.string().trim().max(3000);const id=z.string().min(1).max(100);const date=z.string().refine(s=>s===''||(/^\d{4}-\d{2}-\d{2}$/.test(s)&&!Number.isNaN(Date.parse(s))),'Fecha inválida');
const url=z.string().trim().max(1500).refine(s=>!s||(()=>{try{const u=new URL(s);return u.protocol==='https:'}catch{return false}})(),'Usá un enlace https válido');
export const sellerSchema=z.object({id:id.optional(),name:short.min(2),email:z.string().trim().email().transform(s=>s.toLowerCase()),phone:short,zone:short,map_url:url,active:z.number().int().min(0).max(1)});
export const shopSchema=z.object({id:id.optional(),name:short.min(2),address:short.min(3),zone:short,contact:short,phone:short,seller_id:short,status:z.enum(shopStates),next_visit:date,map_url:url,notes:note});
export const visitSchema=z.object({id:id,shop_id:id,result:z.enum(visitResults),notes:note,next_visit:date});
export const itemSchema=z.object({model:z.enum(['Circular grande · 31 mm','Circular chica · 25 mm','Cara de gato']),color:z.enum(['Naranja','Celeste','Rosado','Negro','Blanco','Verde','Morado','Amarillo']),quantity:z.number().int().min(1).max(10000),price:z.number().int().min(1).max(10000000)});
export const orderSchema=z.object({id:id,shop_id:id,items:z.array(itemSchema).min(1).max(60),delivery:date,notes:note});
export const settingsSchema=z.object({price:z.number().int().min(1).max(10000000),retail:short,minimum:short,delivery:short,payment:short,phone:short,adminEmails:z.string().trim().max(3000).refine(s=>s.split(/[;,\n]+/).every(v=>!v.trim()||z.string().email().safeParse(v.trim()).success),'Revisá los correos de administración')});
export const defaults={price:7000,retail:'',minimum:'',delivery:'',payment:'',phone:'',adminEmails:''};
export function commissionSummary(orders:any[],payments:any[],commissions:any[],sellerId:string){const paidUnits=orders.filter(o=>o.seller_id===sellerId&&o.status!=='Cancelado'&&payments.filter(p=>p.order_id===o.id).reduce((a,p)=>a+p.amount,0)>=o.total).reduce((a,o)=>a+o.units,0);const earned=Math.floor(paidUnits/4)*7000;const paid=commissions.filter(c=>c.seller_id===sellerId).reduce((a,c)=>a+c.amount,0);return{units:paidUnits,earned,paid,due:earned-paid,remainder:paidUnits%4};}
