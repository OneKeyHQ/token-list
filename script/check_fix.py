import json
import os
from pathlib import Path
import tty
from unicodedata import decimal
import requests
import time

class InvalidContractError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def _extract_eth_call_str(data: bytes) -> str:
    payload_offset = int.from_bytes(data[:32], "big")
    payload = data[payload_offset:]
    str_length = int.from_bytes(payload[:32], "big")
    str_result = payload[32:32 + str_length].decode()
    return str_result


class BaseTokenManager(object):

    def __init__(self, url=None):
        self.url = url

    def normalize_token_id(self, token_id):
        return token_id

    def get_token_info(self, token_id):
        return None, None, None


class EVMTokenManager(BaseTokenManager):

    def normalize_token_id(self, token_id):
        token_id = token_id.lower()
        if not token_id.startswith("0x"):
            token_id = "0x" + token_id
        return token_id

    def get_token_info(self, token_id):
        jsonrpc_data = dict(
            jsonrpc="2.0",
            method="eth_getCode",
            id=1,
            params=[token_id, "latest"]
        )
        resp = requests.post(self.url, json=jsonrpc_data, timeout=30)
            
        result = resp.json()

        if result.get("result") is None:
            print(f"  - {token_id} is not a contract.")
            raise InvalidContractError(f"  - {token_id} is not a contract.")

        jsonrpc_data = list(
            dict(
                jsonrpc="2.0",
                method="eth_call",
                id=id,
                params=[{"to": token_id, "data": call_data}, "latest"]
            )
            for id, call_data in enumerate(
                ["0x06fdde03", "0x95d89b41", "0x313ce567"], start=2
            )
        )
        resp = requests.post(self.url, json=jsonrpc_data, timeout=30)
        resp = sorted(resp.json(), key=lambda i: int(i.get("id", 5)))
        try:
            name = _extract_eth_call_str(bytes.fromhex(resp[0]["result"][2:]))
        except Exception:
            name = None

        try:
            symbol = _extract_eth_call_str(
                bytes.fromhex(resp[1]["result"][2:]))
        except Exception:
            symbol = None

        try:
            decimals = int(resp[2]["result"], base=16)
        except Exception:
            decimals = None

        return name, symbol, decimals


class NearTokenManager(BaseTokenManager):

    def normalize_token_id(self, token_id):
        return token_id

    def get_token_info(self, token_id):
        jsonrpc_data = dict(
            jsonrpc="2.0",
            method="query",
            id=1,
            params={
                "request_type": "view_code",
                "finality": "final",
                "account_id": token_id
            }
        )
        resp = requests.post(self.url, json=jsonrpc_data, timeout=30)
        result = resp.json()["result"]
        if len(result) == 0:
            print(f"  - {token_id} is not a contract.")
            raise InvalidContractError(f"  - {token_id} is not a contract.")

        jsonrpc_data = dict(
            jsonrpc="2.0",
            method="query",
            id=1,
            params={
                "request_type": "call_function",
                "finality": "final",
                "account_id": token_id,
                "method_name": "ft_metadata",
                "args_base64": ""
            }
        )
        resp = requests.post(self.url, json=jsonrpc_data, timeout=30)

        info = bytearray(resp.json()["result"]["result"]).decode("utf-8")
        info = json.loads(info)
        name = info.get("name")
        symbol = info.get("symbol")
        decimals = info.get("decimals")
        return name, symbol, int(decimals)


class SolTokenManager(BaseTokenManager):

    def normalize_token_id(self, token_id):
        return token_id

    def get_token_info(self, token_id):
        jsonrpc_data = dict(
            jsonrpc="2.0",
            method="getAccountInfo",
            id=1,
            params=[token_id, {"encoding": "jsonParsed"}]
        )
        resp = requests.post(self.url, json=jsonrpc_data, timeout=30)
        result = resp.json()
        if result.get("result") is None:
            print(f"  - {token_id} is not a contract.")
            raise InvalidContractError(f"  - {token_id} is not a contract.")
        decimals = None
        try:
            result = result["result"]
            if result["value"]["data"]["parsed"]["type"] == "mint":
                decimals = result["value"]["data"]["parsed"]["info"]["decimals"]
        except Exception:
            return None, None, None

        return None, None, decimals


