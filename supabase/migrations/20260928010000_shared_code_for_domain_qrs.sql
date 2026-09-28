-- Existing QR links for patasacasa.com.ar use the shared activation flow.
-- Keep activation_hash unchanged: it is a separate legacy owner credential.
update public.tags as t
set activation_mode = 'shared'
where t.activation_mode = 'pin'
  and t.activated_at is null
  and t.pet_id is null
  and exists (
    select 1
    from public.short_links as s
    where s.public_code = t.public_code
      and s.target_url ~* '^https://(www\.)?patasacasa\.com\.ar/'
      and upper(substring(s.target_url from '[?&]tag=([A-Za-z0-9]+)')) = t.public_code
  );

-- Future batches keep a unique QR and an internal random hash, while the
-- code delivered with each chapita is the shared activation code.
create or replace function public.generate_tag_batch(p_admin_key text, p_count integer)
returns table(public_code text, activation_pin text)
language plpgsql
security definer
set search_path to 'public', 'extensions', 'pg_temp'
set statement_timeout to '12s'
as $function$
declare
  v_hash text;
  v_code text;
  v_pin_digits text;
  v_private_pin text;
  v_bytes bytea;
  v_num bigint;
  v_created integer := 0;
begin
  if p_count is null or p_count < 1 or p_count > 100 then
    raise exception 'Cantidad inválida';
  end if;

  select key_hash into v_hash from public.app_admin_config where id = 1;
  if v_hash is null or extensions.crypt(coalesce(p_admin_key,''), v_hash) <> v_hash then
    raise exception 'Clave de administrador incorrecta';
  end if;

  while v_created < p_count loop
    v_code := upper(encode(extensions.gen_random_bytes(4), 'hex'));

    v_bytes := extensions.gen_random_bytes(4);
    v_num := get_byte(v_bytes,0)::bigint * 16777216
           + get_byte(v_bytes,1)::bigint * 65536
           + get_byte(v_bytes,2)::bigint * 256
           + get_byte(v_bytes,3)::bigint;
    v_pin_digits := lpad((v_num % 100000000)::text, 8, '0');
    v_private_pin := substr(v_pin_digits,1,4) || '-' || substr(v_pin_digits,5,4);

    if exists (
      select 1
      from public.tags t
      where t.activation_hash = extensions.crypt(v_private_pin, t.activation_hash)
    ) then
      continue;
    end if;

    begin
      insert into public.tags(public_code, activation_hash, activation_mode)
      values (v_code, extensions.crypt(v_private_pin, extensions.gen_salt('bf')), 'shared');
      v_created := v_created + 1;
      public_code := v_code;
      activation_pin := 'PAC2011';
      return next;
    exception when unique_violation then
      -- A public-code collision is rare; generate another code.
    end;
  end loop;
end;
$function$;
