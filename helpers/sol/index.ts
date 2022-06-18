import fetch from "node-fetch";
import { chunk, compact, flatten, get } from "lodash";
import { FungibleToken } from "../../types";

export async function getSolTokenInfosFromRPC(
  url: string,
  tokens: FungibleToken[],
  pageSize = 100
): Promise<FungibleToken[]> {
  // Avoid oversize requests
  const chunks = chunk(tokens, pageSize);

  const verifiedTokens = await Promise.all(
    chunks.map(async (x) => {
      const body = x.map((token) => ({
        jsonrpc: "2.0",
        method: "getAccountInfo",
        id: 1,
        params: [token.address, { encoding: "jsonParsed" }],
      }));

      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      if (!response.ok || response.status !== 200) {
        console.error(`Failed to fetch ${url}, body: ${JSON.stringify(body)}`);
        return [];
      }

      const results = await response.json();

      if (!Array.isArray(results)) {
        console.error(
          `Incorrect response type from ${url} : ${JSON.stringify(results)}`
        );
        return [];
      }

      return compact(
        results.map((value, index) => {
          const token = x[index];
          if (!token) return;

          const decimals = get(
            value,
            "result.value.data.parsed.info.decimals"
          ) as number | undefined;

          if (!decimals) return;

          return {
            ...token,
            decimals,
          };
        })
      );
    })
  );

  return flatten(verifiedTokens);
}
