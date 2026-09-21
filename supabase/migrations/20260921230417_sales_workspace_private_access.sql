-- Sales data is isolated from pets, tags and existing administration.
create table public.sales_workspace (
 id integer primary key check(id=1),
 state jsonb not null,
 version bigint not null default 0,
 updated_at timestamptz not null default now()
);
alter table public.sales_workspace enable row level security;
revoke all on public.sales_workspace from public, anon, authenticated;
grant select,insert,update on public.sales_workspace to service_role;
create table public.sales_invites (
 seller_id text primary key,
 email text not null,
 token_hash text not null unique check(length(token_hash)=64),
 expires_at timestamptz not null,
 used_at timestamptz
);
alter table public.sales_invites enable row level security;
revoke all on public.sales_invites from public, anon, authenticated;
grant select,insert,update,delete on public.sales_invites to service_role;
insert into public.sales_workspace(id,state)
select 1,jsonb_build_object(
 'owner_id',id,'owner_email',lower(email),
 'settings',jsonb_build_object('price',7000,'retail','','minimum','','delivery','','payment','','phone','','adminEmails',''),
 'sellers','[]'::jsonb,'shops','[]'::jsonb,'visits','[]'::jsonb,'orders','[]'::jsonb,'payments','[]'::jsonb,'commissions','[]'::jsonb,'kits','[]'::jsonb
) from auth.users where lower(email)='farid.ahumada21@gmail.com' and email_confirmed_at is not null;
DO $$ BEGIN IF NOT EXISTS(select 1 from public.sales_workspace where id=1) THEN RAISE EXCEPTION 'Owner account not found'; END IF; END $$;

-- Bind the sales owner to the verified connected account.
update public.sales_workspace w set state=jsonb_set(jsonb_set(w.state,'{owner_id}',to_jsonb(u.id::text)),'{owner_email}',to_jsonb(lower(u.email))),version=version+1 from auth.users u where w.id=1 and lower(u.email)='ahumada.f.gds2024@gmail.com' and u.email_confirmed_at is not null;
