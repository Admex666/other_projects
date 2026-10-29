const fs = require('fs');
const envText = fs.readFileSync('.env', 'utf8');
const tokenMatch = envText.match(/FB_PAGE_ACCESS_TOKEN="([^"]+)"/);
const pageMatch = envText.match(/FB_PAGE_ID="([^"]+)"/);

const token = tokenMatch ? tokenMatch[1] : '';
const pageId = pageMatch ? pageMatch[1] : '61574268396665';

console.log('Testing FB token with Page ID:', pageId);

async function run() {
  try {
    const pageRes = await fetch('https://graph.facebook.com/v21.0/' + pageId + '?fields=id,name,link,followers_count,fan_count&access_token=' + encodeURIComponent(token));
    const pageData = await pageRes.json();
    console.log('Page Data Status:', pageRes.status);
    console.log('Page Data:', JSON.stringify(pageData, null, 2));

    const postsRes = await fetch('https://graph.facebook.com/v21.0/' + pageId + '/posts?fields=id,message,created_time,shares,reactions.summary(true),comments.summary(true)&limit=5&access_token=' + encodeURIComponent(token));
    const postsData = await postsRes.json();
    console.log('Posts Data Status:', postsRes.status);
    console.log('Posts Count:', postsData.data ? postsData.data.length : 0);
    if (postsData.data) {
      postsData.data.forEach((p, idx) => {
        console.log(`[Post #${idx+1}] ID: ${p.id} | Date: ${p.created_time}`);
        console.log(`  Message: ${(p.message || '').slice(0, 80)}...`);
        console.log(`  Reactions: ${p.reactions?.summary?.total_count || 0} | Comments: ${p.comments?.summary?.total_count || 0} | Shares: ${p.shares?.count || 0}`);
      });
    } else if (postsData.error) {
      console.log('Posts Error:', postsData.error);
    }
  } catch (err) {
    console.error('Fetch error:', err);
  }
}

run();
