const { loadUsers } = require("./util/users-store");
const { verifyPassword, makeSessionCookie } = require("./util/auth");

exports.handler = async (event) => {
  if (event.httpMethod !== "POST") {
    return { statusCode: 405, body: "Method Not Allowed" };
  }

  let body;
  try {
    body = JSON.parse(event.body || "{}");
  } catch {
    return { statusCode: 400, body: JSON.stringify({ error: "Invalid JSON" }) };
  }

  const username = String(body.username || "").trim().toLowerCase();
  const password = String(body.password || "");

  const users = await loadUsers();
  const user = users[username];

  const invalidResponse = {
    statusCode: 401,
    body: JSON.stringify({ error: "Invalid username or password." }),
  };

  if (!user) return invalidResponse;
  if (!verifyPassword(password, user.salt, user.passwordHash)) return invalidResponse;

  if (user.status === "pending") {
    return { statusCode: 403, body: JSON.stringify({ error: "Your account is still pending admin approval." }) };
  }
  if (user.status === "rejected") {
    return { statusCode: 403, body: JSON.stringify({ error: "Your account request was not approved." }) };
  }

  return {
    statusCode: 200,
    headers: { "Set-Cookie": makeSessionCookie(user) },
    body: JSON.stringify({ message: "Logged in.", role: user.role }),
  };
};
