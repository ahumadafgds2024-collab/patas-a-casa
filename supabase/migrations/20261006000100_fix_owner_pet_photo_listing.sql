drop policy if exists "pet_owner_list_photos_for_delete" on storage.objects;

create or replace function public.list_my_pet_photo_paths(p_public_code text)
returns text[]
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_user_id uuid := auth.uid();
  v_code text := upper(btrim(coalesce(p_public_code, '')));
  v_pet_id uuid;
  v_paths text[];
begin
  if v_user_id is null then
    raise exception 'Sesión vencida. Volvé a ingresar.' using errcode = '42501';
  end if;

  select p.id
    into v_pet_id
  from public.pets p
  where p.owner_id = v_user_id
    and p.public_code = v_code
    and p.is_active = true
  limit 1;

  if v_pet_id is null then
    return array[]::text[];
  end if;

  select coalesce(array_agg(o.name order by o.name), array[]::text[])
    into v_paths
  from storage.objects o
  where o.bucket_id = 'pet-photos'
    and o.name like v_pet_id::text || '/%';

  return v_paths;
end;
$$;

revoke all on function public.list_my_pet_photo_paths(text) from public;
revoke all on function public.list_my_pet_photo_paths(text) from anon;
grant execute on function public.list_my_pet_photo_paths(text) to authenticated;
