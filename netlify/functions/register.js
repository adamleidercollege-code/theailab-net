const { loadUsers, saveUsers } = require("./util/users-store");
const { hashPassword } = require("./util/auth");
const { sendMail } = require("./util/mail");

const ADMIN_NOTIFY_EMAIL = "jonchun2000@gmail.com";

const USERNAME_RE = /^[a-zA-Z0-9._-]{3,40}$/;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

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
  const email = String(body.email || "").trim().toLowerCase();

  if (!USERNAME_RE.test(username)) {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: "Username must be 3-40 characters: letters, numbers, dot, dash, underscore." }),
    };
  }
  if (password.length < 8) {
    return { statusCode: 400, body: JSON.stringify({ error: "Password must be at least 8 characters." }) };
  }
  if (!EMAIL_RE.test(email)) {
    return { statusCode: 400, body: JSON.stringify({ error: "A valid email address is required (used for password resets)." }) };
  }

  const users = await loadUsers();
  if (users[username]) {
    return { statusCode: 409, body: JSON.stringify({ error: "That username is already registered." }) };
  }

  const { salt, hash } = hashPassword(password);
  users[username] = {
    username,
    name: name || username,
    email,
    salt,
    passwordHash: hash,
    status: "pending",
    role: "student",
    createdAt: new Date().toISOString(),
  };
  await saveUsers(users);

  await sendMail({
    to: ADMIN_NOTIFY_EMAIL,
    subject: `New account request: ${username}`,
    html: `<p>A new account application is pending approval.</p>
<ul>
<li><strong>Username:</strong> ${username}</li>
<li><strong>Name:</strong> ${name || username}</li>
<li><strong>Email:</strong> ${email}</li>
<li><strong>Requested:</strong> ${new Date().toISOString()}</li>
</ul>
<p><a href="https://theailab.net/core/admin.html">Review pending accounts</a></p>`,
    text: `New account application pending approval.\nUsername: ${username}\nName: ${name || username}\nEmail: ${email}\nReview at https://theailab.net/core/admin.html`,
  }).catch((err) => console.error("Failed to send admin notification email", err));

  return {
    statusCode: 201,
    body: JSON.stringify({ message: "Registration received. An admin must approve your account before you can log in." }),
  };
};
