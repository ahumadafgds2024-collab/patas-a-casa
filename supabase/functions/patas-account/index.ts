import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const PHOTO_BUCKET = "pet-photos";
const MAX_PHOTO_BYTES = 2 * 1024 * 1024;

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
function txt(v: unknown, max = 500) {
  const s = String(v ?? "").trim().slice(0, max);
  return s || null;
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
  const r = await fetch(`${SUPABASE_URL}/rest/v1/pets?id=eq.${encodeURIComponent(id)}&select=*&limit=1`, { headers: serviceHeaders });
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

async function ownedPet(userId: string, c: string) {
  const r = await fetch(`${SUPABASE_URL}/rest/v1/pets?owner_id=eq.${encodeURIComponent(userId)}&public_code=eq.${encodeURIComponent(c)}&select=*&limit=1`, { headers: serviceHeaders });
  if (!r.ok) throw new Error(`owned_pet_${r.status}`);
  const rows = await r.json();
  return rows?.[0] ?? null;
}

async function pendingForUser(userId: string, c: string) {
  const r = await fetch(
    `${SUPABASE_URL}/rest/v1/pending_owner_claims?auth_user_id=eq.${encodeURIComponent(userId)}&public_code=eq.${encodeURIComponent(c)}&consumed_at=is.null&select=id,auth_user_id,tag_id,pet_id,public_code,email,expires_at,created_at&order=created_at.desc&limit=1`,
    { headers: serviceHeaders },
  );
  if (!r.ok) throw new Error(`pending_lookup_${r.status}`);
  const rows = await r.json();
  return rows?.[0] ?? null;
}

async function completePending(id: string, userId: string, petId: string) {
  const r = await fetch(
    `${SUPABASE_URL}/rest/v1/pending_owner_claims?id=eq.${encodeURIComponent(id)}&auth_user_id=eq.${encodeURIComponent(userId)}&consumed_at=is.null`,
    {
      method: "PATCH",
      headers: { ...serviceHeaders, Prefer: "return=minimal" },
      body: JSON.stringify({ pet_id: petId, consumed_at: new Date().toISOString() }),
    },
  );
  if (!r.ok) console.error("complete_pending", r.status, await r.text());
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
  if (!upload.ok) throw new Error("No se pudo subir la foto");
  return `${SUPABASE_URL}/storage/v1/object/public/${PHOTO_BUCKET}/${objectPath}`;
}

function profilePayload(b: any) {
  const out: Record<string, unknown> = {
    name: txt(b.name, 80) || "Mascota",
    species: txt(b.species, 40) || "Perro",
    breed: txt(b.breed, 80),
    sex: txt(b.sex, 30),
    age_text: txt(b.age_text, 40),
    size: txt(b.size, 30),
    color: txt(b.color, 50),
    diseases: txt(b.diseases),
    medications: txt(b.medications),
    medication_schedule: txt(b.medication_schedule, 300),
    allergies: txt(b.allergies),
    special_care: txt(b.special_care, 700),
    vet_info: txt(b.vet_info, 500),
    contact_name: txt(b.contact_name, 80),
    contact_phone: txt(b.contact_phone, 40),
    contact_whatsapp: txt(b.contact_whatsapp, 40),
    alt_contact: txt(b.alt_contact, 120),
    public_health: Boolean(b.public_health),
    public_contact: Boolean(b.public_contact),
    updated_at: new Date().toISOString(),
  };
  return out;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "Ruta no encontrada" }, 404);

  try {
    const b = await req.json();

    // Deprecated on purpose: all new accounts must use patas-register-v2,
    // which requires email verification before linking the first pet.
    if (b.action === "register_owner") {
      return json({ error: "El registro cambió. Actualizá la página y verificá tu correo para crear la cuenta." }, 410);
    }

    const user = await currentUser(req);
    if (!user?.id) return json({ error: "Sesión vencida. Volvé a ingresar." }, 401);

    if (b.action === "complete_activation") {
      if (!user.email_confirmed_at && !user.confirmed_at) {
        return json({ error: "Primero confirmá tu correo electrónico." }, 403);
      }

      const c = code(b.public_code);
      if (!c) return json({ error: "No encontramos la chapita pendiente." }, 400);
      const pending = await pendingForUser(user.id, c);
      if (!pending) return json({ error: "No encontramos una activación pendiente para esta cuenta." }, 404);
      if (String(pending.email || "").toLowerCase() !== String(user.email || "").toLowerCase()) {
        return json({ error: "La verificación no coincide con esta cuenta." }, 403);
      }
      if (new Date(pending.expires_at).getTime() < Date.now()) {
        return json({ error: "La activación pendiente venció. Contactanos para continuar sin perder la chapita." }, 410);
      }

      const tag = await tagByCode(c);
      if (!tag || tag.blocked_at || tag.id !== pending.tag_id) {
        return json({ error: "La chapita pendiente no está disponible." }, 409);
      }

      if (pending.pet_id) {
        const existingPendingPet = await petById(pending.pet_id);
        if (existingPendingPet?.owner_id === user.id) {
          await completePending(pending.id, user.id, existingPendingPet.id);
          return json({ ok: true, already: true, public_code: c, pet: existingPendingPet });
        }
        return json({ error: "Esta activación ya fue utilizada." }, 409);
      }

      if (tag.pet_id || tag.activated_at) {
        if (tag.pet_id && tag.activated_at) {
          const existingTagPet = await petById(tag.pet_id);
          if (existingTagPet?.owner_id === user.id) {
            await completePending(pending.id, user.id, existingTagPet.id);
            return json({ ok: true, already: true, public_code: c, pet: existingTagPet });
          }
        }
        return json({ error: "Esta chapita ya fue activada por otra cuenta." }, 409);
      }

      const petName = txt(b.name, 80);
      const contactName = txt(b.contact_name, 80);
      const contactPhone = txt(b.contact_whatsapp || b.contact_phone, 40);
      if (!petName || !contactName || !contactPhone) {
        return json({ error: "Completá el nombre de la mascota, tu nombre y un teléfono de contacto." }, 400);
      }

      const petId = crypto.randomUUID();
      let photoUrl: string | null = null;
      if (b.photo_data) {
        try {
          photoUrl = await savePhoto(petId, b.photo_data);
        } catch (e) {
          return json({ error: e instanceof Error ? e.message : "No se pudo subir la foto" }, 400);
        }
      }

      const insert = await fetch(`${SUPABASE_URL}/rest/v1/pets`, {
        method: "POST",
        headers: { ...serviceHeaders, Prefer: "return=representation" },
        body: JSON.stringify({
          id: petId,
          owner_id: user.id,
          public_code: c,
          ...profilePayload({ ...b, name: petName, contact_name: contactName, contact_phone: contactPhone }),
          photo_url: photoUrl,
          status: "normal",
          is_active: true,
        }),
      });
      const createdRows = insert.ok ? await insert.json() : [];
      if (!insert.ok || !createdRows?.[0]?.id) {
        if (!insert.ok) console.error("create_pet", insert.status, await insert.text());
        return json({ error: "No pudimos crear el perfil de la mascota." }, 409);
      }

      const tagUpdate = await fetch(
        `${SUPABASE_URL}/rest/v1/tags?id=eq.${encodeURIComponent(tag.id)}&pet_id=is.null&activated_at=is.null`,
        {
          method: "PATCH",
          headers: { ...serviceHeaders, Prefer: "return=representation" },
          body: JSON.stringify({ pet_id: petId, activated_at: new Date().toISOString() }),
        },
      );
      const updatedTags = tagUpdate.ok ? await tagUpdate.json() : [];
      if (!tagUpdate.ok || !updatedTags?.length) {
        await fetch(`${SUPABASE_URL}/rest/v1/pets?id=eq.${encodeURIComponent(petId)}&owner_id=eq.${encodeURIComponent(user.id)}`, {
          method: "DELETE",
          headers: serviceHeaders,
        }).catch(() => {});
        return json({ error: "La chapita cambió de estado mientras creábamos el perfil. Volvé a intentarlo." }, 409);
      }

      await completePending(pending.id, user.id, petId);
      return json({ ok: true, public_code: c, pet: createdRows[0] });
    }

    if (b.action === "list_my_pets") {
      const r = await fetch(`${SUPABASE_URL}/rest/v1/pets?owner_id=eq.${encodeURIComponent(user.id)}&is_active=eq.true&select=*&order=created_at.asc`, { headers: serviceHeaders });
      if (!r.ok) return json({ error: "No pudimos cargar tus mascotas." }, 500);
      const pets = await r.json();
      return json({ ok: true, user: { id: user.id, email: user.email }, pets });
    }

    if (b.action === "claim_pet") {
      const c = code(b.public_code);
      const pin = String(b.activation_code ?? "").trim().slice(0, 50);
      if (!c || !pin) return json({ error: "Ingresá el código y el PIN de la chapita." }, 400);
      const tag = await tagByCode(c);
      if (!tag || tag.blocked_at || !tag.pet_id || !tag.activated_at) return json({ error: "La chapita no existe o todavía no está activada." }, 404);
      if (!(await verifyPin(c, pin))) return json({ error: "PIN incorrecto." }, 403);
      const pet = await petById(tag.pet_id);
      if (!pet) return json({ error: "Mascota no encontrada." }, 404);
      if (pet.owner_id && pet.owner_id !== user.id) return json({ error: "Esta mascota ya pertenece a otra cuenta." }, 409);
      if (pet.owner_id === user.id) return json({ ok: true, already: true });
      const r = await fetch(`${SUPABASE_URL}/rest/v1/pets?id=eq.${encodeURIComponent(pet.id)}&owner_id=is.null`, {
        method: "PATCH",
        headers: { ...serviceHeaders, Prefer: "return=representation" },
        body: JSON.stringify({ owner_id: user.id, updated_at: new Date().toISOString() }),
      });
      const rows = r.ok ? await r.json() : [];
      if (!r.ok || !rows?.length) return json({ error: "No pudimos agregar esta mascota a tu cuenta." }, 409);
      return json({ ok: true, public_code: c });
    }

    if (b.action === "set_status") {
      const c = code(b.public_code);
      const status = b.status === "perdido" ? "perdido" : b.status === "normal" ? "normal" : "";
      if (!c || !status) return json({ error: "Estado inválido." }, 400);
      const r = await fetch(`${SUPABASE_URL}/rest/v1/pets?owner_id=eq.${encodeURIComponent(user.id)}&public_code=eq.${encodeURIComponent(c)}`, {
        method: "PATCH",
        headers: { ...serviceHeaders, Prefer: "return=representation" },
        body: JSON.stringify({ status, updated_at: new Date().toISOString() }),
      });
      const rows = r.ok ? await r.json() : [];
      if (!r.ok || !rows?.length) return json({ error: "No pudimos cambiar el estado." }, 404);
      return json({ ok: true, status });
    }

    if (b.action === "list_sightings") {
      const c = code(b.public_code);
      const pet = await ownedPet(user.id, c);
      if (!pet) return json({ error: "Mascota no encontrada en tu cuenta." }, 404);
      const r = await fetch(`${SUPABASE_URL}/rest/v1/sightings?pet_public_code=eq.${encodeURIComponent(c)}&select=id,message,finder_phone,area_text,latitude,longitude,location_consent,contact_consent,created_at&order=created_at.desc&limit=50`, { headers: serviceHeaders });
      if (!r.ok) return json({ error: "No pudimos cargar los avistamientos." }, 500);
      return json({ ok: true, sightings: await r.json() });
    }

    if (b.action === "update_pet") {
      const c = code(b.public_code);
      const pet = await ownedPet(user.id, c);
      if (!pet) return json({ error: "Mascota no encontrada en tu cuenta." }, 404);
      const payload = profilePayload(b);
      if (b.remove_photo === true) payload.photo_url = null;
      else if (b.photo_data) payload.photo_url = await savePhoto(pet.id, b.photo_data);
      const r = await fetch(`${SUPABASE_URL}/rest/v1/pets?id=eq.${encodeURIComponent(pet.id)}&owner_id=eq.${encodeURIComponent(user.id)}`, {
        method: "PATCH",
        headers: { ...serviceHeaders, Prefer: "return=representation" },
        body: JSON.stringify(payload),
      });
      const rows = r.ok ? await r.json() : [];
      if (!r.ok || !rows?.length) return json({ error: "No pudimos guardar los cambios." }, 500);
      return json({ ok: true, pet: rows[0] });
    }

    return json({ error: "Acción no encontrada." }, 404);
  } catch (e) {
    console.error(e);
    return json({ error: e instanceof Error ? e.message : "Error interno" }, 500);
  }
});
