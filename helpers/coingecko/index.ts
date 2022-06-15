import urlcat from "urlcat";
import fetch from "node-fetch";
import { chunk } from "lodash";
import { CoingeckoCoin, FungibleToken } from "../../types";

let allCoinsCache: CoingeckoCoin[] = [];

const COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3";

function sleep(ms: number) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

export async function getCoinListWithPlatform(
  platform: string
): Promise<(CoingeckoCoin & { address?: string })[]> {
  if (allCoinsCache.length) {
    return allCoinsCache
      .filter((x) => !!x.platforms?.[platform])
      .map((x) => ({ ...x, address: x.platforms?.[platform] }));
  } else {
    const response = await fetch(
      urlcat(`${COINGECKO_BASE_URL}/coins/list`, { include_platform: true })
    );

    if (!response.ok || response.status !== 200) return [];

    const result = (await response.json()) as CoingeckoCoin[];

    allCoinsCache = result;

    return result
      .filter((x) => !!x.platforms?.[platform])
      .map((x) => ({ ...x, address: x.platforms?.[platform] }));
  }
}

export async function getMarketCoinData(ids: string[]) {
  const chunks = chunk(ids, 250).map((x) => x.join(","));
  const results = new Map<string, string>();

  for (const chunk of chunks) {
    const response = await fetch(
      urlcat(`${COINGECKO_BASE_URL}/coins/markets`, {
        vs_currency: "usd",
        ids: chunk,
      })
    );
    if (response.ok && response.status === 200) {
      const result = (await response.json()) as { image: string; id: string }[];

      result.forEach((x) => results.set(x.id, x.image));
    }
    await sleep(1000);
  }
  return results;
}

export async function getCoinFromCoinGecko(
  chainId: string,
  platform?: string
): Promise<FungibleToken[]> {
  if (!platform) return [];
  const coins = await getCoinListWithPlatform(platform);
  const coinsData = await getMarketCoinData(coins.map((x) => x.id));

  return coins
    .filter((x) => !!x.address)
    .map((x) => {
      const logoURI = coinsData.get(x.id);

      return {
        address: x.address!,
        chainId: chainId,
        name: x.name,
        symbol: x.symbol,
        logoURI,
        source: ["coingecko"],
      };
    });
}
