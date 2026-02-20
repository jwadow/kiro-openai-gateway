import { Proxy, ProxyKeyBinding, ProxyHealthLog } from '../db/mongodb.js';

export interface CreateProxyInput {
  name: string;
  type: 'http' | 'socks5';
  host: string;
  port: number;
  username?: string;
  password?: string;
}

export interface UpdateProxyInput {
  name?: string;
  host?: string;
  port?: number;
  username?: string;
  password?: string;
  isActive?: boolean;
}

let proxyCounter = 0;

export async function createProxy(input: CreateProxyInput) {
  // Generate unique ID
  const count = await Proxy.countDocuments();
  proxyCounter = Math.max(proxyCounter, count);
  const proxyId = `proxy-${++proxyCounter}`;

  const proxy = new Proxy({
    _id: proxyId,
    name: input.name,
    type: input.type,
    host: input.host,
    port: input.port,
    username: input.username,
    password: input.password,
    status: 'unknown',
  });

  await proxy.save();
  return sanitizeProxy(proxy.toJSON());
}

export async function listProxies() {
  const proxies = await Proxy.find().sort({ createdAt: -1 });
  return proxies.map(p => sanitizeProxy(p.toJSON()));
}

export async function getProxy(proxyId: string) {
  const proxy = await Proxy.findById(proxyId);
  return proxy ? sanitizeProxy(proxy.toJSON()) : null;
}

export async function updateProxy(proxyId: string, input: UpdateProxyInput) {
  const updateData: Record<string, unknown> = {};
  
  if (input.name !== undefined) updateData.name = input.name;
  if (input.host !== undefined) updateData.host = input.host;
  if (input.port !== undefined) updateData.port = input.port;
  if (input.username !== undefined) updateData.username = input.username;
  if (input.password !== undefined) updateData.password = input.password;
  if (input.isActive !== undefined) updateData.isActive = input.isActive;

  const proxy = await Proxy.findByIdAndUpdate(
    proxyId,
    { $set: updateData },
    { new: true }
  );

  return proxy ? sanitizeProxy(proxy.toJSON()) : null;
}

export async function deleteProxy(proxyId: string) {
  // Delete all bindings first
  await ProxyKeyBinding.deleteMany({ proxyId });
  
  const result = await Proxy.findByIdAndDelete(proxyId);
  return result !== null;
}

// Binding type for deprecated factory key bindings
interface BindingResult {
  id: string;
  proxyId: string;
  factoryKeyId: string;
  priority: number;
  isActive: boolean;
  createdAt: Date;
}

// Key Bindings - deprecated (factory keys removed)
export async function getProxyBindings(_proxyId: string): Promise<BindingResult[]> {
  return [];
}

export async function bindKeyToProxy(_proxyId: string, _factoryKeyId: string, _priority: number): Promise<BindingResult> {
  throw new Error('Factory keys have been removed');
}

export async function updateBindingPriority(_proxyId: string, _factoryKeyId: string, _priority: number): Promise<BindingResult | null> {
  return null;
}

export async function updateBinding(_proxyId: string, _factoryKeyId: string, _updates: { priority?: number; isActive?: boolean }): Promise<BindingResult | null> {
  return null;
}

export async function getAllBindings(): Promise<Array<BindingResult & { proxyName: string; factoryKeyStatus: string }>> {
  return [];
}

export async function unbindKeyFromProxy(_proxyId: string, _factoryKeyId: string): Promise<boolean> {
  return false;
}

// Health logs
export async function getProxyHealthLogs(proxyId: string, limit = 100) {
  const logs = await ProxyHealthLog.find({ proxyId })
    .sort({ checkedAt: -1 })
    .limit(limit);
  return logs;
}

// Stats
export async function getProxyStats() {
  const total = await Proxy.countDocuments();
  const healthy = await Proxy.countDocuments({ status: 'healthy', isActive: true });
  const unhealthy = await Proxy.countDocuments({ status: 'unhealthy', isActive: true });
  const unknown = await Proxy.countDocuments({ status: 'unknown', isActive: true });
  const inactive = await Proxy.countDocuments({ isActive: false });

  return { total, healthy, unhealthy, unknown, inactive };
}

// Helper to sanitize proxy (hide password)
function sanitizeProxy(proxy: Record<string, unknown>) {
  const { password, ...rest } = proxy;
  return {
    ...rest,
    hasAuth: !!password,
  };
}
