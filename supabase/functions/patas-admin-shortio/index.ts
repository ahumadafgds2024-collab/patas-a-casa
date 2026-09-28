import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const LEGACY_APP_ORIGIN = "https://patas-a-casa.vercel.app";
const NEW_TAG_ORIGIN = "https://www.patasacasa.com.ar";
const ALLOWED_ORIGINS = new Set([
  LEGACY_APP_ORIGIN,
  "https://patasacasa.com.ar",
  "https://www.patasacasa.com.ar",
]);
const BASE_TAG_URL = `${NEW_TAG_ORIGIN}/?tag=`;
const SHORT_API = "https://api.short.io/links";
const ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
const FUNCTION_NAME = "patas-admin-shortio";
const MAX_BODY_BYTES = 32 * 1024;
const MAX_BATCH_SIZE = 30;
const FETCH_TIMEOUT_MS = 12_000;

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

function cors(req: Request) {
  const origin = req.headers.get("origin") || "";
  const allowedOrigin = ALLOWED_ORIGINS.has(origin) ? origin : LEGACY_APP_ORIGIN;
  return {
    "Access-Control-Allow-Origin": allowedOrigin,
    "Access-Control-Allow-Headers": "content-type, x-request-id",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
    "Access-Control-Expose-Headers": "X-Request-Id",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Vary": "Origin",
  };
}

function json(req: Request, ctx: RequestContext, data: Record<string, unknown>, status = 200) {
  ctx.status = status;
  const body = status >= 400
    ? { ...data, error: `${String(data.error || "Error") } Referencia: ${ctx.id}`, request_id: ctx.id }
    : data;
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors(req), "Content-Type": "application/json; charset=utf-8", "X-Request-Id": ctx.id },
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

