// Server config from the environment (docs/GCP.md §4 "Web → Cloud Run").
// Nothing here reaches the browser.

export interface Config {
  project: string;
  agentLocation: string;
  agentRuntimeId: string;
  mcpUrl: string;
  accessCode: string;
  userDailyQuota: number;
  globalDailyCap: number;
  quotaBackend: "firestore" | "memory";
  firestoreDatabase: string;
  secureCookies: boolean;
}

function int(name: string, fallback: number): number {
  const raw = process.env[name];
  if (!raw) return fallback;
  const n = Number.parseInt(raw, 10);
  if (!Number.isFinite(n) || n < 0) throw new Error(`${name} must be a non-negative integer`);
  return n;
}

let cached: Config | null = null;

export function config(): Config {
  if (cached) return cached;
  const env = process.env;
  const accessCode = env.ACCESS_CODE ?? "";
  if (accessCode.length < 8) throw new Error("ACCESS_CODE must be set (8+ characters)");
  cached = {
    project: env.GOOGLE_CLOUD_PROJECT ?? "",
    agentLocation: env.AGENT_LOCATION || "europe-west6",
    agentRuntimeId: env.AGENT_RUNTIME_ID ?? "",
    mcpUrl: env.SWISS_LAW_MCP_URL || "http://127.0.0.1:8080/mcp",
    accessCode,
    userDailyQuota: int("USER_DAILY_QUOTA", 10),
    globalDailyCap: int("GLOBAL_DAILY_CAP", 30),
    quotaBackend: env.QUOTA_BACKEND === "memory" ? "memory" : "firestore",
    firestoreDatabase: env.FIRESTORE_DATABASE || "swiss-nav",
    secureCookies: env.NODE_ENV === "production" && env.INSECURE_COOKIES !== "1",
  };
  return cached;
}
