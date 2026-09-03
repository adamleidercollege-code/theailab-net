const { loadUsers, saveUsers } = require("./util/users-store");
const { hashPassword } = require("./util/auth");

const USERNAME_RE = /^[a-zA-Z0-9._-]{3,40}$/;

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
  const name = String(body.name || "").trim();

  if (!USERNAME_RE.test(username)) {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: "Username must be 3-40 characters: letters, numbers, dot, dash, underscore." }),
    };
  }
  if (password.length < 8) {
    return { statusCode: 400, body: JSON.stringify({ error: "Password must be at least 8 characters." }) };
  }

  const users = await loadUsers();
  if (users[username]) {
    return { statusCode: 409, body: JSON.stringify({ error: "That username is already registered." }) };
  }

  const { salt, hash } = hashPassword(password);
  users[username] = {
    username,
    name: name || username,
    salt,
    passwordHash: hash,
    status: "pending",
    role: "student",
    createdAt: new Date().toISOString(),
  };
  await saveUsers(users);

  return {
    statusCode: 201,
    body: JSON.stringify({ message: "Registration received. An admin must approve your account before you can log in." }),
  };
};
