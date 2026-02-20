import mongoose from 'mongoose';

export interface IMigrationLog {
  _id: mongoose.Types.ObjectId;
  userId: string;              // Reference to UserNew._id
  username: string;            // Username for display
  oldCredits: number;          // Credits before migration
  newCredits: number;          // Credits after migration (oldCredits / 2.5)
  migratedAt: Date;            // Timestamp of migration
  oldRate: number;             // Old rate (1000)
  newRate: number;             // New rate (2500)
  autoMigrated: boolean;       // true if auto-migrated (zero credits), false if manual
}

const migrationLogSchema = new mongoose.Schema({
  userId: { type: String, required: true, index: true },
  username: { type: String, required: true },
  oldCredits: { type: Number, required: true },
  newCredits: { type: Number, required: true },
  migratedAt: { type: Date, default: Date.now, index: true },
  oldRate: { type: Number, required: true },
  newRate: { type: Number, required: true },
  autoMigrated: { type: Boolean, default: false },
});

// Compound index for querying by user with recent first
migrationLogSchema.index({ userId: 1, migratedAt: -1 });

export const MigrationLog = mongoose.model<IMigrationLog>(
  'MigrationLog',
  migrationLogSchema,
  'migration_logs'
);
