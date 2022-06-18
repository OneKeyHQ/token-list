const packageJson = require("../package.json");
const schema = require("@uniswap/token-lists/src/tokenlist.schema.json");
// Allow '|' in name.
schema.definitions.TokenInfo.properties.symbol = {
  type: "string",
  minLength: 1,
};
schema.definitions.TokenInfo.properties.name = { type: "string", minLength: 1 };
// schema.definitions.TokenInfo.properties.name.pattern = "^[ \\|\\w.'+\\-%/À-ÖØ-öø-ÿ:&\\[\\]\\(\\)]+$"
schema.definitions.TokenInfo.properties.chainId = {
  type: "string",
  minLength: 1,
}; // CHANGE TYPE BECAUSE OF COSMOS
const { expect } = require("chai");
const Ajv = require("ajv");
const { evmOnekeyTokenList } = require("../build/index");

const ajv = new Ajv({ allErrors: true, format: "full" });
const validator = ajv.compile(schema);

describe("buildEVMList", () => {
  const defaultTokenList = evmOnekeyTokenList;

  it("validates", () => {
    expect(validator(defaultTokenList)).to.equal(true);
  });

  it("contains no duplicate addresses", () => {
    const map = {};
    for (let token of defaultTokenList.tokens) {
      const key = `${token.chainId}-${token.address}`;
      expect(typeof map[key]).to.equal("undefined");
      map[key] = true;
    }
  });
  it("version matches package.json", () => {
    expect(packageJson.version).to.match(/^\d+\.\d+\.\d+$/);
    expect(packageJson.version).to.equal(
      `${defaultTokenList.version.major}.${defaultTokenList.version.minor}.${defaultTokenList.version.patch}`
    );
  });
});
