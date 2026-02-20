import mongoose from 'mongoose';

export interface OhMyGPTKey {
  _id: string;
  apiKey: string;
  status: string;
  tokensUsed: number;
  requestsCount: number;
  lastError?: string;
  cooldownUntil?: Date;
  createdAt: Date;
  updatedAt?: Date;
}

export interface OhMyGPTBackupKey {
  _id: string;
  apiKey: string;
  isUsed: boolean;
  activated: boolean;
  usedFor?: string;
  usedAt?: Date;
  createdAt: Date;
}

function getCollection(name: string) {
  return mongoose.connection.db!.collection(name);
}

// ============ KEYS ============

export async function listKeys(): Promise<OhMyGPTKey[]> {
  const result = await getCollection('ohmygpt_keys').find({}).toArray();
  return result as any;
}

export async function getKey(id: string): Promise<OhMyGPTKey | null> {
  const result = await getCollection('ohmygpt_keys').findOne({ _id: id as any });
  return result as any;
}

export async function createKey(data: { id: string; apiKey: string }): Promise<OhMyGPTKey> {
  const key = {
    _id: data.id,
    apiKey: data.apiKey,
    status: 'healthy',
    tokensUsed: 0,
    requestsCount: 0,
    createdAt: new Date(),
  };
  await getCollection('ohmygpt_keys').insertOne(key as any);
  return key as any;
}

export async function updateKey(id: string, data: Partial<OhMyGPTKey>): Promise<OhMyGPTKey | null> {
  const result = await getCollection('ohmygpt_keys').findOneAndUpdate(
    { _id: id as any },
    { $set: { ...data, updatedAt: new Date() } },
    { returnDocument: 'after' }
  );
  return result as any;
}

export async function deleteKey(id: string): Promise<boolean> {
  await getCollection('ohmygpt_bindings').deleteMany({ ohmygptKeyId: id });
  const result = await getCollection('ohmygpt_keys').deleteOne({ _id: id as any });
  return result.deletedCount > 0;
}

export async function resetKeyStats(id: string): Promise<OhMyGPTKey | null> {
  const result = await getCollection('ohmygpt_keys').findOneAndUpdate(
    { _id: id as any },
    { $set: { status: 'healthy', tokensUsed: 0, requestsCount: 0, lastError: null, cooldownUntil: null } },
    { returnDocument: 'after' }
  );
  return result as any;
}

export async function getStats() {
  const [keys, healthyKeys] = await Promise.all([
    getCollection('ohmygpt_keys').countDocuments(),
    getCollection('ohmygpt_keys').countDocuments({ status: 'healthy' }),
  ]);

  return { totalKeys: keys, healthyKeys };
}

// ============ BACKUP KEYS ============

export async function listBackupKeys(): Promise<OhMyGPTBackupKey[]> {
  const result = await getCollection('ohmygpt_backup_keys').find({}).sort({ createdAt: -1 }).toArray();
  return result as any;
}

export async function getBackupKeyStats() {
  const [total, available, used] = await Promise.all([
    getCollection('ohmygpt_backup_keys').countDocuments(),
    getCollection('ohmygpt_backup_keys').countDocuments({ isUsed: false }),
    getCollection('ohmygpt_backup_keys').countDocuments({ isUsed: true }),
  ]);
  return { total, available, used };
}

export async function createBackupKey(data: { id: string; apiKey: string }): Promise<OhMyGPTBackupKey> {
  const key = {
    _id: data.id,
    apiKey: data.apiKey,
    isUsed: false,
    activated: false,
    createdAt: new Date(),
  };
  await getCollection('ohmygpt_backup_keys').insertOne(key as any);
  return key as any;
}

export async function deleteBackupKey(id: string): Promise<boolean> {
  const result = await getCollection('ohmygpt_backup_keys').deleteOne({ _id: id as any });
  return result.deletedCount > 0;
}

