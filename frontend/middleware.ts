import { NextRequest, NextResponse } from "next/server";
import auth0 from "@/lib/auth0";

/**
 * Protect all routes under /dashboard and /admin.
 * Unauthenticated requests are redirected to the Auth0 login page.
 */
export async function middleware(request: NextRequest) {
  const session = await auth0.getSession(request, new NextResponse());
  const { pathname } = request.nextUrl;

  const protectedPaths = ["/dashboard", "/admin"];
  const isProtected = protectedPaths.some((p) => pathname.startsWith(p));

  if (isProtected && !session) {
    const loginUrl = new URL("/api/auth/login", request.url);
    loginUrl.searchParams.set("returnTo", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/admin/:path*"],
};
