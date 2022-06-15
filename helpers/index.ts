import { FungibleToken, TokenSource } from "../types";
import fetch from "node-fetch";
import { get } from "lodash";

export async function getOriginalTokens(
  token_source?: TokenSource[],
  merged?: FungibleToken[]
) {
  const map = new Map<string, FungibleToken>();

  if (token_source) {
    await Promise.all(
      token_source.map(async ({ source, url, path }) => {
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
                  source: [source],
                }
          );
        });
      })
    );
  }

  merged?.forEach((x) => {
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
  });

  return [...map.values()];
}
