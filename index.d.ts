
export type Version = {
  major: number;
  minor: number;
  patch: number;
}

export type TokenList = {
  keywords?: string[];
  logoURI: string;
  name: string;
  tags?: Record<string, string>;
  timestamp: string;
  tokens: Token[];
  version: Version;
};

type Token = {
  address: string;
  chainId: string;
  decimals: number;
  logoURI?: string;
  name: string;
  symbol: string;
  extensions?: Record<string, any>;
};

export const version: {
  version: string;
};

export const evmAllTokenList: TokenList;
export const solAllTokenList: TokenList;
export const algoAllTokenList: TokenList;
export const cosmosAllTokenList: TokenList;
