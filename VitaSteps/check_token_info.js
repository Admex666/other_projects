const fs = require('fs');
const envText = fs.readFileSync('.env', 'utf8');
const tokenMatch = envText.match(/FB_PAGE_ACCESS_TOKEN="([^"]+)"/);
const token = tokenMatch ? tokenMatch[1] : '';

async function check() {
  const meRes = await fetch('https://graph.facebook.com/v21.0/me?access_token=' + encodeURIComponent(token));
  console.log('/me Status:', meRes.status);
  console.log('/me Body:', await meRes.json());

  const accountsRes = await fetch('https://graph.facebook.com/v21.0/me/accounts?access_token=' + encodeURIComponent(token));
  console.log('/me/accounts Status:', accountsRes.status);
  console.log('/me/accounts Body:', await accountsRes.json());
}

check();
