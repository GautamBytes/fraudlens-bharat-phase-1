const PUBLIC_PATHS = new Set(["/", "/login", "/api/health"]);

export function requiresProfessorSession(pathname: string): boolean {
  if (PUBLIC_PATHS.has(pathname)) return false;
  return !pathname.startsWith("/api/auth/");
}

export function safeReturnPath(value: string | null): string {
  if (!value || !value.startsWith("/")) return "/analyze";
  try {
    const decoded = decodeURIComponent(value);
    if (decoded.startsWith("//") || decoded.includes("\\")) return "/analyze";
    const destination = new URL(decoded, "https://fraudlens.local");
    if (destination.origin !== "https://fraudlens.local") return "/analyze";
    if (!requiresProfessorSession(destination.pathname) || destination.pathname === "/login") {
      return "/analyze";
    }
    return `${destination.pathname}${destination.search}${destination.hash}`;
  } catch {
    return "/analyze";
  }
}
