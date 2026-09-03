const { getSessionFromEvent } = require("./util/auth");

exports.handler = async (event) => {
  const session = getSessionFromEvent(event);
  if (!session) {
    return { statusCode: 200, body: JSON.stringify({ authenticated: false }) };
  }
  return {
    statusCode: 200,
    body: JSON.stringify({ authenticated: true, username: session.sub, role: session.role }),
  };
};
