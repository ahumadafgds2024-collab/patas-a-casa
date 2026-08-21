import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const PUBLISHABLE_KEY = (() => {
  try {
    const raw = Deno.env.get("SUPABASE_PUBLISHABLE_KEYS");
    if (raw) return JSON.parse(raw)?.default || Deno.env.get("SUPABASE_ANON_KEY")!;
  } catch {}
  return Deno.env.get("SUPABASE_ANON_KEY")!;
})();
const CONFIRM_URL = "https://patas-a-casa.vercel.app/mi-cuenta/confirmar/";

const serviceHeaders = {
  apikey: SERVICE_KEY,
  Authorization: `Bearer ${SERVICE_KEY}`,
  "Content-Type": "application/json",
};

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "content-type, authorization, apikey",
  "Access-Control-Allow-Methods": "POST,OPTIONS",
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
};

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...cors, "Content-Type": "application/json; charset=utf-8" },
  });
}

function code(v: unknown) {
  return String(v ?? "").trim().toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 12);
}
function email(v: unknown) {
  return String(v ?? "").trim().toLowerCase().slice(0, 254);
}

async function tagByCode(c: string) {
  const r = await fetch(`${SUPABASE_URL}/rest/v1/tags?public_code=eq.${encodeURIComponent(c)}&select=id,public_code,pet_id,activated_at,blocked_at&limit=1`, { headers: serviceHeaders });
  if (!r.ok) throw new Error(`tag_lookup_${r.status}`);
  const rows = await r.json();
  return rows?.[0] ?? null;
}

async function verifyPin(c: string, pin: string) {
  const r = await fetch(`${SUPABASE_URL}/rest/v1/rpc/verify_tag_activation`, {
    method: "POST",
    headers: serviceHeaders,
    body: JSON.stringify({ p_public_code: c, p_activation_code: pin }),
  });
  return r.ok && Boolean(await r.json());
}

async function petById(id: string) {
  const r = await fetch(`${SUPABASE_URL}/rest/v1/pets?id=eq.${encodeURIComponent(id)}&select=id,public_code,owner_id,is_active&limit=1`, { headers: serviceHeaders });
  if (!r.ok) throw new Error(`pet_lookup_${r.status}`);
  const rows = await r.json();
  return rows?.[0] ?? null;
}

async function currentUser(req: Request) {
  const auth = req.headers.get("Authorization") || "";
  if (!auth.toLowerCase().startsWith("bearer ")) return null;
  const r = await fetch(`${SUPABASE_URL}/auth/v1/user`, {
    headers: { apikey: SERVICE_KEY, Authorization: auth },
  });
  if (!r.ok) return null;
  return await r.json();
}

async function pendingForUser(userId: string) {
  const r = await fetch(
    `${SUPABASE_URL}/rest/v1/pending_owner_claims?auth_user_id=eq.${encodeURIComponent(userId)}&consumed_at=is.null&select=id,auth_user_id,tag_id,pet_id,public_code,email,expires_at,created_at&order=created_at.desc&limit=1`,
    { headers: serviceHeaders },
  );
  if (!r.ok) throw new Error(`pending_lookup_${r.status}`);
  const rows = await r.json();
  return rows?.[0] ?? null;
}

