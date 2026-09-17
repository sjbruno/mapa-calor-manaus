import { AwsClient } from "aws4fetch";

export const config = { runtime: "edge" };

// Schema fechado: nenhum campo fora daqui chega a ser gravado.
// Nada de IP, user-agent bruto ou qualquer identificador pessoal.
const ALLOWED_EVENTS = new Set([
  "pageview",
  "section",
  "section_time",
  "share_button_clicked",
  "link_click",
]);

function str(value, maxLen) {
  if (typeof value !== "string") return undefined;
  const trimmed = value.trim().slice(0, maxLen);
  return trimmed.length ? trimmed : undefined;
}

function num(value, min, max) {
  if (typeof value !== "number" || !Number.isFinite(value)) return undefined;
  const rounded = Math.round(value);
  if (rounded < min || rounded > max) return undefined;
  return rounded;
}

function buildEvent(body) {
  const eventType = str(body.event, 40);
  if (!eventType || !ALLOWED_EVENTS.has(eventType)) return null;

  const sessionId = str(body.session_id, 60);
  if (!sessionId || !/^[a-f0-9-]{20,60}$/i.test(sessionId)) return null;

  const event = {
    event: eventType,
    session_id: sessionId,
    device_type: body.device_type === "mobile" ? "mobile" : "desktop",
    path: str(body.path, 300) ?? "/",
    ts: new Date().toISOString(),
  };

  if (eventType === "pageview") {
    event.referrer_domain = str(body.referrer_domain, 200);
    event.utm_source = str(body.utm_source, 100);
    event.utm_medium = str(body.utm_medium, 100);
    event.utm_campaign = str(body.utm_campaign, 100);
    event.utm_content = str(body.utm_content, 100);
    event.utm_term = str(body.utm_term, 100);
  } else if (eventType === "section") {
    event.section_id = str(body.section_id, 40);
    if (!event.section_id) return null;
  } else if (eventType === "section_time") {
    event.section_id = str(body.section_id, 40);
    event.duration_ms = num(body.duration_ms, 1, 3600000); // teto de 1h contra payload adulterado
    if (!event.section_id || event.duration_ms === undefined) return null;
  } else if (eventType === "link_click") {
    event.url = str(body.url, 500);
    event.outbound = body.outbound === true;
    if (!event.url) return null;
  }
  // share_button_clicked não carrega campos extras.

  return event;
}

export default async function handler(req) {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  const { R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME } = process.env;
  if (!R2_ACCOUNT_ID || !R2_ACCESS_KEY_ID || !R2_SECRET_ACCESS_KEY || !R2_BUCKET_NAME) {
    return new Response("Server misconfigured", { status: 500 });
  }

  let body;
  try {
    body = await req.json();
  } catch {
    return new Response("Bad Request", { status: 400 });
  }

  const event = buildEvent(body ?? {});
  if (!event) {
    return new Response("Bad Request", { status: 400 });
  }

  const day = event.ts.slice(0, 10);
  const key = `events/${day}/${crypto.randomUUID()}.json`;
  const endpoint = `https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com/${R2_BUCKET_NAME}/${key}`;

  const client = new AwsClient({
    accessKeyId: R2_ACCESS_KEY_ID,
    secretAccessKey: R2_SECRET_ACCESS_KEY,
    service: "s3",
    region: "auto",
  });

  const upload = await client.fetch(endpoint, {
    method: "PUT",
    body: JSON.stringify(event),
    headers: { "Content-Type": "application/json" },
  });

  if (!upload.ok) {
    return new Response("Upstream error", { status: 502 });
  }

  return new Response(null, { status: 204 });
}
