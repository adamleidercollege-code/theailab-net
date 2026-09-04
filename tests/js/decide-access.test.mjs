import test from "node:test";
import assert from "node:assert/strict";
import { decideAccess, resolveGateEnabled } from "../../netlify/edge-functions/lib/decide-access.mjs";

const STUDENT_SESSION = { sub: "student1", role: "student" };
const ADMIN_SESSION = { sub: "jchun", role: "admin" };

test("gate disabled: /core/syllabus.html is allowed with no session", () => {
  const result = decideAccess({ pathname: "/core/syllabus.html", gateEnabled: false, session: null });
  assert.equal(result.action, "allow");
});

test("gate disabled: /weeks/week-03.html is allowed with no session", () => {
  const result = decideAccess({ pathname: "/weeks/week-03.html", gateEnabled: false, session: null });
  assert.equal(result.action, "allow");
});

test("gate enabled: /core/syllabus.html with no session redirects to login", () => {
  const result = decideAccess({ pathname: "/core/syllabus.html", gateEnabled: true, session: null });
  assert.equal(result.action, "redirect");
  assert.equal(result.redirectTo, "/login.html?next=%2Fcore%2Fsyllabus.html");
});

test("gate enabled: /weeks/week-03.html with no session redirects to login", () => {
  const result = decideAccess({ pathname: "/weeks/week-03.html", gateEnabled: true, session: null });
  assert.equal(result.action, "redirect");
  assert.equal(result.redirectTo, "/login.html?next=%2Fweeks%2Fweek-03.html");
});

test("gate enabled: /core/syllabus.html with a valid student session is allowed", () => {
  const result = decideAccess({ pathname: "/core/syllabus.html", gateEnabled: true, session: STUDENT_SESSION });
  assert.equal(result.action, "allow");
});

test("gate enabled: /weeks/week-03.html with a valid admin session is allowed", () => {
  const result = decideAccess({ pathname: "/weeks/week-03.html", gateEnabled: true, session: ADMIN_SESSION });
  assert.equal(result.action, "allow");
});

test("admin route (/admin) always requires admin role, gate disabled, no session", () => {
  const result = decideAccess({ pathname: "/admin", gateEnabled: false, session: null });
  assert.equal(result.action, "redirect");
  assert.equal(result.redirectTo, "/login.html?next=%2Fadmin");
});

test("admin route (/core/admin.html) always requires admin role, gate disabled, no session", () => {
  const result = decideAccess({ pathname: "/core/admin.html", gateEnabled: false, session: null });
  assert.equal(result.action, "redirect");
  assert.equal(result.redirectTo, "/login.html?next=%2Fcore%2Fadmin.html");
});

test("admin route: gate disabled, student session, still redirects (not admin)", () => {
  const result = decideAccess({ pathname: "/admin", gateEnabled: false, session: STUDENT_SESSION });
  assert.equal(result.action, "redirect");
  assert.equal(result.redirectTo, "/login.html?next=%2Fadmin");
});

test("admin route: gate enabled, student session, still redirects (not admin)", () => {
  const result = decideAccess({ pathname: "/core/admin.html", gateEnabled: true, session: STUDENT_SESSION });
  assert.equal(result.action, "redirect");
});

test("admin route: gate disabled, admin session, allowed", () => {
  const result = decideAccess({ pathname: "/admin", gateEnabled: false, session: ADMIN_SESSION });
  assert.equal(result.action, "allow");
});

test("admin route: gate enabled, admin session, allowed", () => {
  const result = decideAccess({ pathname: "/core/admin.html", gateEnabled: true, session: ADMIN_SESSION });
  assert.equal(result.action, "allow");
});

test("expired/invalid session (null) on a gated course page redirects", () => {
  const result = decideAccess({ pathname: "/core/policies.html", gateEnabled: true, session: null });
  assert.equal(result.action, "redirect");
});

test("gate enabled with malformed session object missing role is treated as non-admin for /admin", () => {
  const result = decideAccess({ pathname: "/admin", gateEnabled: true, session: { sub: "x" } });
  assert.equal(result.action, "redirect");
});

test("query string and hash on the original path are preserved in next param", () => {
  const result = decideAccess({ pathname: "/weeks/week-05.html", gateEnabled: true, session: null });
  assert.equal(result.redirectTo, "/login.html?next=%2Fweeks%2Fweek-05.html");
});

// --- resolveGateEnabled: fail-safe default when the env var is missing/malformed ---

test("resolveGateEnabled: undefined (env var unset) fails safe to gated (true)", () => {
  assert.equal(resolveGateEnabled(undefined), true);
});

test("resolveGateEnabled: null fails safe to gated (true)", () => {
  assert.equal(resolveGateEnabled(null), true);
});

test('resolveGateEnabled: explicit "false" string means open (false)', () => {
  assert.equal(resolveGateEnabled("false"), false);
});

test('resolveGateEnabled: explicit "true" string means gated (true)', () => {
  assert.equal(resolveGateEnabled("true"), true);
});

test("resolveGateEnabled: empty string fails safe to gated (true)", () => {
  assert.equal(resolveGateEnabled(""), true);
});

test('resolveGateEnabled: unrecognized value (e.g. typo "flase") fails safe to gated (true)', () => {
  assert.equal(resolveGateEnabled("flase"), true);
});

test("resolveGateEnabled: is case-insensitive for the false value", () => {
  assert.equal(resolveGateEnabled("FALSE"), false);
  assert.equal(resolveGateEnabled("False"), false);
});
