import { getCookieCache } from "better-auth/cookies";
import { NextRequest, NextResponse } from "next/server";

import { authConfigurationError, BUILD_ONLY_AUTH_SECRET } from "@/lib/auth-configuration";

export async function proxy(request: NextRequest): Promise<NextResponse> {
  if (!authConfigurationError()) {
    try {
      const session = await getCookieCache(request, {
        secret: process.env.BETTER_AUTH_SECRET ?? BUILD_ONLY_AUTH_SECRET,
        strategy: "jwe",
        isSecure: process.env.NODE_ENV === "production",
      });
      if (session) return NextResponse.next();
    } catch {
      // Invalid, truncated, or unverifiable cookies are treated as unauthenticated.
    }
  }
  const login = new URL("/login", request.url);
  login.searchParams.set("returnTo", `${request.nextUrl.pathname}${request.nextUrl.search}`);
  return NextResponse.redirect(login);
}

export const config = {
  matcher: ["/analyze/:path*", "/relationships/:path*", "/research/:path*", "/guide/:path*"],
};
