import { MongoClient } from 'mongodb';

async function migrateGuilds() {
  const uri = process.env.MONGODB_URI || "mongodb://localhost:27017/quizcasino";
  const client = new MongoClient(uri);

  try {
    await client.connect();
    const db = client.db();
    const result = await db.collection('guilds').updateMany(
      { isPublic: { $exists: false } },
      { $set: { isPublic: true, pendingRequests: [] } }
    );
    
    console.log(`Updated ${result.modifiedCount} guilds.`);
  } finally {
    await client.close();
  }
}

migrateGuilds();
