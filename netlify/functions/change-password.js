const { loadUsers, saveUsers } = require("./util/users-store");
const { verifyPassword, hashPassword, getSessionFromEvent } = require("./util/auth");

exports.handler = async (event) => {
  if (event.httpMethod !== "POST") {
    return { statusCode: 405, body: "Method Not Allowed" };
  }

  const session = getSessionFromEvent(event);
  if (!session) {
    return { statusCode: 401, body: JSON.stringify({ error: "Not logged in." }) };
  }

  let body;
  try {
    body = JSON.parse(event.body || "{}");
  } catch {
    return { statusCode: 400, body: JSON.stringify({ error: "Invalid JSON" }) };
  }

  const currentPassword = String(body.currentPassword || "");
  const newPassword = String(body.newPassword || "");

  if (newPassword.length < 8) {
    return { statusCode: 400, body: JSON.stringify({ error: "New password must be at least 8 characters." }) };
  }

  const users = await loadUsers();
  const user = users[session.sub];
  if (!user) {
    return { statusCode: 404, body: JSON.stringify({ error: "Account not found." }) };
  }

  if (!verifyPassword(currentPassword, user.salt, user.passwordHash)) {
    return { statusCode: 403, body: JSON.stringify({ error: "Current password is incorrect." }) };
  }

  const { salt, hash } = hashPassword(newPassword);
  user.salt = salt;
  user.passwordHash = hash;
  user.passwordChangedAt = new Date().toISOString();
  await saveUsers(users);

  return { statusCode: 200, body: JSON.stringify({ message: "Password changed." }) };
};
