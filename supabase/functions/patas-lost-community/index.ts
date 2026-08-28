import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "content-type, authorization, apikey, x-request-id",
  "Access-Control-Allow-Methods": "GET,OPTIONS",
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
};

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...cors, "Content-Type": "application/json; charset=utf-8" },
  });
}

function digits(value: unknown) {
  return String(value ?? "").replace(/\D/g, "");
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
  if (req.method !== "GET") return json({ error: "Ruta no encontrada" }, 404);

  try {
    const select = [
      "public_code",
      "name",
      "species",
      "breed",
      "age_text",
      "photo_url",
      "lost_location",
      "lost_at",
      "contact_whatsapp",
      "contact_phone",
      "public_contact",
    ].join(",");

    const url = `${SUPABASE_URL}/rest/v1/pets?is_active=eq.true&status=eq.perdido&select=${encodeURIComponent(select)}&order=lost_at.desc.nullslast,updated_at.desc&limit=100`;
    const response = await fetch(url, {
      headers: {
        apikey: SERVICE_KEY,
        Authorization: `Bearer ${SERVICE_KEY}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      console.error("lost_community_query_failed", response.status);
      return json({ error: "No se pudieron cargar las mascotas perdidas" }, 500);
    }

    const rows = await response.json();
    const pets = (Array.isArray(rows) ? rows : []).map((pet) => ({
      public_code: pet.public_code,
      name: pet.name,
      species: pet.species,
      breed: pet.breed,
      age_text: pet.age_text,
      photo_url: pet.photo_url,
      lost_location: pet.lost_location,
      lost_at: pet.lost_at,
      whatsapp: pet.public_contact === false ? null : (digits(pet.contact_whatsapp) || digits(pet.contact_phone) || null),
    }));

    return json({ ok: true, pets });
  } catch (error) {
    console.error("lost_community_error", error instanceof Error ? error.name : "UnknownError");
    return json({ error: "Error interno" }, 500);
  }
});
