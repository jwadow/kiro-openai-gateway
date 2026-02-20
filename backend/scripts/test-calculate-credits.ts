import 'dotenv/config';
import mongoose from 'mongoose';

const CURRENT_RATE = 1500;
const NEW_RATE = 2500;

async function main() {
  try {
    console.log('Starting script...');
    console.log('MONGODB_URI:', process.env.MONGODB_URI ? 'exists' : 'not found');

    const uri = process.env.MONGODB_URI;
    if (!uri) {
      throw new Error('MONGODB_URI not found in environment');
    }

    console.log('Connecting to MongoDB...');
    await mongoose.connect(uri);
    console.log('Connected!');

    const UserNew = mongoose.model('UserNew', new mongoose.Schema({
      _id: String,
      creditsNew: Number,
      role: String,
    }, { strict: false }), 'usersNew');

    console.log('Counting documents...');
    const count = await UserNew.countDocuments({ creditsNew: { $gt: 0 } });
    console.log(`Found ${count} users with creditsNew > 0`);

    if (count > 0) {
      console.log('\nFetching users...');
      const users = await UserNew.find({ creditsNew: { $gt: 0 } })
        .select('_id creditsNew role')
        .sort({ creditsNew: -1 })
        .limit(10)
        .lean();

      console.log(`\nTop ${users.length} users:`);
      let total = 0;
      users.forEach((user: any, i: number) => {
        const converted = user.creditsNew * (CURRENT_RATE / NEW_RATE);
        total += user.creditsNew;
        console.log(`${i+1}. ${user._id}: $${user.creditsNew.toFixed(2)} -> $${converted.toFixed(2)}`);
      });

      // Get total for all users
      const allUsers = await UserNew.find({ creditsNew: { $gt: 0 } })
        .select('creditsNew')
        .lean();

      const totalCurrent = allUsers.reduce((sum: number, u: any) => sum + u.creditsNew, 0);
      const totalConverted = totalCurrent * (CURRENT_RATE / NEW_RATE);

      console.log(`\n=== TOTAL ===`);
      console.log(`Total users: ${allUsers.length}`);
      console.log(`Total creditsNew (rate ${CURRENT_RATE}): $${totalCurrent.toFixed(2)}`);
      console.log(`Total creditsNew (rate ${NEW_RATE}): $${totalConverted.toFixed(2)}`);
      console.log(`Difference: -$${(totalCurrent - totalConverted).toFixed(2)} (-${(((totalCurrent - totalConverted) / totalCurrent) * 100).toFixed(2)}%)`);
    }

    await mongoose.disconnect();
    console.log('\nDisconnected');
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

main();
