import { readdirSync, readFileSync } from "fs";
import { join } from "path";

function check() {
  for (const dir of readdirSync(join(__dirname, "/tokens"))) {
    const path = join(__dirname, `/tokens/${dir}/tokens.json`);
    const rawToken = readFileSync(path, "utf-8");

    const localTokens = JSON.parse(rawToken);

    if (!Array.isArray(localTokens))
      throw new Error("tokens.json must be an array.");

    for (const record of localTokens) {
      if (
        typeof record.symbol !== "string" ||
        typeof record.decimals !== "number" ||
        typeof record.name !== "string" ||
        new RegExp("^[ \\w.'+\\-%/À-ÖØ-öø-ÿ]+$").test(record.name)
      )
        throw new Error(
          `The format of the token does not match the schema, Pleas check it in ${path}`
        );
    }
  }
}

check();
