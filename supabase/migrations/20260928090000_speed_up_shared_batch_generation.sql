-- Shared-code tags do not expose their random internal PIN, so comparing it
-- against every existing bcrypt hash only adds O(batch_size * tag_count) work.
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
  v_private_secret text;
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

    v_private_secret := encode(extensions.gen_random_bytes(16), 'hex');

    begin
      insert into public.tags(public_code, activation_hash, activation_mode)
      values (v_code, extensions.crypt(v_private_secret, extensions.gen_salt('bf')), 'shared');
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

