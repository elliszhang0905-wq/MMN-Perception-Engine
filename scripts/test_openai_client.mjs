import { askOpenAI } from "../openaiClient.mjs";

try {
  const answer = await askOpenAI("请只回复：MMN OpenAI API OK");
  console.log("OpenAI 调用成功：");
  console.log(answer);
} catch (error) {
  console.error("OpenAI 调用失败：");
  console.error(error?.message || error);
  process.exitCode = 1;
}
