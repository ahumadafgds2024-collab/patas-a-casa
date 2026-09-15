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

const SHARED_ACTIVATION_CODE = "PAC2011";
const DEFAULT_APP_ORIGIN = "https://patas-a-casa.vercel.app";
const ALLOWED_APP_ORIGINS = new Set([
  DEFAULT_APP_ORIGIN,
  "https://patasacasa.com.ar",
  "https://www.patasacasa.com.ar",
]);

const serviceHeaders = {
  apikey: SERVICE_KEY,
  Authorization: `Bearer ${SERVICE_KEY}`,
  "Content-Type": "application/json",
};

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "content-type, authorization, apikey",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
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

function activationCode(v: unknown) {
  return String(v ?? "").trim().toUpperCase().replace(/\s+/g, "").slice(0, 32);
}

function validActivationCode(v: unknown) {
  return activationCode(v) === SHARED_ACTIVATION_CODE;
}

function isSharedMode(tag: any) {
  // "qr" is accepted during the short migration window from the previous experiment.
  return tag?.activation_mode === "shared" || tag?.activation_mode === "qr";
}

function appOrigin(req: Request) {
  const origin = String(req.headers.get("origin") || "").replace(/\/+$/, "");
  return ALLOWED_APP_ORIGINS.has(origin) ? origin : DEFAULT_APP_ORIGIN;
}

function confirmUrl(req: Request, publicCode: string) {
  const url = new URL("/mi-cuenta/confirmar/", appOrigin(req));
  url.searchParams.set("chapita", code(publicCode));
  url.searchParams.set("modo", "shared");
  return url.toString();
}

async function tagByCode(c: string) {
  const r = await fetch(
    `${SUPABASE_URL}/rest/v1/tags?public_code=eq.${encodeURIComponent(c)}&select=id,public_code,pet_id,activated_at,blocked_at,activation_mode&limit=1`,
    { headers: serviceHeaders },
  );
  if (!r.ok) throw new Error(`tag_lookup_${r.status}`);
  const rows = await r.json();
  return rows?.[0] ?? null;
}

