const crypto = require("crypto");
const { loadUsers, saveUsers } = require("./util/users-store");
const { sendMail } = require("./util/mail");

const RESET_TTL_MS = 30 * 60 * 1000; // 30 minutes

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
  const genericResponse = {
    statusCode: 200,
    body: JSON.stringify({ message: "If that account exists, a reset link has been emailed to its registered contact." }),
  };

  if (!username) return genericResponse;

  const users = await loadUsers();
  const user = users[username];

  // Always return the same generic message so this endpoint can't be used to
  // enumerate which usernames are registered.
  if (!user || !user.email) return genericResponse;

  const token = crypto.randomBytes(32).toString("hex");
  user.resetToken = token;
  user.resetTokenExpires = Date.now() + RESET_TTL_MS;
  await saveUsers(users);

  const resetUrl = `https://theailab.net/reset-password.html?username=${encodeURIComponent(username)}&token=${token}`;

  await sendMail({
    to: user.email,
    subject: "Password reset requested — IPHS 400",
    html: `<p>A password reset was requested for the account <strong>${username}</strong>.</p>
<p><a href="${resetUrl}">Click here to set a new password</a> (link expires in 30 minutes).</p>
<p>If you didn't request this, you can ignore this email.</p>`,
    text: `A password reset was requested for account ${username}.\nReset here (expires in 30 minutes): ${resetUrl}\nIf you didn't request this, ignore this email.`,
  }).catch((err) => console.error("Failed to send reset email", err));

  return genericResponse;
};
