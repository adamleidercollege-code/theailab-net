const { loadUsers, saveUsers } = require("./util/users-store");
const { getSessionFromEvent } = require("./util/auth");

const VALID_ACTIONS = new Set(["approve", "reject"]);

exports.handler = async (event) => {
  if (event.httpMethod !== "POST") {
    return { statusCode: 405, body: "Method Not Allowed" };
  }

  const session = getSessionFromEvent(event);
  if (!session || session.role !== "admin") {
    return { statusCode: 403, body: JSON.stringify({ error: "Admin access required." }) };
  }

  let body;
  try {
    body = JSON.parse(event.body || "{}");
  } catch {
    return { statusCode: 400, body: JSON.stringify({ error: "Invalid JSON" }) };
  }

  const username = String(body.username || "").trim().toLowerCase();
  const action = String(body.action || "");

  if (!VALID_ACTIONS.has(action)) {
    return { statusCode: 400, body: JSON.stringify({ error: "action must be 'approve' or 'reject'." }) };
  }

  const users = await loadUsers();
  const user = users[username];
  if (!user) {
    return { statusCode: 404, body: JSON.stringify({ error: "User not found." }) };
  }

  user.status = action === "approve" ? "approved" : "rejected";
  user.decidedAt = new Date().toISOString();
  await saveUsers(users);

  return { statusCode: 200, body: JSON.stringify({ message: `User ${username} ${user.status}.` }) };
};
