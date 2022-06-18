import fetch from "node-fetch";
import { FungibleToken } from "../../types";
import { chunk } from "lodash";
import Web3 from "web3";

const checkFields = [
  {
    key: "decimals",
    code: "0x313ce567",
    type: "uint8",
  },
  {
    key: "symbol",
    code: "0x95d89b41",
    type: "string",
  },
  {
    key: "name",
    code: "0x06fdde03",
    type: "string",
  },
];
const web3 = new Web3();

export async function getEVMTokenInfosFromRPC(
  url: string,
  tokens: FungibleToken[],
  pageSize = 100
): Promise<FungibleToken[]> {
  const chunks = chunk(tokens, pageSize);
  const map = new Map<string, FungibleToken>();

  for (const { code, type, key } of checkFields) {
    for (const x of chunks) {
      const body = x.map((token) => ({
        jsonrpc: "2.0",
        method: "eth_call",
        id: 1,
        params: [{ to: token.address, data: code }, "latest"],
      }));

      try {
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(body),
        });

        if (!response.ok || response.status !== 200) {
          console.error(
            `Failed to fetch ${url}, ${code}, ${type}, ${key}, ${JSON.stringify(
              body
            )}`
          );
          continue;
        }

        const results = await response.json();

        if (!Array.isArray(results)) {
          console.error(
            `Incorrect response type from ${url} : ${JSON.stringify(results)}`
          );
          continue;
        }

        x.forEach((token, index) => {
          const result = results[index];
          if (!result.result) return;

          try {
            const decodeResult = web3.eth.abi.decodeParameter(
              type,
              result.result
            );

            if (!decodeResult) return;

            const cache = map.get(`${token.address}_${token.chainId}`);

            map.set(`${token.address}_${token.chainId}`, {
              ...(cache ?? token),
              [key]: decodeResult,
            });
          } catch {
            // Results that cannot be decoded will be filtered
          }
        });
      } catch {
        console.error("Fetch error with: ", url);
        // fetch failed
        x.map((token) => {
          map.set(`${token.address}_${token.chainId}`, token);
        });
      }
    }
  }

  return [...map.values()];
}
