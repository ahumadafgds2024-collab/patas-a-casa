import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const APP_ORIGIN = "https://patas-a-casa.vercel.app";
const FUNCTION_NAME = "patas-admin-tags";
const MAX_BODY_BYTES = 16 * 1024;
const FETCH_TIMEOUT_MS = 10_000;

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
  return {
    "Access-Control-Allow-Origin": origin === APP_ORIGIN ? APP_ORIGIN : APP_ORIGIN,
    "Access-Control-Allow-Headers": "content-type, x-request-id",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
    "Access-Control-Expose-Headers": "X-Request-Id",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Vary": "Origin",
  };
}

function json(req: Request, requestId: string, data: Record<string, unknown>, status = 200) {
  const body = status >= 400
    ? { ...data, error: `${String(data.error || "Error")} Referencia: ${requestId}`, request_id: requestId }
    : data;
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors(req), "Content-Type": "application/json; charset=utf-8", "X-Request-Id": requestId },
  });
}

async function fetchWithTimeout(url: string, init: RequestInit = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
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

async function rpc(name: string, body: Record<string, unknown>) {
  return await fetchWithTimeout(`${SUPABASE_URL}/rest/v1/rpc/${name}`, {
    method: "POST",
    headers: {
      apikey: SERVICE_KEY,
      Authorization: `Bearer ${SERVICE_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

function cleanCode(value: unknown) {
  return String(value ?? "").trim().toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 12);
}

function rpcErrorStatus(text: string, fallback = 500) {
  if (text.includes("Clave de administrador incorrecta")) return 403;
  if (text.includes("Chapita no encontrada")) return 404;
  if (text.includes("Acción inválida")) return 400;
  return fallback;
}

Deno.serve(async (req) => {
  const id = requestId(req);
  const started = performance.now();
  let action = "unknown";
  let status = 500;

  try {
    if (req.method === "OPTIONS") {
      status = 204;
      action = "preflight";
      return new Response(null, { status, headers: { ...cors(req), "X-Request-Id": id } });
    }
    if (req.method !== "POST") {
      status = 405;
      return json(req, id, { error: "Método no permitido" }, status);
    }

    const origin = req.headers.get("origin") || "";
    if (origin && origin !== APP_ORIGIN) {
      status = 403;
      return json(req, id, { error: "Origen no permitido" }, status);
    }

    const body = await readJson(req);
    action = String(body?.action || "").trim().toLowerCase().slice(0, 20);
    const adminKey = String(body?.admin_key || "").trim().slice(0, 120);
    if (!adminKey) {
      status = 400;
      return json(req, id, { error: "Ingresá la clave de administrador" }, status);
    }

    if (action === "list") {
      const search = String(body?.search || "").trim().slice(0, 120);
      const filter = String(body?.status || "all").trim().toLowerCase().slice(0, 20);
      const limit = Math.max(1, Math.min(Number(body?.limit) || 100, 200));
      const offset = Math.max(0, Number(body?.offset) || 0);
      const r = await rpc("admin_tag_dashboard", {
        p_admin_key: adminKey,
        p_search: search,
        p_status: filter,
        p_limit: limit,
        p_offset: offset,
      });
      const text = await r.text();
      if (!r.ok) {
        status = rpcErrorStatus(text);
        console.error(JSON.stringify({ event: "rpc_error", function: FUNCTION_NAME, request_id: id, action, rpc: "admin_tag_dashboard", rpc_status: r.status }));
        return json(req, id, { error: status === 403 ? "Clave de administrador incorrecta" : "No se pudo cargar la gestión de chapitas" }, status);
      }
      let data: any = {};
      try { data = JSON.parse(text); } catch {}
      status = 200;
      return json(req, id, { ok: true, ...data }, status);
    }

    if (["reset", "block", "unblock"].includes(action)) {
      const publicCode = cleanCode(body?.public_code);
      if (!publicCode) {
        status = 400;
        return json(req, id, { error: "Ingresá un código de chapita válido" }, status);
      }
      const r = await rpc("admin_tag_action", {
        p_admin_key: adminKey,
        p_public_code: publicCode,
        p_action: action,
      });
      const text = await r.text();
      if (!r.ok) {
        status = rpcErrorStatus(text);
        console.error(JSON.stringify({ event: "rpc_error", function: FUNCTION_NAME, request_id: id, action, rpc: "admin_tag_action", rpc_status: r.status, public_code: publicCode }));
        const message = status === 403 ? "Clave de administrador incorrecta" : status === 404 ? "Chapita no encontrada" : "No se pudo realizar la acción";
        return json(req, id, { error: message }, status);
      }
      let data: any = {};
      try { data = JSON.parse(text); } catch {}
      status = 200;
      return json(req, id, data && typeof data === "object" ? data : { ok: true }, status);
    }

    status = 400;
    return json(req, id, { error: "Acción inválida" }, status);
  } catch (error) {
    status = error instanceof HttpError ? error.status : 500;
    console.error(JSON.stringify({ event: "request_error", function: FUNCTION_NAME, request_id: id, action, error_type: error instanceof Error ? error.name : "UnknownError" }));
    return json(req, id, { error: error instanceof HttpError ? error.message : "Error interno" }, status);
  } finally {
    console.log(JSON.stringify({ event: "request_complete", function: FUNCTION_NAME, request_id: id, method: req.method, action, status, duration_ms: Math.round(performance.now() - started) }));
  }
});
