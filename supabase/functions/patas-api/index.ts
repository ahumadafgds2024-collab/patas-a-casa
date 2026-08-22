import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const PHOTO_BUCKET = "pet-photos";
const MAX_PHOTO_BYTES = 2 * 1024 * 1024;

const dbHeaders = {
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

function activationPin(v: unknown) {
  const raw = String(v ?? "").trim().slice(0, 50);
  return /^\d{8}$/.test(raw) ? `${raw.slice(0, 4)}-${raw.slice(4)}` : raw;
}

function txt(v: unknown, max = 500) {
  const s = String(v ?? "").trim().slice(0, max);
  return s || null;
}

const petCols = [
  "id", "public_code", "name", "species", "breed", "sex", "birth_date", "age_text",
  "size", "color", "photo_url", "status", "diseases", "medications", "medication_schedule",
  "allergies", "special_care", "vet_info", "public_health", "contact_name", "contact_phone",
  "contact_whatsapp", "alt_contact", "public_contact", "is_active", "updated_at",
].join(",");

async function tagByCode(c: string) {
  const r = await fetch(
    `${SUPABASE_URL}/rest/v1/tags?public_code=eq.${encodeURIComponent(c)}&select=id,public_code,pet_id,activated_at,blocked_at&limit=1`,
    { headers: dbHeaders },
  );
  if (!r.ok) throw new Error(`tag_lookup_${r.status}`);
  const rows = await r.json();
  return rows?.[0] ?? null;
}

async function petById(id: string) {
  const r = await fetch(
    `${SUPABASE_URL}/rest/v1/pets?id=eq.${encodeURIComponent(id)}&is_active=eq.true&select=${petCols}&limit=1`,
    { headers: dbHeaders },
  );
  if (!r.ok) throw new Error(`pet_lookup_${r.status}`);
  const rows = await r.json();
  return rows?.[0] ?? null;
}

async function petForTag(c: string) {
  const t = await tagByCode(c);
  if (!t || t.blocked_at) return { tag: t, pet: null };
  if (!t.pet_id || !t.activated_at) return { tag: t, pet: null };
  return { tag: t, pet: await petById(t.pet_id) };
}

function publicPet(pet: any) {
  const p = { ...pet };
  if (!p.public_contact) {
    p.contact_name = null;
    p.contact_phone = null;
    p.contact_whatsapp = null;
    p.alt_contact = null;
  }
  if (!p.public_health) {
    p.diseases = null;
    p.medications = null;
    p.medication_schedule = null;
    p.allergies = null;
    p.special_care = null;
    p.vet_info = null;
  }
  return p;
}

async function verify(c: string, s: string) {
  const r = await fetch(`${SUPABASE_URL}/rest/v1/rpc/verify_tag_activation`, {
    method: "POST",
    headers: dbHeaders,
    body: JSON.stringify({ p_public_code: c, p_activation_code: activationPin(s) }),
  });
  if (!r.ok) return false;
  return Boolean(await r.json());
}

function payloadFrom(b: any) {
  const phone = txt(b.contact_phone, 40);
  const whatsapp = txt(b.contact_whatsapp, 40);
  return {
    name: txt(b.name, 80) || "Mascota",
    species: txt(b.species, 40) || "Perro",
    breed: txt(b.breed, 80),
    sex: txt(b.sex, 30),
    age_text: txt(b.age_text, 40),
    size: txt(b.size, 30),
    color: txt(b.color, 50),
    status: b.status === "perdido" ? "perdido" : "normal",
    diseases: txt(b.diseases),
    medications: txt(b.medications),
    medication_schedule: txt(b.medication_schedule, 300),
    allergies: txt(b.allergies),
    special_care: txt(b.special_care, 700),
    vet_info: txt(b.vet_info, 500),
    contact_name: txt(b.contact_name, 80),
    contact_phone: phone,
    contact_whatsapp: whatsapp,
    alt_contact: txt(b.alt_contact, 120),
    public_health: Boolean(b.public_health),
    public_contact: Boolean(b.public_contact && (phone || whatsapp)),
    updated_at: new Date().toISOString(),
  };
}

function parsePhotoData(data: unknown) {
  if (!data) return null;
  const raw = String(data);
  const m = raw.match(/^data:(image\/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=]+)$/);
  if (!m) throw new Error("Formato de foto inválido");
  return { mime: m[1], base64: m[2] };
}

