const { clearSessionCookie } = require("./util/auth");

exports.handler = async () => {
  return {
    statusCode: 200,
    headers: { "Set-Cookie": clearSessionCookie() },
    body: JSON.stringify({ message: "Logged out." }),
  };
};
