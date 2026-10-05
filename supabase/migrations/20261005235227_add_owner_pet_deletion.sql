create policy "pet_owner_list_photos_for_delete"
on storage.objects
for select
to authenticated
using (
  storage.allow_only_operation('object.list')
  and bucket_id = 'pet-photos'
  and exists (
    select 1
    from public.pets p
    where p.owner_id = (select auth.uid())
      and p.is_active = true
      and p.id::text = (storage.foldername(name))[1]
  )
);

create policy "pet_owner_delete_own_photos"
on storage.objects
for delete
to authenticated
using (
  bucket_id = 'pet-photos'
  and exists (
    select 1
    from public.pets p
    where p.owner_id = (select auth.uid())
      and p.is_active = true
      and p.id::text = (storage.foldername(name))[1]
  )
);

create or replace function public.delete_my_pet(p_public_code text)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_user_id uuid := auth.uid();
  v_code text := upper(btrim(coalesce(p_public_code, '')));
  v_pet_id uuid;
begin
  if v_user_id is null then
    raise exception 'Sesión vencida. Volvé a ingresar.' using errcode = '42501';
  end if;

  if v_code = '' then
    return false;
  end if;

  select p.id
    into v_pet_id
  from public.pets p
  where p.owner_id = v_user_id
    and p.public_code = v_code
    and p.is_active = true
  for update;

  if v_pet_id is null then
    return false;
  end if;

  delete from public.sightings
  where pet_public_code = v_code;

  delete from public.pending_owner_claims
  where pet_id = v_pet_id;

  update public.tags
  set pet_id = null,
      activated_at = null
  where pet_id = v_pet_id;

  delete from public.pets
  where id = v_pet_id
    and owner_id = v_user_id;

  return found;
end;
$$;

revoke all on function public.delete_my_pet(text) from public;
revoke all on function public.delete_my_pet(text) from anon;
grant execute on function public.delete_my_pet(text) to authenticated;
