create schema if not exists private;

revoke all on schema private from public;
grant usage on schema private to authenticated;

create or replace function private.user_owns_pet_folder(p_folder text)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.pets p
    where p.owner_id = auth.uid()
      and p.is_active = true
      and p.id::text = p_folder
  );
$$;

revoke all on function private.user_owns_pet_folder(text) from public;
grant execute on function private.user_owns_pet_folder(text) to authenticated;

drop policy if exists "pet_owner_list_photos_for_delete" on storage.objects;
drop policy if exists "pet_owner_delete_own_photos" on storage.objects;

create policy "pet_owner_list_photos_for_delete"
on storage.objects
for select
to authenticated
using (
  storage.allow_only_operation('object.list')
  and bucket_id = 'pet-photos'
  and private.user_owns_pet_folder((storage.foldername(name))[1])
);

create policy "pet_owner_delete_own_photos"
on storage.objects
for delete
to authenticated
using (
  bucket_id = 'pet-photos'
  and private.user_owns_pet_folder((storage.foldername(name))[1])
);
