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
const DEFAULT_APP_ORIGIN = "https://patas-a-casa.vercel.app";
const ALLOWED_APP_ORIGINS = new Set([
  DEFAULT_APP_ORIGIN,
  "https://patasacasa.com.ar",
  "https://www.patasacasa.com.ar",
]);
const FUNCTION_NAME = "patas-register-v2";
const MAX_BODY_BYTES = 64 * 1024;
const FETCH_TIMEOUT_MS = 15_000;

const serviceHeaders = {
  apikey: SERVICE_KEY,
  Authorization: `Bearer ${SERVICE_KEY}`,
  "Content-Type": "application/json",
};

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "content-type, authorization, apikey, x-request-id",
  "Access-Control-Allow-Methods": "POST,OPTIONS",
  "Access-Control-Expose-Headers": "X-Request-Id",
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
};

type RequestContext = {
  id: string;
  method: string;
  action: string;
  status: number;
  startedAt: number;
};

class HttpError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function requestId(req: Request) {
  const supplied = req.headers.get("x-request-id") || "";
  return /^[A-Za-z0-9_-]{8,80}$/.test(supplied) ? supplied : crypto.randomUUID();
}

function appOrigin(req: Request) {
  const origin = String(req.headers.get("origin") || "").replace(/\/+$/, "");
  return ALLOWED_APP_ORIGINS.has(origin) ? origin : DEFAULT_APP_ORIGIN;
}

function confirmUrl(req: Request, publicCode = "") {
  const url = new URL("/mi-cuenta/confirmar/", appOrigin(req));
  if (publicCode) url.searchParams.set("chapita", code(publicCode));
  return url.toString();
}

function json(ctx: RequestContext, data: Record<string, unknown>, status = 200) {
  ctx.status = status;
  const body = status >= 400 ? { ...data, request_id: ctx.id } : data;
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors, "Content-Type": "application/json; charset=utf-8", "X-Request-Id": ctx.id },
  });
}

function logRequest(ctx: RequestContext) {
  console.log(JSON.stringify({
    event: "request_complete",
    function: FUNCTION_NAME,
    request_id: ctx.id,
    method: ctx.method,
    action: ctx.action || "unknown",
    status: ctx.status,
    duration_ms: Math.round(performance.now() - ctx.startedAt),
  }));
}

function logDependency(ctx: RequestContext, dependency: string, operation: string, status: number | string) {
  console.error(JSON.stringify({
    event: "dependency_error",
    function: FUNCTION_NAME,
    request_id: ctx.id,
    dependency,
    operation,
    status,
  }));
}

async function fetchWithTimeout(url: string, init: RequestInit = {}, timeoutMs = FETCH_TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function readJson(req: Request) {
  const declared = Number(req.headers.get("content-length") || 0);
  if (declared > MAX_BODY_BYTES) throw new HttpError("La solicitud es demasiado grande", 413);
  const raw = await req.text();
  if (new TextEncoder().encode(raw).byteLength > MAX_BODY_BYTES) {
    throw new HttpError("La solicitud es demasiado grande", 413);
  }
  try {
    return JSON.parse(raw || "{}");
  } catch {
    throw new HttpError("La solicitud no tiene un formato válido", 400);
  }
}

function code(v: unknown) {
  return String(v ?? "").trim().toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 12);
}

function activationPin(v: unknown) {
  const raw = String(v ?? "").trim().slice(0, 50);
  return /^\d{8}$/.test(raw) ? `${raw.slice(0, 4)}-${raw.slice(4)}` : raw;
}

function email(v: unknown) {
  return String(v ?? "").trim().toLowerCase().slice(0, 254);
}