async function petById(id: string) {
  const r = await fetch(
    `${SUPABASE_URL}/rest/v1/pets?id=eq.${encodeURIComponent(id)}&select=id,public_code,owner_id,is_active&limit=1`,
    { headers: serviceHeaders },
  );
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

async function expireTagClaims(tagId: string) {
  const now = new Date().toISOString();
  const r = await fetch(
    `${SUPABASE_URL}/rest/v1/pending_owner_claims?tag_id=eq.${encodeURIComponent(tagId)}&consumed_at=is.null&expires_at=lt.${encodeURIComponent(now)}`,
    {
      method: "PATCH",
      headers: { ...serviceHeaders, Prefer: "return=minimal" },
      body: JSON.stringify({ consumed_at: now }),
    },
  );
  if (!r.ok) throw new Error(`expire_claims_${r.status}`);
}

async function pendingForTag(tagId: string) {
  const now = new Date().toISOString();
  const r = await fetch(
    `${SUPABASE_URL}/rest/v1/pending_owner_claims?tag_id=eq.${encodeURIComponent(tagId)}&consumed_at=is.null&expires_at=gt.${encodeURIComponent(now)}&select=id,auth_user_id,tag_id,public_code,email,expires_at&order=created_at.desc&limit=1`,
    { headers: serviceHeaders },
  );
  if (!r.ok) throw new Error(`pending_tag_${r.status}`);
  const rows = await r.json();
  return rows?.[0] ?? null;
}

async function pendingForUser(userId: string, c: string) {
  const now = new Date().toISOString();
  const r = await fetch(
    `${SUPABASE_URL}/rest/v1/pending_owner_claims?auth_user_id=eq.${encodeURIComponent(userId)}&public_code=eq.${encodeURIComponent(c)}&consumed_at=is.null&expires_at=gt.${encodeURIComponent(now)}&select=id,auth_user_id,tag_id,public_code,email,expires_at&order=created_at.desc&limit=1`,
    { headers: serviceHeaders },
  );
  if (!r.ok) throw new Error(`pending_user_${r.status}`);
  const rows = await r.json();
  return rows?.[0] ?? null;
}

async function extendClaim(id: string) {
  const r = await fetch(
    `${SUPABASE_URL}/rest/v1/pending_owner_claims?id=eq.${encodeURIComponent(id)}&consumed_at=is.null`,
    {
      method: "PATCH",
      headers: { ...serviceHeaders, Prefer: "return=representation" },
      body: JSON.stringify({ expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() }),
    },
  );
  const rows = r.ok ? await r.json() : [];
  return r.ok && Boolean(rows?.length);
}

async function createPending(userId: string, mail: string, tag: any, c: string) {
  const r = await fetch(`${SUPABASE_URL}/rest/v1/pending_owner_claims`, {
    method: "POST",
    headers: { ...serviceHeaders, Prefer: "return=representation" },
    body: JSON.stringify({
      auth_user_id: userId,
      tag_id: tag.id,
      pet_id: null,
      public_code: c,
      email: mail,
      expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    }),
  });
  const rows = r.ok ? await r.json() : [];
  return { ok: r.ok, status: r.status, row: rows?.[0] ?? null };
}

async function deleteAuthUser(userId: string) {
  try {
    const r = await fetch(`${SUPABASE_URL}/auth/v1/admin/users/${encodeURIComponent(userId)}`, {
      method: "DELETE",
      headers: serviceHeaders,
    });
    return r.ok || r.status === 404;
  } catch {
    return false;
  }
}

async function resendConfirmation(req: Request, mail: string, c: string) {
  const r = await fetch(
    `${SUPABASE_URL}/auth/v1/resend?redirect_to=${encodeURIComponent(confirmUrl(req, c))}`,
    {
      method: "POST",
      headers: { apikey: PUBLISHABLE_KEY, "Content-Type": "application/json" },
      body: JSON.stringify({ type: "signup", email: mail }),
    },
  );
  const result = await r.json().catch(() => ({}));
  if (r.ok) return { ok: true, status: 200, error: "" };
  const detail = String(result?.msg || result?.message || result?.error_description || "").toLowerCase();
  if (r.status === 429 || detail.includes("rate limit")) {
    return { ok: false, status: 429, error: "Esperá un minuto antes de pedir otro correo." };
  }
  if (detail.includes("already confirmed")) {
    return { ok: false, status: 409, error: "Ese correo ya está confirmado. Iniciá sesión para continuar." };
  }
  return { ok: false, status: 502, error: "No pudimos reenviar el correo en este momento." };
}

async function assertSharedTag(c: string) {
  const tag = await tagByCode(c);
  if (!tag || tag.blocked_at) return { error: json({ error: "Chapita no encontrada o bloqueada." }, 404), tag: null };
  if (!isSharedMode(tag)) return { error: json({ error: "Esta chapita usa el sistema anterior con PIN." }, 409), tag: null };
  return { error: null, tag };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });

  try {
    const url = new URL(req.url);
    if (req.method === "GET" && url.searchParams.get("action") === "is_shared") {
      const c = code(url.searchParams.get("code"));
      if (!c) return json({ shared: false });
      const tag = await tagByCode(c);
      return json({ shared: Boolean(tag && !tag.blocked_at && isSharedMode(tag)) });
    }

    if (req.method !== "POST") return json({ error: "Ruta no encontrada." }, 404);
    const body = await req.json();
    const action = String(body?.action || "");

    if (action === "validate_code") {
      const c = code(body.public_code);
      if (!c || !validActivationCode(body.activation_code)) {
        return json({ error: "Código de activación incorrecto." }, 403);
      }
      const checked = await assertSharedTag(c);
      if (checked.error) return checked.error;
      const tag = checked.tag;
      if (tag.pet_id || tag.activated_at) return json({ error: "Esta chapita ya fue activada." }, 409);
      return json({ ok: true, public_code: c });
    }

    if (action === "start_registration") {
      const c = code(body.public_code);
      const mail = email(body.email);
      const password = String(body.password ?? "");
      if (!c || !validActivationCode(body.activation_code)) {
        return json({ error: "Código de activación incorrecto." }, 403);
      }
      if (!/^\S+@\S+\.\S+$/.test(mail) || password.length < 8) {
        return json({ error: "Completá un email válido y una contraseña de al menos 8 caracteres." }, 400);
      }
      if (body.legal_consent !== true) {
        return json({ error: "Aceptá las condiciones de uso y la Política de Privacidad para continuar." }, 400);
      }

      const checked = await assertSharedTag(c);
      if (checked.error) return checked.error;
      const tag = checked.tag;
      if (tag.pet_id || tag.activated_at) {
        return json({ error: "Esta chapita ya fue activada. Iniciá sesión con la cuenta que la administra." }, 409);
      }

      await expireTagClaims(tag.id);
      const existing = await pendingForTag(tag.id);
      if (existing) {
        if (String(existing.email || "").toLowerCase() !== mail) {
          return json({ error: "Esta chapita ya tiene una activación pendiente con otro correo." }, 409);
        }
        if (!(await extendClaim(existing.id))) {
          return json({ error: "No pudimos renovar la activación. Volvé a intentarlo." }, 502);
        }
        const resent = await resendConfirmation(req, mail, c);
        if (!resent.ok) return json({ error: resent.error }, resent.status);
        return json({ ok: true, verification_required: true, resent: true, email: mail, public_code: c });
      }

      const signup = await fetch(
        `${SUPABASE_URL}/auth/v1/signup?redirect_to=${encodeURIComponent(confirmUrl(req, c))}`,
        {
          method: "POST",
          headers: { apikey: PUBLISHABLE_KEY, "Content-Type": "application/json" },
          body: JSON.stringify({
            email: mail,
            password,
            data: { source: "patas-a-casa", first_pet_code: c, activation_flow: "shared" },
          }),
        },
      );
      const created = await signup.json().catch(() => ({}));
      if (!signup.ok) {
        const detail = String(created?.msg || created?.message || created?.error_description || "").toLowerCase();
        if (signup.status === 422 || detail.includes("already") || detail.includes("registered")) {
          return json({ error: "Ese email ya tiene una cuenta. Iniciá sesión con esa cuenta." }, 409);
        }
        return json({ error: "No pudimos crear la cuenta ni enviar el correo de verificación." }, 502);
      }
      if (!created?.id || (Array.isArray(created?.identities) && created.identities.length === 0)) {
        return json({ error: "Ese email ya tiene una cuenta. Iniciá sesión con esa cuenta." }, 409);
      }

      const pending = await createPending(created.id, mail, tag, c);
      if (!pending.ok || !pending.row) {
        await deleteAuthUser(created.id);
        return json({ error: "No pudimos preparar la vinculación. Volvé a intentarlo." }, pending.status === 409 ? 409 : 500);
      }
      return json({ ok: true, verification_required: true, email: mail, public_code: c });
    }

    if (action === "resend_confirmation") {
      const c = code(body.public_code);
      const mail = email(body.email);
      if (!c || !/^\S+@\S+\.\S+$/.test(mail)) {
        return json({ error: "Ingresá una chapita y un email válido." }, 400);
      }
      const checked = await assertSharedTag(c);
      if (checked.error) return checked.error;
      await expireTagClaims(checked.tag.id);
      const pending = await pendingForTag(checked.tag.id);
      if (!pending || String(pending.email || "").toLowerCase() !== mail) {
        return json({ error: "No encontramos una verificación pendiente con esos datos." }, 404);
      }
      if (!(await extendClaim(pending.id))) {
        return json({ error: "No pudimos renovar la verificación. Volvé a intentarlo." }, 502);
      }
      const resent = await resendConfirmation(req, mail, c);
      if (!resent.ok) return json({ error: resent.error }, resent.status);
      return json({ ok: true, resent: true, email: mail, public_code: c });
    }

    if (action === "prepare_activation") {
      const user = await currentUser(req);
      if (!user?.id) return json({ error: "Sesión vencida. Volvé a ingresar." }, 401);
      if (!user.email || (!user.email_confirmed_at && !user.confirmed_at)) {
        return json({ error: "Primero verificá el correo de tu cuenta." }, 403);
      }
      const c = code(body.public_code);
      if (!c || !validActivationCode(body.activation_code)) {
        return json({ error: "Código de activación incorrecto." }, 403);
      }
      const checked = await assertSharedTag(c);
      if (checked.error) return checked.error;
      const tag = checked.tag;

      const fresh = !tag.pet_id && !tag.activated_at;
      const active = Boolean(tag.pet_id && tag.activated_at);
      if (!fresh && !active) {
        return json({ error: "La chapita tiene un estado incompleto. Contactanos para revisarla." }, 409);
      }
      if (active) {
        const pet = await petById(tag.pet_id);
        if (!pet) return json({ error: "No encontramos el perfil de esta mascota." }, 404);
        if (pet.owner_id === user.id) return json({ ok: true, linked: true, already: true, public_code: c });
        return json({ error: "Esta chapita ya pertenece a otra cuenta." }, 409);
      }

      await expireTagClaims(tag.id);
      const existing = await pendingForUser(user.id, c);
      if (existing) return json({ ok: true, profile_required: true, public_code: c });

      const other = await pendingForTag(tag.id);
      if (other && other.auth_user_id !== user.id) {
        return json({ error: "Esta chapita tiene una activación en curso con otra cuenta." }, 409);
      }

      const pending = await createPending(user.id, String(user.email || "").toLowerCase(), tag, c);
      if (!pending.ok || !pending.row) {
        return json({ error: "No pudimos preparar la activación. Volvé a intentarlo." }, 409);
      }
      return json({ ok: true, profile_required: true, public_code: c });
    }

    return json({ error: "Acción no encontrada." }, 404);
  } catch (error) {
    console.error(error);
    return json({ error: "Ocurrió un error interno. Volvé a intentarlo." }, 500);
  }
});
