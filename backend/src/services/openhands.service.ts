import mongoose from 'mongoose';

export interface OpenHandsKey {
  _id: string;
  apiKey: string;
  status: string;
  tokensUsed: number;
  requestsCount: number;
  lastError?: string;
  cooldownUntil?: Date;
  createdAt: Date;
  updatedAt?: Date;
  // Rotation tracking
  replacedBy?: string;      // Backup key ID that replaced this key's API
  replacedAt?: Date;        // When the replacement happened
  previousApiKey?: string;  // Masked version of old API key
  // Spend tracking
  lastUsedAt?: Date;
  totalSpend?: number;
  lastSpendCheck?: Date;
}

export interface OpenHandsKeyBinding {
  _id?: any;
  proxyId: string;
  openhandsKeyId: string;
  priority: number;
  isActive: boolean;
  createdAt: Date;
}

export interface Proxy {
  _id: string;
  name: string;
  type: string;
  host: string;
  port: number;
  status: string;
  isActive: boolean;
}

function getCollection(name: string) {
  return mongoose.connection.db!.collection(name);
}

// Keys
export async function listKeys(): Promise<OpenHandsKey[]> {
  const result = await getCollection('openhands_keys').find({}).toArray();
  return result as any;
}

export async function getKey(id: string): Promise<OpenHandsKey | null> {
  const result = await getCollection('openhands_keys').findOne({ _id: id as any });
  return result as any;
}

export async function createKey(data: { id: string; apiKey: string }): Promise<OpenHandsKey> {
  const key = {
    _id: data.id,
    apiKey: data.apiKey,
    status: 'healthy',
    tokensUsed: 0,
    requestsCount: 0,
    createdAt: new Date(),
  };
  await getCollection('openhands_keys').insertOne(key as any);
  return key as any;
}

export async function updateKey(id: string, data: Partial<OpenHandsKey>): Promise<OpenHandsKey | null> {
  const result = await getCollection('openhands_keys').findOneAndUpdate(
    { _id: id as any },
    { $set: { ...data, updatedAt: new Date() } },
    { returnDocument: 'after' }
  );
  return result as any;
}

export async function deleteKey(id: string): Promise<boolean> {
  // Check if key exists first (avoid unnecessary deletes)
  const key = await getKey(id);
  if (!key) {
    console.log(`[DeleteKey] Key ${id} not found (already deleted)`);
    return false;
  }

  // Delete all bindings for this key (no history needed - key can't be reused)
  const bindingsResult = await getCollection('openhands_bindings').deleteMany({ openhandsKeyId: id });
  console.log(`[DeleteKey] Deleted ${bindingsResult.deletedCount} bindings for key ${id}`);

  // Delete the key from database
  const result = await getCollection('openhands_keys').deleteOne({ _id: id as any });
  console.log(`[DeleteKey] Deleted key ${id} (deleted: ${result.deletedCount > 0})`);
  
  return result.deletedCount > 0;
}

export async function resetKeyStats(id: string): Promise<OpenHandsKey | null> {
  const result = await getCollection('openhands_keys').findOneAndUpdate(
    { _id: id as any },
    { $set: { status: 'healthy', tokensUsed: 0, requestsCount: 0, lastError: null, cooldownUntil: null } },
    { returnDocument: 'after' }
  );
  return result as any;
}

// Bindings
export async function listBindings(): Promise<OpenHandsKeyBinding[]> {
  const result = await getCollection('openhands_bindings').find({}).sort({ proxyId: 1, priority: 1 }).toArray();
  return result as any;
}

export async function getBindingsForProxy(proxyId: string): Promise<OpenHandsKeyBinding[]> {
  const result = await getCollection('openhands_bindings').find({ proxyId }).sort({ priority: 1 }).toArray();
  return result as any;
}

export async function createBinding(data: { proxyId: string; openhandsKeyId: string; priority: number }): Promise<OpenHandsKeyBinding> {
  const binding = {
    proxyId: data.proxyId,
    openhandsKeyId: data.openhandsKeyId,
    priority: data.priority,
    isActive: true,
    createdAt: new Date(),
  };
  const result = await getCollection('openhands_bindings').insertOne(binding);
  return { ...binding, _id: result.insertedId } as any;
}

export async function updateBinding(proxyId: string, openhandsKeyId: string, data: Partial<OpenHandsKeyBinding>): Promise<OpenHandsKeyBinding | null> {
  const result = await getCollection('openhands_bindings').findOneAndUpdate(
    { proxyId, openhandsKeyId },
    { $set: data },
    { returnDocument: 'after' }
  );
  return result as any;
}

export async function deleteBinding(proxyId: string, openhandsKeyId: string): Promise<boolean> {
  const result = await getCollection('openhands_bindings').deleteOne({ proxyId, openhandsKeyId });
  return result.deletedCount > 0;
}

