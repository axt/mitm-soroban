# mitm-soroban

This repository provides a [mitmproxy](https://github.com/mitmproxy/) content view plugin designed to decode XDR properties both in requests and repsonses when interacting with the [soroban-rpc](https://github.com/stellar/soroban-tools/tree/main/cmd/soroban-rpc) server. This enhances the visibility and debugging capabilities of developers working with Soroban and Stellar network transactions.

## Prerequisites
- ensure that [mitmproxy](https://github.com/mitmproxy/) is installed and updated
- [soroban-cli](https://crates.io/crates/soroban-cli) is used to decode the XDR values, needs to be installed and in the PATH

## Usage
To use this plugin, run [mitmproxy](https://github.com/mitmproxy/) with the following command:
```
mitmproxy -s soroban_rpc_view.py
```
The custom view automatically activates when the JSON-RPC protocol is detected. To toggle between different view plugins, simply press the `m` key. 

## Tips

For instance, you can utilize [proxychains](https://github.com/haad/proxychains) to route `soroban-cli` through `mitmproxy`:
```
proxychains soroban contract deploy --wasm contract.wasm  --network standalone  
```

## Screenshots

Below are screenshots demonstrating the plugin in action:

Request (JSON view) | Request (Soroban RPC view)
--- | ---
![Request as plain JSON][req_json] | ![Request with Soroban-RPC view][req_soroban]

Response (JSON view) | Response (Soroban RPC view)
--- | ---
![Response as plain JSON][res_json] | ![Response with Soroban-RPC view][res_soroban]


[req_json]: https://i.imgur.com/zIqEMft.png
[req_soroban]: https://i.imgur.com/Lrienux.png
[res_json]: https://i.imgur.com/sNfyMLU.png
[res_soroban]: https://i.imgur.com/IkboHkT.png
