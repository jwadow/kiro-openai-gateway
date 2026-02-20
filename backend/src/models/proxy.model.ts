import mongoose from 'mongoose';

export interface IProxy {
  _id: string;
  name: string;
  type: 'http' | 'socks5';
  host: string;
  port: number;
  username?: string;
  password?: string;
  status: 'healthy' | 'unhealthy' | 'unknown';
  lastLatencyMs?: number;
  lastCheckedAt?: Date;
  lastError?: string;
  failCount: number;
  isActive: boolean;
  createdAt: Date;
}

export interface IProxyKeyBinding {
  _id?: mongoose.Types.ObjectId;
  proxyId: string;
  factoryKeyId: string;
  priority: 1 | 2;
  isActive: boolean;
  createdAt: Date;
}

export interface IProxyHealthLog {
  _id?: mongoose.Types.ObjectId;
  proxyId: string;
  status: 'healthy' | 'unhealthy' | 'timeout' | 'error';
  latencyMs?: number;
  errorMessage?: string;
  checkedAt: Date;
}

const proxySchema = new mongoose.Schema({
  _id: { type: String, required: true },
  name: { type: String, required: true },
  type: { type: String, enum: ['http', 'socks5'], required: true },
  host: { type: String, required: true },
  port: { type: Number, required: true },
  username: { type: String },
  password: { type: String },
  status: { type: String, enum: ['healthy', 'unhealthy', 'unknown'], default: 'unknown' },
  lastLatencyMs: { type: Number },
  lastCheckedAt: { type: Date },
  lastError: { type: String },
  failCount: { type: Number, default: 0 },
  isActive: { type: Boolean, default: true },
  createdAt: { type: Date, default: Date.now },
});

const proxyKeyBindingSchema = new mongoose.Schema({
  proxyId: { type: String, required: true, ref: 'Proxy' },
  factoryKeyId: { type: String, required: true, ref: 'FactoryKey' },
  priority: { type: Number, enum: [1, 2], default: 1 },
  isActive: { type: Boolean, default: true },
  createdAt: { type: Date, default: Date.now },
});
proxyKeyBindingSchema.index({ proxyId: 1, factoryKeyId: 1 }, { unique: true });
proxyKeyBindingSchema.index({ proxyId: 1, priority: 1 });

const proxyHealthLogSchema = new mongoose.Schema({
  proxyId: { type: String, required: true },
  status: { type: String, enum: ['healthy', 'unhealthy', 'timeout', 'error'], required: true },
  latencyMs: { type: Number },
  errorMessage: { type: String },
  checkedAt: { type: Date, default: Date.now, expires: 604800 },
});
proxyHealthLogSchema.index({ proxyId: 1, checkedAt: -1 });

export const Proxy = mongoose.model<IProxy>('Proxy', proxySchema, 'proxies');
export const ProxyKeyBinding = mongoose.model<IProxyKeyBinding>('ProxyKeyBinding', proxyKeyBindingSchema, 'proxy_key_bindings');
export const ProxyHealthLog = mongoose.model<IProxyHealthLog>('ProxyHealthLog', proxyHealthLogSchema, 'proxy_health_logs');
