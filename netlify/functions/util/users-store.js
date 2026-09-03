const { getStore } = require("@netlify/blobs");

const KEY = "users.json";

function store() {
  const siteID = process.env.SITE_ID;
  const token = process.env.NETLIFY_FUNCTIONS_TOKEN || process.env.NETLIFY_API_TOKEN;
  if (siteID && token) {
    return getStore({ name: "users", siteID, token });
  }
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
