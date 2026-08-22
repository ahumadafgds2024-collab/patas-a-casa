-- The first pet is created only after the owner confirms their email.
-- Existing claims keep their pet_id; new activation claims may leave it null
-- until the verified owner submits the pet profile.
alter table public.pending_owner_claims
  alter column pet_id drop not null;

comment on column public.pending_owner_claims.pet_id is
  'Pet linked to the claim; null while a verified owner still needs to create the first pet profile.';