def load_networks(dir):
    '''find all networks'''
    root = Path(dir)
    dirs = [f for f in root.iterdir() if f.is_dir()]

    networks = {}
    for d in dirs:
        d = os.path.basename(d)
        network_file = os.path.join(dir, d, "chain.json")
        try:
            with open(network_file) as f:
                network = json.load(f)
        except Exception:
            return
        network["code"] = d
        networks[network.get("id")] = network
    return networks


token_managers = {}


def create_token_manager(impl, chain_id, url):
    id = f'{impl}--{chain_id}'

    tm = token_managers.get(id, None)
    if tm is not None:
        return tm

    if impl == "evm":
        tm = EVMTokenManager(url)
    if impl == "near":
        tm = NearTokenManager(url)
    if impl == "sol":
        tm = SolTokenManager(url)
    if tm is not None:
        token_managers[id] = tm
    return tm


def check_token(token, info, id):
    ''''''
    for field in ["name", "symbol"]:
        if info.get(field) is not None and info[field] != "" and info[field] != token[field]:
            print(
                f'check {id} not same at [{field}]: {token[field]} vs {info[field]}')
            token[field] = info[field]
    for field in ["decimals"]:
        if info.get(field) is not None and info[field] != token.get(field):
            print(
                f'check {id} not same at [{field}]: {token.get(field)} vs {info[field]}')
            token[field] = info[field]


def check_tokens(impl, networks, tokens, token_info):
    ''''''
    invalid_token_ids = {}
    for token in tokens:
        token_id = f'{token["chainId"]}--{token["address"]}'
        if token_info.get(token_id, None) is not None:
            check_token(token, token_info[token_id], f'{impl}--{token_id}')
            continue

        id = f'{impl}--{token["chainId"]}'

        network = networks.get(id)
        tm = create_token_manager(
            impl, token['chainId'], network.get("rpcURLs", [{}])[0].get("url"))
        if tm is None:
            continue

        print(impl, token['chainId'], token)
        try:

            name, symbol, decimals = tm.get_token_info(token["address"])
            info = dict(id=f'{impl}--{token_id}', name=name,
                        symbol=symbol, decimals=decimals)
            check_token(token, info, f'{impl}--{token_id}')

            token_info[token_id] = info

            with open('./token_info.json', 'w') as f:
                f.write(json.dumps(token_info, sort_keys=True, indent=2))
                f.write("\n")
        except InvalidContractError:
            invalid_token_ids[token["address"]] = True

        time.sleep(1)
    return invalid_token_ids


def check_files(impl, networks, files):
    ''''''
    token_info = {}
    try:
        with open('./token_info.json', 'r') as f:
            token_info = json.load(f)
    except Exception:
        token_info = {}
    for file in files:
        with open(file, "r") as f:
            data = json.load(f)
        tokens = data.get("tokens", [])

        invalid_token_ids = check_tokens(impl, networks, tokens, token_info)

        tokens = [ t for t in tokens if invalid_token_ids.get(t["address"]) is None ]
        data['tokens'] = tokens
        with open(file, "w") as f:
            f.write(json.dumps(data, sort_keys=True, indent=2))


def check():
    networks = load_networks('./tokens')

    dir = "./build"
    # find json file
    files = [os.path.join(dir, f) for f in os.listdir(
        dir) if os.path.isfile(os.path.join(dir, f)) and ".json" in f]

    impl_files = {}
    for file in files:
        with open(file, "r") as f:
            data = json.load(f)
        tokens = data.get("tokens", [])
        if len(tokens) == 0:
            continue
        impl = os.path.basename(file).split(".")[0]
        if impl_files.get(impl) is None:
            impl_files[impl] = [file]
        else:
            impl_files[impl].append(file)

    for impl, files in impl_files.items():
        check_files(impl, networks, files)


if __name__ == "__main__":
    check()
