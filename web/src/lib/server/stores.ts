// Quota counters and feedback: Firestore in the cloud, process memory for local dev.

import { Firestore } from "@google-cloud/firestore";

import { config } from "@/lib/server/config";
import { FirestoreQuota, MemoryQuota, type QuotaStore } from "@/lib/server/quota";

/**
 * What a thumbs up/down stores. No question or answer text (questions can be
 * personal; the MCP server doesn't log them either). The session id lets an admin
 * look the conversation up in Agent Runtime Sessions while it lives (24 h TTL).
 */
export interface Feedback {
  rating: "up" | "down";
  sessionId: string;
  uid: string;
  language: string | null;
  citations: string[]; // "OR Art. 257e", …
  verification: string | null;
  confidence: string | null;
  at: Date;
}

export interface FeedbackStore {
  add(f: Feedback): Promise<void>;
}

let db: Firestore | null = null;
let quota: QuotaStore | null = null;
let feedback: FeedbackStore | null = null;

function firestore(): Firestore {
  const c = config();
  db ??= new Firestore({ projectId: c.project || undefined, databaseId: c.firestoreDatabase });
  return db;
}

export function quotaStore(): QuotaStore {
  quota ??=
    config().quotaBackend === "memory" ? new MemoryQuota() : new FirestoreQuota(firestore());
  return quota;
}

export function feedbackStore(): FeedbackStore {
  if (feedback) return feedback;
  if (config().quotaBackend === "memory") {
    feedback = {
      async add(f) {
        console.log(JSON.stringify({ msg: "feedback", ...f }));
      },
    };
  } else {
    const col = firestore().collection("feedback");
    feedback = {
      async add(f) {
        await col.add(f);
      },
    };
  }
  return feedback;
}
