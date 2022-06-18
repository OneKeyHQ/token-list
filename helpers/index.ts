import { Chain, FungibleToken, TokenSource } from "../types";
import fetch from "node-fetch";
import { get } from "lodash";
import { getSolTokenInfosFromRPC } from "./sol";
import { getEVMTokenInfosFromRPC } from "./evm";

export async function getOriginalTokens(
  tokenSource?: TokenSource[],
  multiOriginalTokenSources?: FungibleToken[][]
) {
  const map = new Map<string, FungibleToken>();

  if (tokenSource) {
    await Promise.all(
      tokenSource.map(async ({ source, url, path }) => {
        const response = await fetch(url);

        if (!response.ok || response.status !== 200) return;

        const body = await response.json();
        const result: FungibleToken[] | undefined = path
          ? get(body, path)
          : body;

        if (!result?.length) return;
        result.forEach((x) => {
          const key = `${x.address.toLowerCase()}_${
            x.chainId
          }_${x.symbol.toLowerCase()}`;
          const cache = map.get(key);

          map.set(
            key,
            cache
              ? {
                  ...cache,
                  source: [...new Set([...(cache.source ?? []), source])],
                }
              : {
                  ...x,
                  chainId: `${x.chainId}`,
                  source: [source],
                }
          );
        });
      })
    );
  }

  // Merge data from other sources
  multiOriginalTokenSources?.forEach((tokens) =>
    tokens.forEach((x) => {
      const key = `${x.address.toLowerCase()}_${
        x.chainId
      }_${x.symbol.toLowerCase()}`;
      const cache = map.get(key);

      map.set(
        key,
        cache
          ? {
              ...x,
              source: [
                ...new Set([...(cache.source ?? []), ...(x.source ?? [])]),
              ],
            }
          : x
      );
    })
  );

  return [...map.values()];
}

// Some rpc nodes have batch limit
const chainPageSizeMapper: Record<string, number> = {
  ["43114"]: 20,
  ["25"]: 3,
};

export async function getVerifiedTokenFromRPC(
  chain: Chain,
  tokens: FungibleToken[],
  url?: string
) {
  if (!url) return tokens;

  switch (chain.impl) {
    case "evm":
      return getEVMTokenInfosFromRPC(
        url,
        tokens,
        chainPageSizeMapper[chain.chainId] ?? 100
      );
    case "sol":
      return getSolTokenInfosFromRPC(url, tokens);
    //TODO: Support other network rpc check
    default:
      return tokens;
  }
}