async function tagByCode(ctx: RequestContext, c: string) {
  const r = await fetchWithTimeout(
    `${SUPABASE_URL}/rest/v1/tags?public_code=eq.${encodeURIComponent(c)}&select=id,public_code,pet_id,activated_at,blocked_at&limit=1`,
    { headers: serviceHeaders },
  );
  if (!r.ok) {
    logDependency(ctx, "postgres", "tag_lookup", r.status);
    throw new Error("tag_lookup_failed");
  }
  const rows = await r.json();
  return rows?.[0] ?? null;
}

async function verifyPin(ctx: RequestContext, c: string, pin: string) {
  const r = await fetchWithTimeout(`${SUPABASE_URL}/rest/v1/rpc/verify_tag_activation`, {
    method: "POST",
    headers: serviceHeaders,
    body: JSON.stringify({ p_public_code: c, p_activation_code: activationPin(pin) }),
  });
  if (!r.ok) {
    logDependency(ctx, "postgres", "verify_tag_activation", r.status);
    throw new Error("pin_verification_failed");
  }
  return Boolean(await r.json());
}

async function petById(ctx: RequestContext, id: string) {
  const r = await fetchWithTimeout(
    `${SUPABASE_URL}/rest/v1/pets?id=eq.${encodeURIComponent(id)}&select=id,public_code,owner_id,is_active&limit=1`,
    { headers: serviceHeaders },
  );
  if (!r.ok) {
    logDependency(ctx, "postgres", "pet_lookup", r.status);
    throw new Error("pet_lookup_failed");
  }
  const rows = await r.json();
  return rows?.[0] ?? null;
}

async function currentUser(ctx: RequestContext, req: Request) {
  const auth = req.headers.get("Authorization") || "";
  if (!auth.toLowerCase().startsWith("bearer ")) return null;
  const r = await fetchWithTimeout(`${SUPABASE_URL}/auth/v1/user`, {
    headers: { apikey: SERVICE_KEY, Authorization: auth },
  });
  if (r.status === 401 || r.status === 403) return null;
  if (!r.ok) {
    logDependency(ctx, "auth", "current_user", r.status);
    throw new Error("auth_lookup_failed");
  }
  return await r.json();
}

async function pendingForUser(ctx: RequestContext, userId: string) {
  const r = await fetchWithTimeout(
    `${SUPABASE_URL}/rest/v1/pending_owner_claims?auth_user_id=eq.${encodeURIComponent(userId)}&consumed_at=is.null&select=id,auth_user_id,tag_id,pet_id,public_code,email,expires_at,created_at&order=created_at.desc&limit=1`,
    { headers: serviceHeaders },
  );
  if (!r.ok) {
    logDependency(ctx, "postgres", "pending_lookup", r.status);
    throw new Error("pending_lookup_failed");
  }
  const rows = await r.json();
  return rows?.[0] ?? null;
}

async function pendingForTag(ctx: RequestContext, tagId: string) {
  const r = await fetchWithTimeout(
    `${SUPABASE_URL}/rest/v1/pending_owner_claims?tag_id=eq.${encodeURIComponent(tagId)}&consumed_at=is.null&select=id,auth_user_id,public_code,email,expires_at&limit=1`,
    { headers: serviceHeaders },
  );
  if (!r.ok) {
    logDependency(ctx, "postgres", "pending_tag_lookup", r.status);
    throw new Error("pending_tag_lookup_failed");
  }
  const rows = await r.json();
  return rows?.[0] ?? null;
}

async function extendClaim(ctx: RequestContext, claimId: string) {
  const r = await fetchWithTimeout(
    `${SUPABASE_URL}/rest/v1/pending_owner_claims?id=eq.${encodeURIComponent(claimId)}&consumed_at=is.null`,
    {
      method: "PATCH",
      headers: { ...serviceHeaders, Prefer: "return=representation" },
      body: JSON.stringify({ expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() }),
    },
  );
  if (!r.ok) {
    logDependency(ctx, "postgres", "extend_pending_claim", r.status);
    return false;
  }
  const rows = await r.json();
  return Boolean(rows?.length);
}

