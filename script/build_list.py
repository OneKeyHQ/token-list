import os
from pathlib import Path
from re import T
import sys
import json
import time
import yaml
from datetime import datetime
import shutil
import requests


class Coingecko():
    '''coingecko client'''

    base = "https://api.coingecko.com/api/v3"

    coin_cache = {}

    def get_all_coins(self):
        '''get all coins'''
        data = requests.get(
            f'{self.base}/coins/list?include_platform=true').json()

        platform_coins = {}
        id_coins = {}
        for coin in data:
            id_coins[coin["id"]] = coin
            platforms = coin.get("platforms", {})
            for p, addr in platforms.items():
                tokens = platform_coins.get(p, [])
                tokens.append(dict(
                    address=addr,
                    symbol=coin.get("symbol"),
                    name=coin.get("name"),
                    id=coin.get("id"),
                ))
                platform_coins[p] = tokens

        return platform_coins, id_coins

    def get_info_by_ids(self, ids):
        '''get by ids'''

        req_ids = []
        coins = {}
        for id in ids:
            if self.coin_cache.get(id) is not None:
                coins[id] = self.coin_cache[id]
            else:
                req_ids.append(id)

        step = 100
        for i in range(0, len(req_ids), step):
            end = i + step
            data = requests.get(
                f'{self.base}/coins/markets',
                params={"vs_currency": "usd", "ids": ",".join(
                    req_ids[i:end]), "order": "market_cap_desc", "sparkline": "false"}
            ).json()
            for item in data:
                coins[item["id"]] = item
                self.coin_cache[item["id"]] = item
            time.sleep(1.5)

        return coins

    def topk_by_market_cap(self, network, tokens, k):
        # get coingecko platform id
        platform_id = network.get("coingecko", {}).get("platform")
        if platform_id is None:
            return tokens

        value_map = {}
        step = 100
        for i in range(0, len(tokens), step):
            end = i + step
            addresses = [t["address"] for t in tokens[i:end]]
            url = f"https://api.coingecko.com/api/v3/simple/token_price/{platform_id}"
            data = requests.get(
                url,
                params={'contract_addresses': ','.join(
                    addresses), 'include_market_cap': 'true', 'vs_currencies': 'usd'}
            ).json()
            for address in addresses:
                market_cap = data.get(address, {'usd_market_cap': 0}).get(
                    'usd_market_cap', 0)
                if market_cap is not None and market_cap > 0:
                    value_map[address] = market_cap
            print(f"get coingecko for {platform_id} {end}")
            time.sleep(1.5)

        addresses_with_cap = list(value_map.keys())
        addresses_with_cap.sort(key=lambda a: value_map[a], reverse=True)
        topk_with_place = dict((address, idx)
                               for idx, address in enumerate(addresses_with_cap[:k]))
        tokens.sort(key=lambda t: topk_with_place.get(t['address'], k))
        return tokens