export async function deleteAllBindingsForProxy(proxyId: string): Promise<number> {
  const result = await getCollection('openhands_bindings').deleteMany({ proxyId });
  return result.deletedCount;
}

// Proxies (read-only)
export async function listProxies(): Promise<Proxy[]> {
  const result = await getCollection('proxies').find({}).toArray();
  return result as any;
}

// Stats
export async function getStats() {
  const [keys, bindings, proxies, healthyKeys] = await Promise.all([
    getCollection('openhands_keys').countDocuments(),
    getCollection('openhands_bindings').countDocuments({ isActive: true }),
    getCollection('proxies').countDocuments({ isActive: true }),
    getCollection('openhands_keys').countDocuments({ status: 'healthy' }),
  ]);

  return { totalKeys: keys, healthyKeys, totalBindings: bindings, totalProxies: proxies };
}

// ============ BACKUP KEYS ============

export interface OpenHandsBackupKey {
  _id: string;
  apiKey: string;
  isUsed: boolean;
  activated: boolean;
  usedFor?: string;
  usedAt?: Date;
  createdAt: Date;
}

export async function listBackupKeys(): Promise<OpenHandsBackupKey[]> {
  const result = await getCollection('openhands_backup_keys').find({}).sort({ createdAt: -1 }).toArray();
  return result as any;
}

export async function getBackupKeyStats() {
  const cutoff24h = new Date(Date.now() - 24 * 60 * 60 * 1000);
  const [total, available, used, usedIn24h] = await Promise.all([
    getCollection('openhands_backup_keys').countDocuments(),
    getCollection('openhands_backup_keys').countDocuments({ isUsed: false }),
    getCollection('openhands_backup_keys').countDocuments({ isUsed: true }),
    getCollection('openhands_backup_keys').countDocuments({ isUsed: true, usedAt: { $gte: cutoff24h } }),
  ]);
  return { total, available, used, usedIn24h };
}

export async function createBackupKey(data: { id: string; apiKey: string }): Promise<OpenHandsBackupKey> {
  const key = {
    _id: data.id,
    apiKey: data.apiKey,
    isUsed: false,
    activated: false,
    createdAt: new Date(),
  };
  await getCollection('openhands_backup_keys').insertOne(key as any);
  return key as any;
}

export async function deleteBackupKey(id: string): Promise<boolean> {
  const result = await getCollection('openhands_backup_keys').deleteOne({ _id: id as any });
  return result.deletedCount > 0;
}

export async function restoreBackupKey(id: string): Promise<boolean> {
  const result = await getCollection('openhands_backup_keys').updateOne(
    { _id: id as any },
    { $set: { isUsed: false, activated: false, usedFor: null, usedAt: null } }
  );
  return result.modifiedCount > 0;
}

// ============ REPAIR/SYNC BINDINGS ============

export interface RepairResult {
  checked: number;
  repaired: number;
  deleted: number;
  details: Array<{
    oldKeyId: string;
    newKeyId?: string;
    action: 'repaired' | 'deleted';
  }>;
}

/**
 * Repair orphaned bindings where the openhandsKeyId no longer exists.
 * - If a backup key was activated for the old key, update binding to use new key
 * - If no replacement found, delete the orphaned binding
 */
export async function repairBindings(): Promise<RepairResult> {
  const bindings = await listBindings();
  const keys = await listKeys();
  const backupKeys = await listBackupKeys();

  const keyIds = new Set(keys.map(k => k._id));
  const result: RepairResult = {
    checked: bindings.length,
    repaired: 0,
    deleted: 0,
    details: [],
  };

  for (const binding of bindings) {
    // Check if binding's key exists
    if (keyIds.has(binding.openhandsKeyId)) {
      continue; // Key exists, binding is valid
    }

    // Key doesn't exist - find if there's a backup key that replaced it
    const replacementKey = backupKeys.find(
      bk => bk.usedFor === binding.openhandsKeyId && bk.activated && bk.isUsed
    );

    if (replacementKey) {
      // Update binding to use the new key
      await getCollection('openhands_bindings').updateOne(
        { proxyId: binding.proxyId, openhandsKeyId: binding.openhandsKeyId },
        { $set: { openhandsKeyId: replacementKey._id } }
      );
      result.repaired++;
      result.details.push({
        oldKeyId: binding.openhandsKeyId,
        newKeyId: replacementKey._id,
        action: 'repaired',
      });
    } else {
      // No replacement found - delete orphaned binding
      await getCollection('openhands_bindings').deleteOne({
        proxyId: binding.proxyId,
        openhandsKeyId: binding.openhandsKeyId,
      });
      result.deleted++;
      result.details.push({
        oldKeyId: binding.openhandsKeyId,
        action: 'deleted',
      });
    }
  }

  return result;
}
