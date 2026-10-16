// Line framing shared by the BFF (Agent Runtime's NDJSON stream) and the browser
// (the BFF's SSE stream).

/** Splits a byte stream into lines; feed chunks, then flush. */
export class LineSplitter {
  private buffer = "";
  private decoder = new TextDecoder();

  push(chunk: Uint8Array): string[] {
    this.buffer += this.decoder.decode(chunk, { stream: true });
    const lines = this.buffer.split(/\r?\n/);
    this.buffer = lines.pop() ?? "";
    return lines.map(clean).filter((l) => l !== "");
  }

  flush(): string[] {
    const rest = clean(this.buffer + this.decoder.decode());
    this.buffer = "";
    return rest ? [rest] : [];
  }
}

function clean(line: string): string {
  const t = line.trim();
  if (t.startsWith(":")) return ""; // SSE comment / keepalive
  return t.startsWith("data:") ? t.slice(5).trim() : t;
}
