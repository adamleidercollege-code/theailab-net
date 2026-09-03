exports.handler = async () => {
  const keys = Object.keys(process.env).filter((k) => /netlify|site|blob/i.test(k));
  const info = {};
  keys.forEach((k) => {
    info[k] = k.toLowerCase().includes("token") || k.toLowerCase().includes("secret") ? "[redacted]" : process.env[k];
  });
  return { statusCode: 200, body: JSON.stringify(info, null, 2) };
};
