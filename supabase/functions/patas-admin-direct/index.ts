import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const LEGACY_APP_ORIGIN = "https://patas-a-casa.vercel.app";
const PUBLIC_ORIGIN = "https://www.patasacasa.com.ar";
const DIRECT_DOMAIN = "www.patasacasa.com.ar";
const DIRECT_PREFIX = `HTTPS://${DIRECT_DOMAIN.toUpperCase()}/S/`;
const ALLOWED_ORIGINS = new Set([
  LEGACY_APP_ORIGIN,
  "https://patasacasa.com.ar",
  PUBLIC_ORIGIN,
]);
const FUNCTION_NAME = "patas-admin-direct";
const MAX_BODY_BYTES = 16 * 1024;
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
    ? { ...data, error: `${String(data.error || "Error")} Referencia: ${ctx.id}`, request_id: ctx.id }
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

function directItem(row: any, number: number) {
  const publicCode = String(row.public_code || "").toUpperCase();
  if (!/^[A-F0-9]{8}$/.test(publicCode)) throw new Error("La base devolvió un código público inválido");
  const shortUrl = `https://${DIRECT_DOMAIN}/S/${publicCode}`;
  const targetUrl = `${PUBLIC_ORIGIN}/tag.html?tag=${publicCode}`;
  const qrPayload = `${DIRECT_PREFIX}${publicCode}`;
  if (qrPayload.length > 41 || !/^[0-9A-Z $%*+\-./:]+$/.test(qrPayload)) {
    throw new Error("La dirección directa no entra en QR 21×21");
  }
  return {
    number,
    public_code: publicCode,
    pin: String(row.activation_pin),
    url: targetUrl,
    short_url: shortUrl,
    short_path: `S/${publicCode}`,
    external_id: null,
    domain: DIRECT_DOMAIN,
    provider: "direct",
    qr_payload: qrPayload,
  };
}

async function verifyDirectUrl(ctx: RequestContext, item: any) {
  try {
    const response = await fetchWithTimeout(item.short_url, {
      method: "GET",
      redirect: "follow",
      headers: { "User-Agent": "Patas-a-Casa-Link-Check/3.0" },
    });
    if (!response.ok) return false;
    const finalUrl = new URL(response.url);
    return finalUrl.hostname.toLowerCase() === DIRECT_DOMAIN &&
      finalUrl.pathname === "/tag.html" &&
      finalUrl.searchParams.get("tag") === item.public_code;
  } catch (error) {
    logDependency(ctx, "patas_web", "verify_direct_url", error instanceof Error ? error.name : "UnknownError");
    return false;
  }
}

async function saveBackups(ctx: RequestContext, items: any[]) {
  const rows = items.map((item) => ({
    code: `${item.domain}/${item.short_path}`,
    target_url: item.url,
    provider: item.provider,
    domain: item.domain,
    short_url: item.short_url,
    external_id: null,
    public_code: item.public_code,
  }));
  const response = await fetchWithTimeout(`${SUPABASE_URL}/rest/v1/short_links`, {
    method: "POST",
    headers: {
      apikey: SERVICE_KEY,
      Authorization: `Bearer ${SERVICE_KEY}`,
      "Content-Type": "application/json",
      Prefer: "return=minimal",
    },
    body: JSON.stringify(rows),
  });
  if (!response.ok) {
    logDependency(ctx, "postgres", "save_direct_backups", response.status);
    throw new Error(`No se pudo respaldar el lote (${response.status})`);
  }
}

async function cleanupTags(ctx: RequestContext, codes: string[]) {
  for (const publicCode of codes) {
    try {
      const response = await fetchWithTimeout(
        `${SUPABASE_URL}/rest/v1/tags?public_code=eq.${encodeURIComponent(publicCode)}&pet_id=is.null&activated_at=is.null`,
        {
          method: "DELETE",
          headers: { apikey: SERVICE_KEY, Authorization: `Bearer ${SERVICE_KEY}` },
        },
      );
      if (!response.ok) logDependency(ctx, "postgres", "rollback_tag", response.status);
    } catch (error) {
      logDependency(ctx, "postgres", "rollback_tag", error instanceof Error ? error.name : "UnknownError");
    }
  }
}

async function cleanupBackups(ctx: RequestContext, codes: string[]) {
  for (const publicCode of codes) {
    try {
      const response = await fetchWithTimeout(
        `${SUPABASE_URL}/rest/v1/short_links?provider=eq.direct&public_code=eq.${encodeURIComponent(publicCode)}`,
        {
          method: "DELETE",
          headers: { apikey: SERVICE_KEY, Authorization: `Bearer ${SERVICE_KEY}` },
        },
      );
      if (!response.ok) logDependency(ctx, "postgres", "rollback_direct_backup", response.status);
    } catch (error) {
      logDependency(ctx, "postgres", "rollback_direct_backup", error instanceof Error ? error.name : "UnknownError");
    }
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
    if (ctx.action !== "generate_direct_batch") return json(req, ctx, { error: "Acción inválida" }, 400);

    const adminKey = String(body.admin_key ?? "").trim().slice(0, 100);
    const count = Number(body.count);
    if (!adminKey) return json(req, ctx, { error: "Ingresá la clave de administrador" }, 400);
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
    const codes = created.map((row: any) => String(row.public_code));
    if (created.length !== count) {
      await cleanupTags(ctx, codes);
      return json(req, ctx, { error: "La base devolvió un lote incompleto. Se revirtió para que puedas reintentar." }, 500);
    }

    try {
      const items = created.map((row: any, index: number) => directItem(row, index + 1));
      for (const item of items) {
        if (!(await verifyDirectUrl(ctx, item))) {
          throw new Error("La dirección directa de Patas a Casa no respondió correctamente");
        }
      }
      await saveBackups(ctx, items);
      return json(req, ctx, {
        ok: true,
        provider: "direct",
        domain: DIRECT_DOMAIN,
        created_at: new Date().toISOString(),
        items,
      });
    } catch (error) {
      await cleanupBackups(ctx, codes);
      await cleanupTags(ctx, codes);
      console.error(JSON.stringify({
        event: "batch_rollback",
        function: FUNCTION_NAME,
        request_id: ctx.id,
        created_tags: codes.length,
        error_type: error instanceof Error ? error.name : "UnknownError",
      }));
      const message = error instanceof Error ? error.message : "falló la verificación";
      return json(req, ctx, {
        error: `No se pudo completar el lote: ${message}. Se revirtieron las chapitas nuevas para que puedas reintentar.`,
      }, 502);
    }
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
