-- Separate the new shared-code flow from both the legacy per-tag PIN flow
-- and the short-lived QR-without-code experiment.

alter table public.tags
  drop constraint if exists tags_activation_mode_check;

alter table public.tags
  add constraint tags_activation_mode_check
  check (activation_mode in ('pin', 'qr', 'shared'));

-- These are the two tags used in the new-flow rollout.
-- Do not touch their activation_hash: the shared code is only an activation gate,
-- never the credential used by legacy owner-edit endpoints.
update public.tags
set activation_mode = 'shared'
where public_code in ('A09215F0', '36C76BB2')
  and activation_mode = 'qr';

comment on column public.tags.activation_mode is
  'pin = legacy private PIN; shared = shared activation code + unique QR; qr = deprecated QR-only experiment.';
