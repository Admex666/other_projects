const pageToken = 'EAAauWb397U4BS02Hudia1VIkYAHQ5fpHo6sWaCX3dufCjazKMcwJ0HDRp7CHPo427q1bWZByhV6ZAWZAZBprrivPzY6eIOr3kOFUGYfMRfV7jdHkS0TN4pOFdjnODYRGr96GJY8VYSIK9u5zt59nZAWVGWVac4pcoEhc14vuZBzKpQZAxXd4UUJ2bMfNgQPCZBrR3pYdWiMPtKEGxshKMUHhM79F79r1kPHqct4nlzcZD';
const pageId = '1014443515092673';

async function testPageToken() {
  const pRes = await fetch('https://graph.facebook.com/v21.0/' + pageId + '?fields=id,name,link,followers_count,fan_count&access_token=' + encodeURIComponent(pageToken));
  console.log('Page info status:', pRes.status);
  console.log('Page info:', await pRes.json());

  const postsRes = await fetch('https://graph.facebook.com/v21.0/' + pageId + '/posts?fields=id,message,created_time,shares,reactions.summary(true),comments.summary(true)&limit=5&access_token=' + encodeURIComponent(pageToken));
  console.log('Posts status:', postsRes.status);
  const postsData = await postsRes.json();
  console.log('Posts count:', postsData.data ? postsData.data.length : 0);
  if (postsData.data) {
    postsData.data.forEach((p, idx) => {
      console.log(`[Poszt #${idx+1}] ID: ${p.id} | Dátum: ${p.created_time}`);
      console.log(`  Szöveg: ${(p.message || '').slice(0, 100)}...`);
      console.log(`  Lájkok/Reakciók: ${p.reactions?.summary?.total_count || 0} | Kommentek: ${p.comments?.summary?.total_count || 0} | Megosztások: ${p.shares?.count || 0}`);
    });
  } else {
    console.log('Posts Error:', postsData.error);
  }
}

testPageToken();
