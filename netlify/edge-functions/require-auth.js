function base64UrlToUint8Array(b64url) {
  const b64 = b64url.replace(/-/g, "+").replace(/_/g, "/");
  const pad = b64.length % 4 === 0 ? "" : "=".repeat(4 - (b64.length % 4));
  const bin = atob(b64 + pad);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes;
}

async function hmacSha256Base64Url(secret, message) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const sigBuf = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(message));
  const bytes = new Uint8Array(sigBuf);
  let bin = "";
  bytes.forEach((b) => (bin += String.fromCharCode(b)));
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function parseCookies(header) {
  const out = {};
  if (!header) return out;
  header.split(";").forEach((part) => {
    const idx = part.indexOf("=");
    if (idx === -1) return;
    out[part.slice(0, idx).trim()] = decodeURIComponent(part.slice(idx + 1).trim());
  });
  return out;
}

async function verifySession(token, secret) {
  if (!token || !token.includes(".")) return null;
  const [b64, sig] = token.split(".");
  const expected = await hmacSha256Base64Url(secret, b64);
  if (expected !== sig) return null;
  try {
    const json = new TextDecoder().decode(base64UrlToUint8Array(b64));
    const payload = JSON.parse(json);
    if (payload.exp && Date.now() / 1000 > payload.exp) return null;
    return payload;
  } catch {
    return null;
  }
}

export default async (request, context) => {
  const secret = Netlify.env.get("SESSION_SECRET");
  const cookies = parseCookies(request.headers.get("cookie"));
  const session = secret ? await verifySession(cookies.iphs_session, secret) : null;

  if (!session) {
    const url = new URL(request.url);
    const loginUrl = new URL("/login.html", url.origin);
    loginUrl.searchParams.set("next", url.pathname);
    return Response.redirect(loginUrl.toString(), 302);
  }

  return context.next();
};

export const config = {
  path: ["/weeks/*", "/core/*"],
};
