import { toNextJsHandler } from "better-auth/next-js";

import { auth } from "@/lib/auth";
import { authConfigurationError } from "@/lib/auth-configuration";

const handler = toNextJsHandler(auth);

function unavailable(): Response {
  return Response.json(
    { detail: "Authentication service is unavailable" },
    {
      status: 503,
      headers: {
        "cache-control": "no-store",
        "x-content-type-options": "nosniff",
      },
    },
  );
}

export async function GET(request: Request): Promise<Response> {
  if (authConfigurationError()) return unavailable();
  try {
    return await handler.GET(request);
  } catch {
    return unavailable();
  }
}

export async function POST(request: Request): Promise<Response> {
  if (authConfigurationError()) return unavailable();
  try {
    return await handler.POST(request);
  } catch {
    return unavailable();
  }
}
