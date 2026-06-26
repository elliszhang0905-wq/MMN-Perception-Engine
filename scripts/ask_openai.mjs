import { askOpenAI } from "../openaiClient.mjs";

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf-8");
}

try {
  const raw = await readStdin();
  const payload = JSON.parse(raw || "{}");
  const text = await askOpenAI(payload.input || "");
  process.stdout.write(JSON.stringify({ ok: true, text }));
} catch (error) {
  process.stdout.write(JSON.stringify({
    ok: false,
    error: error?.message || "OpenAI 请求失败。"
  }));
  process.exitCode = 1;
}