function normalizeDomain(value: unknown) {
  const domain = String(value ?? "").trim().toLowerCase().replace(/^https?:\/\//, "").replace(/\/+$/, "");
  if (!/^[a-z0-9-]+\.s\.gy$/.test(domain)) {
    throw new HttpError("Usá un subdominio gratuito de Short.io terminado en .s.gy", 400);
  }
  const prefix = `HTTPS://${domain.toUpperCase()}/`;
  const slugLength = Math.min(8, 25 - prefix.length);
  if (slugLength < 5) throw new HttpError("Ese dominio es demasiado largo para mantener el QR en 21×21", 400);
  return { domain, slugLength };
}

function randomSlug(length: number) {
  const bytes = new Uint8Array(length);
  crypto.getRandomValues(bytes);
  let out = "";
  for (const byte of bytes) out += ALPHABET[byte % ALPHABET.length];
  return out;
}

function sameTarget(a: string, b: string) {
  try {
    const x = new URL(a);
    const y = new URL(b);
    return x.protocol === y.protocol &&
      x.hostname.toLowerCase() === y.hostname.toLowerCase() &&
      x.pathname === y.pathname &&
      x.search === y.search;
  } catch {
    return false;
  }
}

async function deleteShortLink(ctx: RequestContext, apiKey: string, id: string) {
  if (!id) return false;
  try {
    const r = await fetchWithTimeout(`${SHORT_API}/${encodeURIComponent(id)}`, {
      method: "DELETE",
      headers: { Authorization: apiKey, Accept: "application/json" },
    });
    if (r.ok || r.status === 404) return true;
    logDependency(ctx, "shortio", "delete_link", r.status);
  } catch (error) {
    logDependency(ctx, "shortio", "delete_link", error instanceof Error ? error.name : "UnknownError");
  }
  return false;
}

async function createShortLink(
  ctx: RequestContext,
  apiKey: string,
  domain: string,
  slugLength: number,
  target: string,
) {
  let lastError = "No se pudo crear el enlace Short.io";
  for (let attempt = 0; attempt < 12; attempt++) {
    const path = randomSlug(slugLength);
    const r = await fetchWithTimeout(SHORT_API, {
      method: "POST",
      headers: {
        Authorization: apiKey,
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ originalURL: target, domain, path, allowDuplicates: false }),
    });
    const text = await r.text();
    let data: any = {};
    try {
      data = JSON.parse(text);
    } catch {}

    if (r.ok && data?.success !== false) {
      const returnedPath = String(data?.path || "");
      const externalId = String(data?.idString || data?.id || "");
      const shortUrl = String(data?.secureShortURL || data?.shortURL || `https://${domain}/${path}`);
      let parsed: URL;
      try {
        parsed = new URL(shortUrl);
      } catch {
        throw new Error("Short.io devolvió un enlace inválido");
      }
      if (
        parsed.protocol !== "https:" ||
        parsed.hostname.toLowerCase() !== domain ||
        parsed.pathname.replace(/^\//, "") !== path ||
        (returnedPath && returnedPath !== path)
      ) {
        if (externalId) await deleteShortLink(ctx, apiKey, externalId);
        throw new Error("Short.io devolvió una ruta distinta a la solicitada");
      }
      if (data?.originalURL && !sameTarget(String(data.originalURL), target)) {
        if (externalId) await deleteShortLink(ctx, apiKey, externalId);
        throw new Error("Short.io devolvió un destino distinto al de la chapita");
      }
      const qrPayload = `HTTPS://${domain.toUpperCase()}/${path}`;
      if (qrPayload.length > 25 || !/^[0-9A-Z $%*+\-./:]+$/.test(qrPayload)) {
        if (externalId) await deleteShortLink(ctx, apiKey, externalId);
        throw new Error("El enlace corto no entra en QR 21×21");
      }
      return {
        short_url: `https://${domain}/${path}`,
        path,
        external_id: externalId,
        qr_payload: qrPayload,
      };
    }

    if (r.status === 401 || r.status === 403) {
      throw new HttpError("API key de Short.io inválida o sin permiso para crear enlaces", 403);
    }
    if (r.status === 404) {
      throw new HttpError("Short.io no reconoce ese dominio. Crealo y activalo primero en tu cuenta", 400);
    }
    if (r.status === 429) throw new HttpError("Short.io alcanzó temporalmente el límite de solicitudes de la cuenta", 429);

    const message = String(data?.error || data?.message || data?.errorMessage || text || "").slice(0, 300);
    lastError = message || lastError;
    if ([400, 409, 422].includes(r.status)) continue;
    logDependency(ctx, "shortio", "create_link", r.status);
    throw new Error(lastError);
  }
  throw new Error(lastError);
}

async function verifyRedirect(ctx: RequestContext, shortUrl: string, target: string) {
  for (let attempt = 0; attempt < 4; attempt++) {
    if (attempt) await new Promise((resolve) => setTimeout(resolve, attempt * 450));
    try {
      const r = await fetchWithTimeout(shortUrl, {
        method: "GET",
        redirect: "manual",
        headers: { "User-Agent": "Patas-a-Casa-Link-Check/2.0" },
      }, 8_000);
      const location = r.headers.get("location") || "";
      if (r.status >= 300 && r.status < 400 && location) {
        const resolved = new URL(location, shortUrl).toString();
        if (sameTarget(resolved, target)) return true;
      }
    } catch (error) {
      if (attempt === 3) {
        logDependency(ctx, "shortio", "verify_redirect", error instanceof Error ? error.name : "UnknownError");
      }
    }
  }
  return false;
}

async function cleanupTags(ctx: RequestContext, codes: string[]) {
  for (const publicCode of codes) {
    try {
      const r = await fetchWithTimeout(
        `${SUPABASE_URL}/rest/v1/tags?public_code=eq.${encodeURIComponent(publicCode)}&pet_id=is.null&activated_at=is.null`,
        {
          method: "DELETE",
          headers: { apikey: SERVICE_KEY, Authorization: `Bearer ${SERVICE_KEY}` },
        },
      );
      if (!r.ok) logDependency(ctx, "postgres", "rollback_tag", r.status);
    } catch (error) {
      logDependency(ctx, "postgres", "rollback_tag", error instanceof Error ? error.name : "UnknownError");
    }
  }
}

async function cleanupBackups(ctx: RequestContext, shortUrls: string[]) {
  for (const shortUrl of shortUrls) {
    try {
      const r = await fetchWithTimeout(
        `${SUPABASE_URL}/rest/v1/short_links?short_url=eq.${encodeURIComponent(shortUrl)}`,
        {
          method: "DELETE",
          headers: { apikey: SERVICE_KEY, Authorization: `Bearer ${SERVICE_KEY}` },
        },
      );
      if (!r.ok) logDependency(ctx, "postgres", "rollback_short_backup", r.status);
    } catch (error) {
      logDependency(ctx, "postgres", "rollback_short_backup", error instanceof Error ? error.name : "UnknownError");
    }
  }
}

async function saveBackup(ctx: RequestContext, item: any) {
  const backupCode = `${item.domain}/${item.short_path}`;
  const r = await fetchWithTimeout(`${SUPABASE_URL}/rest/v1/short_links`, {
    method: "POST",
    headers: {
      apikey: SERVICE_KEY,
      Authorization: `Bearer ${SERVICE_KEY}`,
      "Content-Type": "application/json",
      Prefer: "return=minimal",
    },
    body: JSON.stringify({
      code: backupCode,
      target_url: item.url,
      provider: "shortio",
      domain: item.domain,
      short_url: item.short_url,
      external_id: item.external_id || null,
      public_code: item.public_code,
    }),
  });
  if (!r.ok) {
    logDependency(ctx, "postgres", "save_short_backup", r.status);
    throw new Error(`No se pudo respaldar el enlace físico (${r.status})`);
  }
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
      return new Response(null, { status: 204, headers: { ...cors(req), "X-Request-Id": ctx.id } });
    }
    if (req.method !== "POST") return json(req, ctx, { error: "Método no permitido" }, 405);

    const origin = req.headers.get("origin") || "";
    if (origin && !ALLOWED_ORIGINS.has(origin)) return json(req, ctx, { error: "Origen no permitido" }, 403);

    const body = await readJson(req);
    ctx.action = String(body?.action || "").slice(0, 40);
    if (ctx.action !== "generate_batch") return json(req, ctx, { error: "Acción inválida" }, 400);

    const adminKey = String(body.admin_key ?? "").trim().slice(0, 100);
    const shortApiKey = String(body.shortio_api_key ?? "").trim().slice(0, 500);
    const count = Number(body.count);
    const { domain, slugLength } = normalizeDomain(body.shortio_domain);

    if (!adminKey) return json(req, ctx, { error: "Ingresá la clave de administrador" }, 400);
    if (!shortApiKey) return json(req, ctx, { error: "Ingresá la API key de Short.io" }, 400);
    if (!Number.isInteger(count) || count < 1 || count > MAX_BATCH_SIZE) {
      return json(req, ctx, { error: `La cantidad debe ser entre 1 y ${MAX_BATCH_SIZE}` }, 400);
    }

    const rpc = await fetchWithTimeout(`${SUPABASE_URL}/rest/v1/rpc/generate_tag_batch`, {
      method: "POST",
      headers: { apikey: SERVICE_KEY, Authorization: `Bearer ${SERVICE_KEY}`, "Content-Type": "application/json" },
      body: JSON.stringify({ p_admin_key: adminKey, p_count: count }),
    });
    if (!rpc.ok) {
      const detail = await rpc.text();
      if (detail.includes("Clave de administrador incorrecta")) {
        return json(req, ctx, { error: "Clave de administrador incorrecta" }, 403);
      }
      logDependency(ctx, "postgres", "generate_tag_batch", rpc.status);
      return json(req, ctx, { error: "No se pudo generar el lote" }, 500);
    }

    const rows = await rpc.json();
    const created = Array.isArray(rows) ? rows : [];
    if (created.length !== count) {
      await cleanupTags(ctx, created.map((row: any) => String(row.public_code)));
      return json(req, ctx, { error: "La base devolvió un lote incompleto. Se revirtió para que puedas reintentar." }, 500);
    }

    if (created.some((row: any) => row.activation_pin !== "PAC2011")) {
      await cleanupTags(ctx, created.map((row: any) => String(row.public_code)));
      return json(req, ctx, { error: "El lote no usa PAC2011. Se canceló para evitar chapitas con otro código." }, 500);
    }

    const codes = created.map((row: any) => String(row.public_code));
    const madeLinks: { id: string; short_url: string }[] = [];
    const backedUp: string[] = [];
    const items: any[] = [];

    try {
      for (let i = 0; i < created.length; i++) {
        const row: any = created[i];
        const publicCode = String(row.public_code);
        const originalUrl = BASE_TAG_URL + encodeURIComponent(publicCode);
        const short = await createShortLink(ctx, shortApiKey, domain, slugLength, originalUrl);
        madeLinks.push({ id: short.external_id, short_url: short.short_url });

        const works = await verifyRedirect(ctx, short.short_url, originalUrl);
        if (!works) {
          throw new Error("El dominio Short.io todavía no redirige correctamente. Verificá que el subdominio esté activado por teléfono");
        }

        const item = {
          number: i + 1,
          public_code: publicCode,
          pin: String(row.activation_pin),
          url: originalUrl,
          short_url: short.short_url,
          short_path: short.path,
          external_id: short.external_id,
          domain,
          qr_payload: short.qr_payload,
        };
        await saveBackup(ctx, item);
        backedUp.push(short.short_url);
        items.push(item);
      }
    } catch (error) {
      await cleanupBackups(ctx, backedUp);
      for (const link of madeLinks) await deleteShortLink(ctx, shortApiKey, link.id);
      await cleanupTags(ctx, codes);
      console.error(JSON.stringify({
        event: "batch_rollback",
        function: FUNCTION_NAME,
        request_id: ctx.id,
        created_tags: codes.length,
        created_links: madeLinks.length,
        error_type: error instanceof Error ? error.name : "UnknownError",
      }));
      const message = error instanceof HttpError ? error.message : error instanceof Error ? error.message : "falló Short.io";
      return json(req, ctx, {
        error: `No se pudo completar el lote: ${message}. Se revirtieron las chapitas nuevas para que puedas reintentar.`,
      }, error instanceof HttpError ? error.status : 502);
    }

    return json(req, ctx, {
      ok: true,
      provider: "shortio",
      domain,
      slug_length: slugLength,
      created_at: new Date().toISOString(),
      items,
    });
  } catch (error) {
    if (error instanceof HttpError) return json(req, ctx, { error: error.message }, error.status);
    console.error(JSON.stringify({
      event: "request_error",
      function: FUNCTION_NAME,
      request_id: ctx.id,
      action: ctx.action || "unknown",
      error_type: error instanceof Error ? error.name : "UnknownError",
    }));
    return json(req, ctx, { error: "Error interno" }, 500);
  } finally {
    logRequest(ctx);
  }
});
