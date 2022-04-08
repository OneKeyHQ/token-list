# onekey-token-list

@onekeyfe@onekey-token-list

 Onekey Token List is a package that contains tokens of multi chains. The JSON schema for the tokens includes: chainId, address, name, decimals, symbol, logoURI (optional), and custom extensions metadata.

## Usage

```bash
npm install @onekeyfe/onekey-token-list
```
or

```bash
yarn add @onekeyfe/onekey-token-list
```

or 

CDN TODO

## Build

Should install python3 environment for your machine before build  
[Download Python](https://www.python.org/downloads/)

```bash
git clone https://github.com/OneKeyHQ/onekey-token-list.git
cd onekey-token-list
pip install requests
python3 ./script/build_list.py
python3 ./script/check_fix.py
```

## Commit PR

In addition to obtaining third-party token lists, we also maintain our own token lists. You are welcome to submit PRs to add your tokens to our list.

### How to add token
There is a chain code as the folder name under the `tokens` folder in the project. The `chain.json` in the folder records the chain information, and the `tokens.json` contains the tokens. The content format of the tokens.json is as follows:
```json
[
    {
      "address": "0xadbd1231fb360047525bedf962581f3eee7b49fe",
      "decimals": 18
      "logoURI": "https://assets.coingecko.com/coins/images/21098/large/logox200.png?1638324977",
      "name": "CronaSwap Token",
      "symbol": "CRONA"
    }
]
```
Please follow this format to append the token information to the `tokens.json` in the target chain folder, For example, add the above token to the `tokens/cronos/tokens.json` file

除了获取第三方的token list, 我们也自己维护了token列表，欢迎你提交PR把你的token加入到我们的列表中。

添加token方法：在项目中的tokens文件夹下有链码作为文件夹名，文件夹内`chain.json`记录chain信息，`tokens.json`收录token，tokens.json内容格式如下：
```json
[
    {
      "address": "0xadbd1231fb360047525bedf962581f3eee7b49fe",
      "decimals": 18
      "logoURI": "https://assets.coingecko.com/coins/images/21098/large/logox200.png?1638324977",
      "name": "CronaSwap Token",
      "symbol": "CRONA"
    }
]
```
请按照此格式把token信息追加到目标chain文件夹的tokens.json中,比如把上述token添加到`tokens/cronos/tokens.json`文件中