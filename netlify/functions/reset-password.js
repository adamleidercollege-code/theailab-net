const { loadUsers, saveUsers } = require("./util/users-store");
const { hashPassword } = require("./util/auth");

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
  const token = String(body.token || "");
  const newPassword = String(body.newPassword || "");

  if (newPassword.length < 8) {
    return { statusCode: 400, body: JSON.stringify({ error: "New password must be at least 8 characters." }) };
  }

  const users = await loadUsers();
  const user = users[username];

  const invalidResponse = {
    statusCode: 400,
    body: JSON.stringify({ error: "This reset link is invalid or has expired. Request a new one." }),
  };

  if (!user || !user.resetToken || !user.resetTokenExpires) return invalidResponse;
  if (user.resetToken !== token) return invalidResponse;
  if (Date.now() > user.resetTokenExpires) return invalidResponse;

  const { salt, hash } = hashPassword(newPassword);
  user.salt = salt;
  user.passwordHash = hash;
  user.passwordChangedAt = new Date().toISOString();
  delete user.resetToken;
  delete user.resetTokenExpires;
  await saveUsers(users);

  return { statusCode: 200, body: JSON.stringify({ message: "Password reset. You can now log in." }) };
};
