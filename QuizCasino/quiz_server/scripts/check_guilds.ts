import { MongoClient } from 'mongodb';

async function checkGuilds() {
  const uri = process.env.MONGODB_URI || "mongodb://localhost:27017/quizcasino";
  console.log(`Connecting to: ${uri.split('@')[1] || uri}`); // Log part of URI for debug safely
  const client = new MongoClient(uri);

  try {
    await client.connect();
    const db = client.db(); // Use default db from URI or atlas default
    const guilds = await db.collection('guilds').find({}).toArray();
    
    console.log(`Found ${guilds.length} guilds:`);
    guilds.forEach(g => {
      console.log(`- Name: ${g.name}, Tag: ${g.tag}, isPublic: ${g.isPublic}, Leader: ${g.leaderUsername}`);
    });
  } finally {
    await client.close();
  }
}

checkGuilds();
