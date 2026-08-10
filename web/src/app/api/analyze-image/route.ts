import { fraudlensRequest } from "@/lib/server/fraudlens";

export const WEB_IMAGE_MAX_BYTES = 4_000_000;
const IMAGE_TYPES = new Set(["image/png", "image/jpeg"]);

export async function POST(request: Request): Promise<Response> {
  const mediaType = request.headers.get("content-type")?.split(";", 1)[0].trim().toLowerCase();
  if (!mediaType || !IMAGE_TYPES.has(mediaType)) {
    return Response.json({ detail: "Use a PNG or JPEG screenshot" }, { status: 415 });
  }

  const contentLength = request.headers.get("content-length");
  if (contentLength && (!/^\d+$/.test(contentLength) || Number(contentLength) > WEB_IMAGE_MAX_BYTES)) {
    return Response.json({ detail: "Screenshot must be under 4 MB" }, { status: 413 });
  }
  const body = await request.arrayBuffer();
  if (body.byteLength > WEB_IMAGE_MAX_BYTES) {
    return Response.json({ detail: "Screenshot must be under 4 MB" }, { status: 413 });
  }

  const sourceUrl = new URL(request.url);
  const storeCase = sourceUrl.searchParams.get("store_case") === "true" ? "true" : "false";
  return fraudlensRequest(
    `/analyze-image?store_case=${storeCase}`,
    { method: "POST", headers: { "content-type": mediaType }, body },
    65_000,
  );
}