class TokenProcesser():
    '''process tokens'''
    coingecko = Coingecko()
    networks = []

    def __init__(self, dir):
        self.dir = dir
        self.networks = self.list_networks(dir)

    def list_networks(self, dir):
        '''find all networks'''
        root = Path(dir)
        dirs = [f for f in root.iterdir() if f.is_dir()]

        networks = []
        for d in dirs:
            d = os.path.basename(d)
            network_file = os.path.join(dir, d, "chain.json")
            try:
                with open(network_file) as f:
                    network = json.load(f)
            except Exception:
                return
            network["code"] = d
            networks.append(network)
        return networks

    def fetch_tokens(self):
        '''fetch all tokens'''
        network_tokens = []
        all_platform_coins, all_coins = self.coingecko.get_all_coins()

        for network in self.networks:
            cg = network.get("coingecko", {})

            coins = []
            if cg.get("platform", "") != "":
                coins = all_platform_coins.get(cg["platform"], [])

            # local list
            tokens_file = f"{self.dir}/{network.get('code')}/tokens.json"
            local_tokens = []
            try:
                with open(tokens_file) as f:
                    local_tokens = json.load(f)
            except Exception:
                local_tokens = []

            for token in local_tokens:
                token["chainId"] = network["chainId"]
                token["extensions"] = dict(source=["onekey"])

            # other source
            third_tokens = self.dump_third_token_list(
                network.get("token_source", []))

            tokens = self.merge_tokens(local_tokens, third_tokens)
            if len(coins) > 0:
                coins_info = self.coingecko.get_info_by_ids(
                    [coin["id"] for coin in coins])

                cg_tokens = []

                for coin in coins:
                    address = all_coins[coin["id"]
                                        ]["platforms"][cg["platform"]]
                    if address is None or address == "":
                        continue
                    token = dict(
                        extensions=dict(source=["coingecko"]),
                        chainId=network["chainId"],
                        symbol=coin.get("symbol"),
                        name=coin.get("name"),
                        address=all_coins[coin["id"]
                                          ]["platforms"][cg["platform"]]
                    )
                    if coins_info[coin["id"]] is not None:
                        token["logoURI"] = coins_info[coin["id"]].get("image")
                    cg_tokens.append(token)

                tokens = self.merge_tokens(cg_tokens, tokens)

            network_tokens.append(dict(
                network=network,
                tokens=self.coingecko.topk_by_market_cap(network, tokens, 100),
            ))
        return network_tokens

    def dump_third_token_list(self, sources):
        ''''''
        all_tokens = []
        for s in sources:
            data = requests.get(s.get("url")).json()
            tokens = []
            if s.get("path", "") == "":
                tokens = data
            for token in tokens:
                t = dict(
                    chainId=token["chainId"],
                    symbol=token["symbol"],
                    name=token["name"],
                    decimals=token["decimals"],
                    extensions=dict(source=[s.get("source")]),
                    address=token["address"],
                )
                if token.get("logoURI", "") != "":
                    t["logoURI"] = token["logoURI"]
                all_tokens.append(t)
        return all_tokens

    def merge_tokens(self, tokens1, tokens2):
        if len(tokens2) == 0:
            return tokens1
        tokens = []
        dup = {}
        for token in tokens1:
            tokens.append(token)
            print(token)
            dup[token["address"].lower()] = token
        for token in tokens2:
            if not token["address"]:  # No address
                continue

            if token["address"].lower() in dup:
                # merge field
                t1 = dup[token["address"].lower()]
                source = t1.get("extensions", {}).get(
                    "source", [])+token.get("extensions", {}).get("source", [])
                source = list(set(source))
                extensions = t1.get("extensions", {})
                extensions["source"] = source
                t1["extensions"] = extensions
                continue

            tokens.append(token)
            dup[token["address"].lower()] = token
        return tokens

    def merge_list_by_impl(self, network_tokens):
        impl_list = {}
        for chain in network_tokens:
            network = chain["network"]
            tokens = chain["tokens"]

            impl = network.get("impl", network.get("code", ""))
            try:
                mem_tokens = impl_list[impl]
            except Exception:
                mem_tokens = []

            for token in tokens:

                mem_tokens.append(token)

            impl_list[impl] = mem_tokens
        return impl_list


def build(version="", impl_list=None):

    dir = "./build"
    try:
        if os.path.exists(dir):
            shutil.rmtree(dir)
        os.mkdir(dir)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))

    if not version:
        try:
            with open("./package.json") as f:
                pkg = json.load(f)
                version = pkg["version"]
        except Exception as e:
            print(e)

    files = []

    files += build_list(impl_list, version, ".all")

    build_index(files)
    with open("./build/version.json", "w") as f:
        f.write(json.dumps({"version": version}, sort_keys=True, indent=4))

    update_version(version)


def build_list(impl_list, version, owner=""):
    parsed = version.split(".")

    files = []
    for impl, tokens in impl_list.items():
        if len(tokens) == 0:
            continue

        list = {
            "name": "OneKey Token List",
            "timestamp": datetime.utcnow().isoformat()[:-3] + "Z",
            "version": {
                "major": int(parsed[0]),
                "minor": int(parsed[1]),
                "patch": int(parsed[2]),
            },
            "tags": {},
            "logoURI": "https://onekey-asset.com/assets/logo.png",
            "keywords": ["onekey", "default"],
            "tokens": tokens,
        }

        with open(f"./build/{impl}{owner}.json", "w") as f:
            f.write(json.dumps(list, sort_keys=True, indent=2))
        files.append(f"{impl}{owner}")
    return files


def update_version(version):
    try:
        with open("./package.json") as f:
            pkg = json.load(f)
        pkg["version"] = version

        with open("./package.json", "w") as f:
            f.write(json.dumps(pkg, indent=2))
            f.write("\n")

    except Exception as e:
        print(e)


def build_index(files):
    requires = ""
    exports = ""
    for impl in files:
        requires += (
            f'const {format_var_name(impl)}TokenList = require("./{impl}.json");\n'
        )
        exports += f"\t{format_var_name(impl)}TokenList,\n"
    with open("./build/index.js", "w") as f:
        f.write(
            f"""{requires}
const version = require("./version.json");

module.exports = {{
    version,
{exports}
}}
    """
        )


def format_var_name(name):
    if "." in name:
        names = name.split(".")
        for i in range(len(names)):
            if i == 0:
                continue
            names[i] = names[i].title()
        return "".join(names)
    return name


if __name__ == "__main__":
    version = None
    if len(sys.argv) > 1:
        version = sys.argv[1]
    p = TokenProcesser("./tokens")

    network_tokens = p.fetch_tokens()
    impl_list = p.merge_list_by_impl(network_tokens)
    build(version=version, impl_list=impl_list)