async function resendConfirmation(ctx: RequestContext, req: Request, mail: string, publicCode: string) {
  const r = await fetchWithTimeout(
    `${SUPABASE_URL}/auth/v1/resend?redirect_to=${encodeURIComponent(confirmUrl(req, publicCode))}`,
    {
      method: "POST",
      headers: { apikey: PUBLISHABLE_KEY, "Content-Type": "application/json" },
      body: JSON.stringify({ type: "signup", email: mail }),
    },
    20_000,
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
  logDependency(ctx, "auth", "resend_confirmation", r.status);
  return { ok: false, status: 502, error: "No pudimos reenviar el correo en este momento. Probá nuevamente en unos minutos." };
}

async function expireTagClaims(ctx: RequestContext, tagId: string) {
  const now = new Date().toISOString();
  const r = await fetchWithTimeout(
    `${SUPABASE_URL}/rest/v1/pending_owner_claims?tag_id=eq.${encodeURIComponent(tagId)}&consumed_at=is.null&expires_at=lt.${encodeURIComponent(now)}`,
    {
      method: "PATCH",
      headers: { ...serviceHeaders, Prefer: "return=minimal" },
      body: JSON.stringify({ consumed_at: now }),
    },
  );
  if (!r.ok) {
    logDependency(ctx, "postgres", "expire_tag_claims", r.status);
    throw new Error("expire_tag_claims_failed");
  }
}

async function markConsumed(ctx: RequestContext, id: string, userId: string) {
  const r = await fetchWithTimeout(
    `${SUPABASE_URL}/rest/v1/pending_owner_claims?id=eq.${encodeURIComponent(id)}&auth_user_id=eq.${encodeURIComponent(userId)}&consumed_at=is.null`,
    {
      method: "PATCH",
      headers: { ...serviceHeaders, Prefer: "return=representation" },
      body: JSON.stringify({ consumed_at: new Date().toISOString() }),
    },
  );
  if (!r.ok) {
    logDependency(ctx, "postgres", "mark_claim_consumed", r.status);
    return false;
  }
  const rows = await r.json();
  return Boolean(rows?.length);
}

async function deleteAuthUser(ctx: RequestContext, userId: string) {
  try {
    const r = await fetchWithTimeout(
      `${SUPABASE_URL}/auth/v1/admin/users/${encodeURIComponent(userId)}`,
      { method: "DELETE", headers: serviceHeaders },
    );
    if (r.ok || r.status === 404) return true;
    logDependency(ctx, "auth", "registration_rollback", r.status);
  } catch (error) {
    logDependency(ctx, "auth", "registration_rollback", error instanceof Error ? error.name : "UnknownError");
  }
  return false;
}

Deno.serve(async (req) => {
  const ctx: RequestContext = {
    id: requestId(req),
    method: req.method,
    action: "",
    status: 500,
    startedAt: performance.now(),
  };

  try {
    if (req.method === "OPTIONS") {
      ctx.action = "preflight";
      ctx.status = 204;
      return new Response(null, { status: 204, headers: { ...cors, "X-Request-Id": ctx.id } });
    }
    if (req.method !== "POST") return json(ctx, { error: "Ruta no encontrada" }, 404);

    const body = await readJson(req);
    ctx.action = String(body?.action || "").slice(0, 40);

    if (ctx.action === "resend_confirmation") {
      const c = code(body.public_code);
      const mail = email(body.email);
      if (!c || !/^\S+@\S+\.\S+$/.test(mail)) {
        return json(ctx, { error: "Ingresá el código de la chapita y un email válido." }, 400);
      }
      const tag = await tagByCode(ctx, c);
      const pending = tag && !tag.blocked_at ? await pendingForTag(ctx, tag.id) : null;
      if (!pending || String(pending.email || "").toLowerCase() !== mail) {
        return json(ctx, { error: "No encontramos una verificación pendiente con esos datos." }, 404);
      }
      if (!(await extendClaim(ctx, pending.id))) {
        return json(ctx, { error: "No pudimos renovar la verificación. Probá nuevamente." }, 502);
      }
      const sent = await resendConfirmation(ctx, req, mail, c);
      if (!sent.ok) return json(ctx, { error: sent.error }, sent.status);
      return json(ctx, { ok: true, resent: true, email: mail, public_code: c });
    }

    if (ctx.action === "start_registration") {
      const c = code(body.public_code);
      const pin = String(body.activation_code ?? "").trim().slice(0, 50);
      const mail = email(body.email);
      const password = String(body.password ?? "");

      if (!c || !pin || !mail || password.length < 8) {
        return json(ctx, { error: "Completá código, PIN, email y una contraseña de al menos 8 caracteres." }, 400);
      }
      if (!/^\S+@\S+\.\S+$/.test(mail)) return json(ctx, { error: "Ingresá un email válido." }, 400);

      const tag = await tagByCode(ctx, c);
      if (!tag || tag.blocked_at) return json(ctx, { error: "Chapita no encontrada o bloqueada." }, 404);
      if (!(await verifyPin(ctx, c, pin))) return json(ctx, { error: "PIN incorrecto." }, 403);

      const freshTag = !tag.pet_id && !tag.activated_at;
      const activeTag = Boolean(tag.pet_id && tag.activated_at);
      if (!freshTag && !activeTag) {
        return json(ctx, { error: "La chapita tiene un estado incompleto. Contactanos para revisarla." }, 409);
      }

      let pet: any = null;
      if (activeTag) {
        pet = await petById(ctx, tag.pet_id);
        if (!pet) return json(ctx, { error: "No encontramos el perfil de esta mascota." }, 404);
        if (pet.owner_id) {
          return json(ctx, { error: "Esta mascota ya está vinculada a una cuenta. Iniciá sesión con esa cuenta." }, 409);
        }
      }

      await expireTagClaims(ctx, tag.id);
      const existingPending = await pendingForTag(ctx, tag.id);
      if (existingPending) {
        if (String(existingPending.email || "").toLowerCase() !== mail) {
          return json(ctx, { error: "Esta chapita ya tiene una activación pendiente con otro correo. Contactanos para revisarla." }, 409);
        }
        if (!(await extendClaim(ctx, existingPending.id))) {
          return json(ctx, { error: "No pudimos renovar la verificación. Probá nuevamente." }, 502);
        }
        const sent = await resendConfirmation(ctx, req, mail, c);
        if (!sent.ok) return json(ctx, { error: sent.error }, sent.status);
        return json(ctx, { ok: true, verification_required: true, resent: true, email: mail, public_code: c });
      }
      const signup = await fetchWithTimeout(
        `${SUPABASE_URL}/auth/v1/signup?redirect_to=${encodeURIComponent(confirmUrl(req, c))}`,
        {
          method: "POST",
          headers: { apikey: PUBLISHABLE_KEY, "Content-Type": "application/json" },
          body: JSON.stringify({
            email: mail,
            password,
            data: { source: "patas-a-casa", first_pet_code: c },
          }),
        },
        20_000,
      );
      const created = await signup.json().catch(() => ({}));

      if (!signup.ok) {
        const message = String(created?.msg || created?.message || created?.error_description || "").toLowerCase();
        if (signup.status === 422 || message.includes("already") || message.includes("registered")) {
          return json(ctx, { error: "Ese email ya tiene una cuenta. Iniciá sesión o usá ‘¿Olvidaste tu contraseña?’." }, 409);
        }
        logDependency(ctx, "auth", "signup", signup.status);
        return json(ctx, { error: "No pudimos crear la cuenta ni enviar el correo de verificación." }, 502);
      }

      if (!created?.id || (Array.isArray(created?.identities) && created.identities.length === 0)) {
        return json(ctx, { error: "Ese email ya tiene una cuenta. Iniciá sesión o recuperá tu contraseña." }, 409);
      }

      const pending = await fetchWithTimeout(`${SUPABASE_URL}/rest/v1/pending_owner_claims`, {
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
        if (!pending.ok) logDependency(ctx, "postgres", "create_pending_claim", pending.status);
        const rolledBack = await deleteAuthUser(ctx, created.id);
        if (pending.status === 409) {
          return json(ctx, { error: "Esta chapita ya tiene una activación pendiente. Esperá a que venza o contactanos." }, 409);
        }
        const message = rolledBack
          ? "No pudimos preparar la vinculación. La cuenta fue cancelada; volvé a intentar."
          : "No pudimos completar el registro. Contactanos con la referencia de este error.";
        return json(ctx, { error: message }, 500);
      }

      return json(ctx, { ok: true, verification_required: true, email: mail, public_code: c });
    }

    if (ctx.action === "finalize_registration") {
      const user = await currentUser(ctx, req);
      if (!user?.id) return json(ctx, { error: "Sesión vencida. Volvé a ingresar." }, 401);
      if (!user.email_confirmed_at && !user.confirmed_at) {
        return json(ctx, { error: "Primero confirmá tu correo electrónico." }, 403);
      }

      const pending = await pendingForUser(ctx, user.id);
      if (!pending) return json(ctx, { ok: true, pending: false, linked: false });
      if (String(pending.email || "").toLowerCase() !== String(user.email || "").toLowerCase()) {
        return json(ctx, { error: "La verificación no coincide con esta cuenta." }, 403);
      }
      if (new Date(pending.expires_at).getTime() < Date.now()) {
        return json(ctx, { error: "La vinculación pendiente venció. Volvé a iniciar el registro de la chapita." }, 410);
      }

      if (!pending.pet_id) {
        return json(ctx, {
          ok: true,
          pending: true,
          linked: false,
          profile_required: true,
          public_code: pending.public_code,
        });
      }

      const pet = await petById(ctx, pending.pet_id);
      if (!pet) return json(ctx, { error: "No encontramos la mascota pendiente." }, 404);
      if (pet.owner_id && pet.owner_id !== user.id) {
        await markConsumed(ctx, pending.id, user.id);
        return json(ctx, { error: "Esta mascota ya fue vinculada a otra cuenta." }, 409);
      }
      if (pet.owner_id === user.id) {
        await markConsumed(ctx, pending.id, user.id);
        return json(ctx, { ok: true, pending: false, linked: true, already: true, public_code: pending.public_code });
      }

      const link = await fetchWithTimeout(
        `${SUPABASE_URL}/rest/v1/pets?id=eq.${encodeURIComponent(pending.pet_id)}&owner_id=is.null`,
        {
          method: "PATCH",
          headers: { ...serviceHeaders, Prefer: "return=representation" },
          body: JSON.stringify({ owner_id: user.id, updated_at: new Date().toISOString() }),
        },
      );
      const linked = link.ok ? await link.json() : [];
      if (!link.ok || !linked?.length) {
        if (!link.ok) logDependency(ctx, "postgres", "link_existing_pet", link.status);
        return json(ctx, { error: "No pudimos vincular la mascota a tu cuenta." }, 409);
      }

      await markConsumed(ctx, pending.id, user.id);
      return json(ctx, { ok: true, pending: false, linked: true, public_code: pending.public_code });
    }

    return json(ctx, { error: "Acción no encontrada." }, 404);
  } catch (error) {
    if (error instanceof HttpError) return json(ctx, { error: error.message }, error.status);
    console.error(JSON.stringify({
      event: "request_error",
      function: FUNCTION_NAME,
      request_id: ctx.id,
      action: ctx.action || "unknown",
      error_type: error instanceof Error ? error.name : "UnknownError",
    }));
    return json(ctx, { error: "Error interno" }, 500);
  } finally {
    logRequest(ctx);
  }
});
