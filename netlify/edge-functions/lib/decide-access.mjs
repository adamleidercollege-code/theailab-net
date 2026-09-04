const ADMIN_PATHS = new Set(["/admin", "/core/admin.html"]);

/**
 * Fails safe: any value other than the literal string "false" (case-insensitive)
 * is treated as gate-enabled, including an unset/missing env var. This means a
 * misconfigured or absent GATE_ENABLED env var gates the site rather than
 * silently exposing it.
 */
export function resolveGateEnabled(rawValue) {
  if (typeof rawValue !== "string") return true;
  return rawValue.toLowerCase() !== "false";
}

function isAdminSession(session) {
  return !!session && session.role === "admin";
}

function loginRedirect(pathname) {
  return `/login.html?next=${encodeURIComponent(pathname)}`;
}

export function decideAccess({ pathname, gateEnabled, session }) {
  if (ADMIN_PATHS.has(pathname)) {
    if (isAdminSession(session)) {
      return { action: "allow" };
    }
    return { action: "redirect", redirectTo: loginRedirect(pathname) };
  }

  if (!gateEnabled) {
    return { action: "allow" };
  }

  if (session) {
    return { action: "allow" };
  }

  return { action: "redirect", redirectTo: loginRedirect(pathname) };
}
