import { fraudlensRequest } from "@/lib/server/fraudlens";

const MAX_JSON_BYTES = 24_000;

export async function POST(request: Request): Promise<Response> {
  if (!request.headers.get("content-type")?.toLowerCase().startsWith("application/json")) {
    return Response.json({ detail: "Expected a JSON analysis request" }, { status: 415 });
  }
  const body = await request.text();
  if (new TextEncoder().encode(body).byteLength > MAX_JSON_BYTES) {
    return Response.json({ detail: "Message request is too large" }, { status: 413 });
  }
  return fraudlensRequest("/analyze", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body,
  });
}