export async function restoreBackupKey(id: string): Promise<boolean> {
  const result = await getCollection('ohmygpt_backup_keys').updateOne(
    { _id: id as any },
    { $set: { isUsed: false, activated: false, usedFor: null, usedAt: null } }
  );
  return result.modifiedCount > 0;
}

// ============ BINDINGS ============

export interface OhMyGPTKeyBinding {
  _id?: any;
  proxyId: string;
  ohmygptKeyId: string;
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

export async function listBindings(): Promise<OhMyGPTKeyBinding[]> {
  const result = await getCollection('ohmygpt_bindings').find({}).sort({ proxyId: 1, priority: 1 }).toArray();
  return result as any;
}

export async function getBindingsForProxy(proxyId: string): Promise<OhMyGPTKeyBinding[]> {
  const result = await getCollection('ohmygpt_bindings').find({ proxyId }).sort({ priority: 1 }).toArray();
  return result as any;
}

export async function createBinding(data: { proxyId: string; ohmygptKeyId: string; priority: number }): Promise<OhMyGPTKeyBinding> {
  const binding = {
    proxyId: data.proxyId,
    ohmygptKeyId: data.ohmygptKeyId,
    priority: data.priority,
    isActive: true,
    createdAt: new Date(),
  };
  const result = await getCollection('ohmygpt_bindings').insertOne(binding);
  return { ...binding, _id: result.insertedId } as any;
}

export async function updateBinding(proxyId: string, ohmygptKeyId: string, data: Partial<OhMyGPTKeyBinding>): Promise<OhMyGPTKeyBinding | null> {
  const result = await getCollection('ohmygpt_bindings').findOneAndUpdate(
    { proxyId, ohmygptKeyId },
    { $set: data },
    { returnDocument: 'after' }
  );
  return result as any;
}

export async function deleteBinding(proxyId: string, ohmygptKeyId: string): Promise<boolean> {
  const result = await getCollection('ohmygpt_bindings').deleteOne({ proxyId, ohmygptKeyId });
  return result.deletedCount > 0;
}

export async function deleteAllBindingsForProxy(proxyId: string): Promise<number> {
  const result = await getCollection('ohmygpt_bindings').deleteMany({ proxyId });
  return result.deletedCount;
}

export async function listProxies(): Promise<Proxy[]> {
  const result = await getCollection('proxies').find({}).toArray();
  return result as any;
}

export async function getBindingsStats() {
  const [bindings, proxies] = await Promise.all([
    getCollection('ohmygpt_bindings').countDocuments({ isActive: true }),
    getCollection('proxies').countDocuments({ isActive: true }),
  ]);

  return { totalBindings: bindings, totalProxies: proxies };
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
 * Repair orphaned bindings where the ohmygptKeyId no longer exists.
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
    if (keyIds.has(binding.ohmygptKeyId)) {
      continue; // Key exists, binding is valid
    }

    // Key doesn't exist - find if there's a backup key that replaced it
    const replacementKey = backupKeys.find(
      bk => bk.usedFor === binding.ohmygptKeyId && bk.activated && bk.isUsed
    );

    if (replacementKey) {
      // Update binding to use the new key
      await getCollection('ohmygpt_bindings').updateOne(
        { proxyId: binding.proxyId, ohmygptKeyId: binding.ohmygptKeyId },
        { $set: { ohmygptKeyId: replacementKey._id } }
      );
      result.repaired++;
      result.details.push({
        oldKeyId: binding.ohmygptKeyId,
        newKeyId: replacementKey._id,
        action: 'repaired',
      });
    } else {
      // No replacement found - delete orphaned binding
      await getCollection('ohmygpt_bindings').deleteOne({
        proxyId: binding.proxyId,
        ohmygptKeyId: binding.ohmygptKeyId,
      });
      result.deleted++;
      result.details.push({
        oldKeyId: binding.ohmygptKeyId,
        action: 'deleted',
      });
    }
  }

  return result;
}
