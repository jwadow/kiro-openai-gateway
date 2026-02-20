import 'dotenv/config';
import mongoose from 'mongoose';
import { Proxy } from './db/mongodb.js';

const MONGODB_URI = process.env.MONGODB_URI || '';

const proxies = [
  { id: 'proxy-1', name: 'Proxy VN 1', type: 'http', host: '160.250.166.89', port: 25265, username: 'hjsad1995', password: 'aa0908700714' },
  { id: 'proxy-2', name: 'Proxy VN 2', type: 'http', host: '113.160.166.31', port: 11161, username: 'hjsad1994', password: 'aa0908700714' },
];

async function seed() {
  console.log('🌱 Starting seed...');

  await mongoose.connect(MONGODB_URI, { dbName: process.env.MONGODB_DB_NAME || 'fproxy' });
  console.log('✅ Connected to MongoDB');

  // Seed Proxies
  console.log('\n🌐 Seeding Proxies...');
  for (const proxy of proxies) {
    const existing = await Proxy.findById(proxy.id);
    if (existing) {
      console.log(`  ⏭️  ${proxy.id} (${proxy.name}) already exists`);
    } else {
      await Proxy.create({
        _id: proxy.id,
        name: proxy.name,
        type: proxy.type,
        host: proxy.host,
        port: proxy.port,
        username: proxy.username,
        password: proxy.password,
        status: 'unknown',
        isActive: true,
      });
      console.log(`  ✅ Created ${proxy.id} (${proxy.name}) - ${proxy.host}:${proxy.port}`);
    }
  }

  console.log('\n✅ Seed completed!');
  console.log('\nSummary:');
  console.log(`  Proxies: ${await Proxy.countDocuments()}`);

  await mongoose.disconnect();
}

seed().catch(err => {
  console.error('❌ Seed failed:', err);
  process.exit(1);
});
