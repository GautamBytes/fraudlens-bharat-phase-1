const JSON_HEADERS = {
  "cache-control": "no-store",
  "content-type": "application/json",
  "x-content-type-options": "nosniff",
};

function jsonError(detail: string, status: number): Response {
  return Response.json({ detail }, { status, headers: JSON_HEADERS });
}

function backendUrl(path: string): URL | null {
  const configured = process.env.FRAUDLENS_API_URL;
  if (!configured) return null;
  try {
    const base = new URL(configured);
    if (!new Set(["http:", "https:"]).has(base.protocol)) return null;
    base.pathname = "/";
    base.search = "";
    base.hash = "";
    return new URL(path.replace(/^\//, ""), base);
  } catch {
    return null;
  }
}

export async function fraudlensRequest(
  path: string,
  init: RequestInit = {},
  timeoutMs = 20_000,
): Promise<Response> {
  const url = backendUrl(path);
  if (!url) return jsonError("Analysis service is not configured", 503);

  const headers = new Headers(init.headers);
  const demoKey = process.env.FRAUDLENS_DEMO_API_KEY;
  if (demoKey) headers.set("X-FraudLens-Demo-Key", demoKey);

  try {
    const upstream = await fetch(url.toString(), {
      ...init,
      headers,
      cache: "no-store",
      signal: AbortSignal.timeout(timeoutMs),
    });
    const responseHeaders = new Headers({
      "cache-control": "no-store",
      "content-type": upstream.headers.get("content-type") ?? "application/json",
      "x-content-type-options": "nosniff",
    });
    const requestId = upstream.headers.get("x-request-id");
    if (requestId) responseHeaders.set("x-request-id", requestId);
    return new Response(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "TimeoutError") {
      return jsonError("Analysis service is still starting", 504);
    }
    return jsonError("Analysis service is unavailable", 502);
  }
}
