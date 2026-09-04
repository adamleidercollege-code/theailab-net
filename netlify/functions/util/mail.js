const RESEND_API_URL = "https://api.resend.com/emails";

async function sendMail({ to, subject, html, text }) {
  const apiKey = process.env.RESEND_API_KEY;
  const from = process.env.MAIL_FROM || "onboarding@resend.dev";

  if (!apiKey) {
    console.warn("RESEND_API_KEY not set; skipping email send:", subject);
    return { skipped: true };
  }

  const res = await fetch(RESEND_API_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from,
      to: Array.isArray(to) ? to : [to],
      subject,
      html,
      text: text || undefined,
    }),
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    console.error("Resend API error", res.status, body);
    return { skipped: false, ok: false, status: res.status };
  }

  return { skipped: false, ok: true };
}

module.exports = { sendMail };
