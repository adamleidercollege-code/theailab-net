const { loadUsers, saveUsers } = require("./util/users-store");
const { hashPassword } = require("./util/auth");

const USERNAME_RE = /^[a-zA-Z0-9._-]{3,40}$/;

exports.handler = async (event) => {
  if (event.httpMethod !== "POST") {
    return { statusCode: 405, body: "Method Not Allowed" };
  }

  const bootstrapSecret = process.env.ADMIN_BOOTSTRAP_SECRET;
  if (!bootstrapSecret) {
    return { statusCode: 403, body: JSON.stringify({ error: "Bootstrap disabled." }) };
  }

  let body;
  try {
    body = JSON.parse(event.body || "{}");
  } catch {
    return { statusCode: 400, body: JSON.stringify({ error: "Invalid JSON" }) };
  }

  if (body.secret !== bootstrapSecret) {
    return { statusCode: 403, body: JSON.stringify({ error: "Invalid bootstrap secret." }) };
  }

  const username = String(body.username || "").trim().toLowerCase();
  const password = String(body.password || "");
  const name = String(body.name || "").trim();

  if (!USERNAME_RE.test(username) || password.length < 8) {
    return { statusCode: 400, body: JSON.stringify({ error: "Invalid username or password." }) };
  }

  const users = await loadUsers();
  const { salt, hash } = hashPassword(password);
  users[username] = {
    username,
    name: name || username,
    salt,
    passwordHash: hash,
    status: "approved",
    role: "admin",
    createdAt: new Date().toISOString(),
  };
  await saveUsers(users);

  return { statusCode: 201, body: JSON.stringify({ message: `Admin account '${username}' created.` }) };
};
