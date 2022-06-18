import { readFileSync, readdirSync } from "fs";
import { mkdir, writeFile } from "fs/promises";
import { join } from "path";
import { Chain, FungibleToken } from "./types";
import { uniqWith, isEqual, head } from "lodash";
import { getOriginalTokens, getVerifiedTokenFromRPC } from "./helpers";
import { getCoinFromCoinGecko } from "./helpers/coingecko";

async function main() {
  const results = new Map<string, FungibleToken[]>();
  for (const dir of readdirSync(join(__dirname, "/tokens"))) {
    const raw_chain = readFileSync(
      join(__dirname, `/tokens/${dir}/chain.json`),
      "utf-8"
    );

    const raw_token = readFileSync(
      join(__dirname, `/tokens/${dir}/tokens.json`),
      "utf-8"
    );

    const chain = JSON.parse(raw_chain) as Chain;
    const localTokens = JSON.parse(raw_token) as FungibleToken[];

    const coinGeckoTokens = await getCoinFromCoinGecko(
      chain.chainId,
      chain.coingecko?.platform
    );

    const originalTokens = await getOriginalTokens(chain.token_source, [
      coinGeckoTokens,
    ]);

    // check token from rpc
    const verifiedTokens = await getVerifiedTokenFromRPC(
      chain,
      [...originalTokens, ...localTokens],
      head(chain.rpcURLs)?.url
    );

    const platformTokens = results.get(chain.impl);
    const tokens = uniqWith(
      [...(platformTokens ?? []), ...verifiedTokens],
      (a, b) => isEqual(a.address, b.address)
    );

    results.set(chain.impl, tokens);
  }

  for (const [key, value] of results.entries()) {
    const pathToFolder = join(__dirname, `/dist/`);
    await mkdir(pathToFolder, { recursive: true });

    await writeFile(`${pathToFolder}/${key}.json`, JSON.stringify(value));
  }
}

main();
