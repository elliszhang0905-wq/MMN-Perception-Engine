import OpenAI from "openai";
import dotenv from "dotenv";

dotenv.config();

const DEFAULT_MODEL = "gpt-5.5";

export class OpenAIConfigurationError extends Error {
  constructor(message) {
    super(message);
    this.name = "OpenAIConfigurationError";
  }
}

export class OpenAIRequestError extends Error {
  constructor(message) {
    super(message);
    this.name = "OpenAIRequestError";
  }
}

export class OpenAIEmptyResponseError extends Error {
  constructor(message) {
    super(message);
    this.name = "OpenAIEmptyResponseError";
  }
}

export async function askOpenAI(input) {
  if (!process.env.OPENAI_API_KEY) {
    throw new OpenAIConfigurationError("缺少 OPENAI_API_KEY，请在项目 .env 中配置。");
  }
  if (typeof input !== "string" || !input.trim()) {
    throw new OpenAIRequestError("askOpenAI(input) 需要传入非空文本。");
  }

  const client = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
    baseURL: process.env.OPENAI_BASE_URL || undefined,
    timeout: 90_000,
    maxRetries: 1
  });

  try {
    const response = await client.responses.create({
      model: process.env.OPENAI_MODEL || DEFAULT_MODEL,
      input
    });
    const text = (response.output_text || "").trim();
    if (!text) {
      throw new OpenAIEmptyResponseError("OpenAI 模型无响应。");
    }
    return text;
  } catch (error) {
    if (error instanceof OpenAIEmptyResponseError) {
      throw error;
    }
    const status = error?.status ? `HTTP ${error.status}` : "请求失败";
    const message = error?.message || "OpenAI 请求失败。";
    throw new OpenAIRequestError(`${status}：${message}`);
  }
}
