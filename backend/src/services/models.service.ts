import * as fs from 'fs';
import * as path from 'path';

export interface ModelConfig {
  name: string;
  id: string;
  type: string;
  reasoning?: string;
  thinking_budget?: number;
  input_price_per_mtok: number;
  output_price_per_mtok: number;
  cache_write_price_per_mtok?: number;
  cache_hit_price_per_mtok?: number;
  billing_multiplier?: number;
  upstream?: string;
  upstream_model_id?: string;
}

interface GoproxyConfig {
  models: ModelConfig[];
  endpoints: { name: string; base_url: string }[];
}

let cachedConfig: GoproxyConfig | null = null;
let lastConfigLoad = 0;
const CONFIG_CACHE_TTL = 60000; // 1 minute

function loadGoproxyConfig(): GoproxyConfig | null {
  const now = Date.now();
  if (cachedConfig && now - lastConfigLoad < CONFIG_CACHE_TTL) {
    return cachedConfig;
  }

  // Try multiple possible paths for goproxy config
  const possiblePaths = [
    // Environment variable path (highest priority)
    process.env.GOPROXY_CONFIG_PATH,
    // Production paths
    '/app/goproxy/config.json',
    '/app/goproxy/config.prod.json',
    // Development paths
    path.resolve(__dirname, '../../../goproxy/config.json'),
    path.resolve(__dirname, '../../goproxy/config.json'),
    path.resolve(process.cwd(), '../goproxy/config.json'),
    path.resolve(process.cwd(), 'goproxy/config.json'),
  ].filter(Boolean) as string[];

  for (const configPath of possiblePaths) {
    try {
      if (fs.existsSync(configPath)) {
        const data = fs.readFileSync(configPath, 'utf-8');
        cachedConfig = JSON.parse(data);
        lastConfigLoad = now;
        console.log(`Loaded goproxy config from: ${configPath}`);
        return cachedConfig;
      }
    } catch (err) {
      console.error(`Failed to load config from ${configPath}:`, err);
    }
  }

  console.warn('Could not find goproxy config.json');
  return null;
}

export function getModels(): ModelConfig[] {
  const config = loadGoproxyConfig();
  return config?.models || [];
}
