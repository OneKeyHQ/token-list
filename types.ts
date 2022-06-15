export interface TokenSource {
  source: string;
  url: string;
  path: string;
}
export interface Chain {
  id: string;
  impl: string;
  chainId: string;
  name: string;
  rpcURLs: { url: string }[];
  coingecko?: {
    platform?: string;
    category_id?: string;
  };
  token_source?: TokenSource[];
}

export interface CoingeckoCoin {
  id: string;
  symbol: string;
  name: string;
  platforms?: Record<string, string>;
}

export interface FungibleToken {
  chainId: string;
  address: string;
  name: string;
  symbol: string;
  decimals?: number;
  logoURI?: string;
  source?: string[];
}