async function markConsumed(id: string, userId: string) {
  await fetch(`${SUPABASE_URL}/rest/v1/pending_owner_claims?id=eq.${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { ...serviceHeaders, Prefer: "return=minimal" },
    body: JSON.stringify({ consumed_at: new Date().toISOString(), auth_user_id: userId }),
  });
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "Ruta no encontrada" }, 404);

  try {
    const b = await req.json().catch(() => ({}));

    if (b.action === "start_registration") {
      const c = code(b.public_code);
      const pin = String(b.activation_code ?? "").trim().slice(0, 50);
      const mail = email(b.email);
      const password = String(b.password ?? "");

      if (!c || !pin || !mail || password.length < 8) {
        return json({ error: "Completá código, PIN, email y una contraseña de al menos 8 caracteres." }, 400);
      }
      if (!/^\S+@\S+\.\S+$/.test(mail)) return json({ error: "Ingresá un email válido." }, 400);

      const tag = await tagByCode(c);
      if (!tag || tag.blocked_at) return json({ error: "Chapita no encontrada o bloqueada." }, 404);
      if (!(await verifyPin(c, pin))) return json({ error: "PIN incorrecto." }, 403);

      const freshTag = !tag.pet_id && !tag.activated_at;
      const activeTag = Boolean(tag.pet_id && tag.activated_at);
      if (!freshTag && !activeTag) return json({ error: "La chapita tiene un estado incompleto. Contactanos para revisarla." }, 409);

      let pet: any = null;
      if (activeTag) {
        pet = await petById(tag.pet_id);
        if (!pet) return json({ error: "No encontramos el perfil de esta mascota." }, 404);
        if (pet.owner_id) return json({ error: "Esta mascota ya está vinculada a una cuenta. Iniciá sesión con esa cuenta." }, 409);
      }

      const signup = await fetch(`${SUPABASE_URL}/auth/v1/signup?redirect_to=${encodeURIComponent(CONFIRM_URL)}`, {
        method: "POST",
        headers: { apikey: PUBLISHABLE_KEY, "Content-Type": "application/json" },
        body: JSON.stringify({
          email: mail,
          password,
          data: { source: "patas-a-casa", first_pet_code: c },
        }),
      });
      const created = await signup.json().catch(() => ({}));

      if (!signup.ok) {
        const msg = String(created?.msg || created?.message || created?.error_description || "").toLowerCase();
        if (signup.status === 422 || msg.includes("already") || msg.includes("registered")) {
          return json({ error: "Ese email ya tiene una cuenta. Iniciá sesión o usá ‘¿Olvidaste tu contraseña?’." }, 409);
        }
        return json({ error: "No pudimos crear la cuenta ni enviar el correo de verificación." }, 500);
      }

      if (!created?.id || (Array.isArray(created?.identities) && created.identities.length === 0)) {
        return json({ error: "Ese email ya tiene una cuenta. Iniciá sesión o recuperá tu contraseña." }, 409);
      }

      const pending = await fetch(`${SUPABASE_URL}/rest/v1/pending_owner_claims`, {
        method: "POST",
        headers: { ...serviceHeaders, Prefer: "return=representation" },
        body: JSON.stringify({
          auth_user_id: created.id,
          tag_id: tag.id,
          pet_id: pet?.id ?? null,
          public_code: c,
          email: mail,
          expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        }),
      });
      const rows = pending.ok ? await pending.json() : [];

      if (!pending.ok || !rows?.length) {
        await fetch(`${SUPABASE_URL}/auth/v1/admin/users/${encodeURIComponent(created.id)}`, {
          method: "DELETE",
          headers: serviceHeaders,
        }).catch(() => {});
        return json({ error: "No pudimos preparar la vinculación. La cuenta fue cancelada; volvé a intentar." }, 500);
      }

      return json({ ok: true, verification_required: true, email: mail, public_code: c });
    }

    if (b.action === "finalize_registration") {
      const user = await currentUser(req);
      if (!user?.id) return json({ error: "Sesión vencida. Volvé a ingresar." }, 401);
      if (!user.email_confirmed_at && !user.confirmed_at) {
        return json({ error: "Primero confirmá tu correo electrónico." }, 403);
      }

      const pending = await pendingForUser(user.id);
      if (!pending) return json({ ok: true, pending: false, linked: false });
      if (String(pending.email || "").toLowerCase() !== String(user.email || "").toLowerCase()) {
        return json({ error: "La verificación no coincide con esta cuenta." }, 403);
      }
      if (new Date(pending.expires_at).getTime() < Date.now()) {
        return json({ error: "La vinculación pendiente venció. Volvé a iniciar el registro de la chapita." }, 410);
      }

      if (!pending.pet_id) {
        return json({
          ok: true,
          pending: true,
          linked: false,
          profile_required: true,
          public_code: pending.public_code,
        });
      }

      const pet = await petById(pending.pet_id);
      if (!pet) return json({ error: "No encontramos la mascota pendiente." }, 404);
      if (pet.owner_id && pet.owner_id !== user.id) {
        await markConsumed(pending.id, user.id);
        return json({ error: "Esta mascota ya fue vinculada a otra cuenta." }, 409);
      }
      if (pet.owner_id === user.id) {
        await markConsumed(pending.id, user.id);
        return json({ ok: true, pending: false, linked: true, already: true, public_code: pending.public_code });
      }

      const link = await fetch(`${SUPABASE_URL}/rest/v1/pets?id=eq.${encodeURIComponent(pending.pet_id)}&owner_id=is.null`, {
        method: "PATCH",
        headers: { ...serviceHeaders, Prefer: "return=representation" },
        body: JSON.stringify({ owner_id: user.id, updated_at: new Date().toISOString() }),
      });
      const linked = link.ok ? await link.json() : [];
      if (!link.ok || !linked?.length) return json({ error: "No pudimos vincular la mascota a tu cuenta." }, 409);

      await markConsumed(pending.id, user.id);
      return json({ ok: true, pending: false, linked: true, public_code: pending.public_code });
    }

    return json({ error: "Acción no encontrada." }, 404);
  } catch (e) {
    console.error(e);
    return json({ error: e instanceof Error ? e.message : "Error interno" }, 500);
  }
});
