const { sendMail } = require("./util/mail");

exports.handler = async () => {
  try {
    const result = await sendMail({
      to: "jonchun2000@gmail.com",
      subject: "Debug: registration mail path test",
      html: "<p>This came from the debug-mail function, using the same sendMail() util as register.js.</p>",
      text: "This came from the debug-mail function, using the same sendMail() util as register.js.",
    });
    return { statusCode: 200, body: JSON.stringify({ result }) };
  } catch (err) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: err.message, stack: err.stack }),
    };
  }
};