function decodeBase64(base64: string) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

async function savePhoto(petId: string, photoData: unknown) {
  const parsed = parsePhotoData(photoData);
  if (!parsed) return null;
  const bytes = decodeBase64(parsed.base64);
  if (bytes.byteLength > MAX_PHOTO_BYTES) throw new Error("La foto es demasiado grande");

  const ext = parsed.mime === "image/png" ? "png" : parsed.mime === "image/webp" ? "webp" : "jpg";
  const objectPath = `${petId}/${Date.now()}-${crypto.randomUUID()}.${ext}`;
  const upload = await fetch(`${SUPABASE_URL}/storage/v1/object/${PHOTO_BUCKET}/${objectPath}`, {
    method: "POST",
    headers: {
      apikey: SERVICE_KEY,
      Authorization: `Bearer ${SERVICE_KEY}`,
      "Content-Type": parsed.mime,
      "x-upsert": "false",
      "cache-control": "3600",
    },
    body: bytes,
  });
  if (!upload.ok) {
    console.error("photo_upload", upload.status, await upload.text());
    throw new Error("No se pudo subir la foto");
  }
  return `${SUPABASE_URL}/storage/v1/object/public/${PHOTO_BUCKET}/${objectPath}`;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });

  try {
    const u = new URL(req.url);
    const action = u.searchParams.get("action") || "";

    if (req.method === "GET" && action === "tag") {
      const c = code(u.searchParams.get("code"));
      if (!c) return json({ error: "Código inválido" }, 400);
      const { tag, pet } = await petForTag(c);
      if (!tag || tag.blocked_at) return json({ error: "Chapita no encontrada o bloqueada" }, 404);
      if (!tag.activated_at || !tag.pet_id || !pet) return json({ state: "unactivated", public_code: c });
      return json({ state: "active", public_code: c, pet: publicPet(pet) });
    }

    if (req.method === "POST") {
      const b = await req.json();

      if (b.action === "verify_pin") {
        const c = code(b.public_code);
        const secret = String(b.activation_code ?? "").trim().slice(0, 50);
        if (!c || !secret) return json({ error: "Ingresá el PIN" }, 400);
        const t = await tagByCode(c);
        if (!t || t.blocked_at) return json({ error: "Chapita no encontrada o bloqueada" }, 404);
        if (t.activated_at || t.pet_id) return json({ error: "Esta chapita ya fue activada" }, 409);
        if (!(await verify(c, secret))) return json({ error: "PIN incorrecto" }, 403);
        return json({ ok: true });
      }

      if (b.action === "activate") {
        const c = code(b.public_code);
        const secret = String(b.activation_code ?? "").trim().slice(0, 50);
        if (!c || !secret) return json({ error: "Falta el código de la chapita o el PIN" }, 400);
        const t = await tagByCode(c);
        if (!t || t.blocked_at) return json({ error: "Chapita no encontrada o bloqueada" }, 404);
        if (t.activated_at || t.pet_id) return json({ error: "Esta chapita ya fue activada" }, 409);
        if (!(await verify(c, secret))) return json({ error: "PIN incorrecto" }, 403);

        const petId = crypto.randomUUID();
        let photoUrl = null;
        if (b.photo_data) {
          try {
            photoUrl = await savePhoto(petId, b.photo_data);
          } catch (e) {
            return json({ error: e instanceof Error ? e.message : "No se pudo subir la foto" }, 400);
          }
        }

        const p = {
          id: petId,
          public_code: c,
          ...payloadFrom(b),
          photo_url: photoUrl,
          is_active: true,
        };
        const ins = await fetch(`${SUPABASE_URL}/rest/v1/pets`, {
          method: "POST",
          headers: { ...dbHeaders, Prefer: "return=representation" },
          body: JSON.stringify(p),
        });
        if (!ins.ok) {
          console.error(await ins.text());
          return json({ error: "No se pudo crear el perfil" }, 500);
        }
        const rows = await ins.json();
        const pet = rows?.[0];
        if (!pet?.id) return json({ error: "No se pudo crear el perfil" }, 500);

        const upd = await fetch(`${SUPABASE_URL}/rest/v1/tags?id=eq.${encodeURIComponent(t.id)}`, {
          method: "PATCH",
          headers: { ...dbHeaders, Prefer: "return=minimal" },
          body: JSON.stringify({ pet_id: pet.id, activated_at: new Date().toISOString() }),
        });
        if (!upd.ok) return json({ error: "El perfil se creó pero no pudo vincularse a la chapita" }, 500);
        return json({ ok: true, public_code: c, photo_url: photoUrl });
      }

      if (b.action === "update_pet") {
        const c = code(b.public_code);
        const secret = String(b.activation_code ?? "").trim().slice(0, 50);
        if (!c || !secret) return json({ error: "Falta el código de la chapita o el PIN" }, 400);
        if (!(await verify(c, secret))) return json({ error: "PIN incorrecto" }, 403);
        const { tag, pet } = await petForTag(c);
        if (!tag || tag.blocked_at || !pet) return json({ error: "La chapita todavía no fue activada" }, 404);

        const payload: Record<string, unknown> = payloadFrom(b);
        if (b.remove_photo === true) {
          payload.photo_url = null;
        } else if (b.photo_data) {
          try {
            payload.photo_url = await savePhoto(pet.id, b.photo_data);
          } catch (e) {
            return json({ error: e instanceof Error ? e.message : "No se pudo subir la foto" }, 400);
          }
        }

        const r = await fetch(`${SUPABASE_URL}/rest/v1/pets?id=eq.${encodeURIComponent(pet.id)}`, {
          method: "PATCH",
          headers: { ...dbHeaders, Prefer: "return=minimal" },
          body: JSON.stringify(payload),
        });
        if (!r.ok) {
          console.error("update_pet", r.status, await r.text());
          return json({ error: "No se pudo actualizar el perfil" }, 500);
        }
        return json({ ok: true, public_code: c });
      }

      if (b.action === "sighting") {
        const c = code(b.public_code);
        const { tag, pet } = await petForTag(c);
        if (!tag || tag.blocked_at || !pet) return json({ error: "Chapita no encontrada o sin activar" }, 404);
        const locationConsent = Boolean(
          b.location_consent && Number.isFinite(Number(b.latitude)) && Number.isFinite(Number(b.longitude)),
        );
        const contactConsent = Boolean(b.contact_consent);
        const lat = locationConsent ? Number(b.latitude) : null;
        const lon = locationConsent ? Number(b.longitude) : null;
        if ((lat !== null && (lat < -90 || lat > 90)) || (lon !== null && (lon < -180 || lon > 180))) {
          return json({ error: "Ubicación inválida" }, 400);
        }
        const row = {
          pet_public_code: pet.public_code,
          message: txt(b.message),
          area_text: txt(b.area_text, 120),
          finder_phone: contactConsent ? txt(b.finder_phone, 40) : null,
          contact_consent: contactConsent,
          location_consent: locationConsent,
          latitude: lat,
          longitude: lon,
        };
        const r = await fetch(`${SUPABASE_URL}/rest/v1/sightings`, {
          method: "POST",
          headers: { ...dbHeaders, Prefer: "return=minimal" },
          body: JSON.stringify(row),
        });
        if (!r.ok) return json({ error: "No se pudo guardar el aviso" }, 500);
        return json({ ok: true });
      }
    }

    return json({ error: "Ruta no encontrada" }, 404);
  } catch (e) {
    console.error(e);
    return json({ error: "Error interno" }, 500);
  }
});
