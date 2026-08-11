import { auth } from "@/lib/auth";
import { authConfigurationError } from "@/lib/auth-configuration";

const AUTH_HEADERS = {
  "cache-control": "no-store",
  "content-type": "application/json",
  "x-content-type-options": "nosniff",
};

export async function requireProfessorSession(request: Request): Promise<Response | null> {
  if (authConfigurationError()) {
    return Response.json(
      { detail: "Authentication service is unavailable" },
      { status: 503, headers: AUTH_HEADERS },
    );
  }
  let session: Awaited<ReturnType<typeof auth.api.getSession>>;
  try {
    session = await auth.api.getSession({ headers: request.headers });
  } catch {
    return Response.json(
      { detail: "Authentication service is unavailable" },
      { status: 503, headers: AUTH_HEADERS },
    );
  }
  if (session) return null;
  return Response.json(
    { detail: "Professor authentication required" },
    { status: 401, headers: AUTH_HEADERS },
  );
}
