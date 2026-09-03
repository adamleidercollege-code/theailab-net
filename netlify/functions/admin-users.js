const { loadUsers } = require("./util/users-store");
const { getSessionFromEvent } = require("./util/auth");

exports.handler = async (event) => {
  const session = getSessionFromEvent(event);
  if (!session || session.role !== "admin") {
    return { statusCode: 403, body: JSON.stringify({ error: "Admin access required." }) };
  }

  const users = await loadUsers();
  const list = Object.values(users).map((u) => ({
    username: u.username,
    name: u.name,
    status: u.status,
    role: u.role,
    createdAt: u.createdAt,
  }));

  return { statusCode: 200, body: JSON.stringify({ users: list }) };
};
