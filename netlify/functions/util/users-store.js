const { getStore } = require("@netlify/blobs");

const KEY = "users.json";

function store() {
  return getStore("users");
}

async function loadUsers() {
  const raw = await store().get(KEY, { type: "json" });
  return raw || {};
}

async function saveUsers(users) {
  await store().setJSON(KEY, users);
}

module.exports = { loadUsers, saveUsers };
