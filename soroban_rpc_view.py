import json
import re
import os
import tempfile
import subprocess
from collections.abc import Iterator
from mitmproxy import contentviews, flow, http, ctx
from mitmproxy.addonmanager import Loader
from typing import Any

PARSE_ERROR = object()

def parse_json(s: bytes) -> Any:
    try:
        return json.loads(s.decode("utf-8"))
    except ValueError:
        return PARSE_ERROR

def format_json(data: Any) -> Iterator[contentviews.base.TViewLine]:
    encoder = json.JSONEncoder(indent=4, sort_keys=True, ensure_ascii=False)
    current_line: contentviews.base.TViewLine = []
    for chunk in encoder.iterencode(data):
        if "\n" in chunk:
            rest_of_last_line, chunk = chunk.split("\n", maxsplit=1)
            current_line.append(("text", rest_of_last_line))
            yield current_line
            current_line = []
        if re.match(r'\s*"', chunk):
            if (
                len(current_line) == 1
                and current_line[0][0] == "text"
                and current_line[0][1].isspace()
            ):
                current_line.append(("Token_Name_Tag", chunk))
            else:
                current_line.append(("Token_Literal_String", chunk))
        elif re.match(r"\s*\d", chunk):
            current_line.append(("Token_Literal_Number", chunk))
        elif re.match(r"\s*(true|null|false)", chunk):
            current_line.append(("Token_Keyword_Constant", chunk))
        else:
            current_line.append(("text", chunk))
    yield current_line

def xdr_to_json(xdr_type: str, input_string: str) -> str:
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        temp_file.write(input_string)
        temp_file_path = temp_file.name

    command = ['soroban', 'lab', 'xdr', 'decode', '--type', xdr_type, temp_file_path]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    finally:
        try:
            os.remove(temp_file_path)
        except OSError:
            pass

def process_json(method, json_data):
    if method == "simulateTransaction":
        if "result" in json_data:
            json_data["result"]["transactionData"] = xdr_to_json('SorobanTransactionData', json_data["result"]["transactionData"])
            if "results" in json_data["result"]:
                for result in json_data["result"]["results"]:
                    if "xdr" in result:
                        result["xdr"] = xdr_to_json('ScVal', result["xdr"])
                    if "auth" in result:
                        result["auth"] = [ xdr_to_json('SorobanAuthorizationEntry',auth) for auth in result["auth"]]
            if "events" in json_data["result"]:
                json_data["result"]["events"] = [ xdr_to_json('DiagnosticEvent',event) for event in json_data["result"]["events"]]
        if "params" in json_data:
            if "transaction" in json_data["params"]:
                json_data["params"]["transaction"] = xdr_to_json('TransactionEnvelope', json_data["params"]["transaction"])
    if method == "sendTransaction":
        if "params" in json_data:
                json_data["params"] = [ xdr_to_json('TransactionEnvelope',event) for event in json_data["params"]]
    if method == "getTransaction":
        if "result" in json_data:
            if "status" in json_data["result"]:
                if json_data["result"]["status"] == "SUCCESS":
                    json_data["result"]["resultMetaXdr"] = xdr_to_json('TransactionMeta', json_data["result"]["resultMetaXdr"])
                    json_data["result"]["envelopeXdr"] = xdr_to_json('TransactionEnvelope', json_data["result"]["envelopeXdr"])
                    json_data["result"]["resultXdr"] = xdr_to_json('TransactionResult', json_data["result"]["resultXdr"])
    if method == "getLedgerEntries":
        if "result" in json_data:
            if "entries" in json_data["result"]:
                for entry in json_data["result"]["entries"]:
                    entry["key"] = xdr_to_json('LedgerKey', entry["key"])
                    entry["xdr"] = xdr_to_json('LedgerEntryData', entry["xdr"])
        if "params" in json_data:
            json_data["params"][0] = [xdr_to_json('LedgerKey', param) for param in json_data["params"][0]]


    return json_data


class SorobanJsonRpcView(contentviews.View):
    name = "soroban jsonrpc"

    def __call__(
        self,
        data: bytes,
        *,
        content_type: str | None = None,
        flow: flow.Flow | None = None,
        http_message: http.Message | None = None,
        **unknown_metadata,
    ) -> contentviews.TViewResult:
        data_parsed = parse_json(data)
        method = flow.request.json()["method"]
        data_parsed = process_json(method, data_parsed)

        if data_parsed is not PARSE_ERROR:
            return "Soroban Json-RPC", format_json(data_parsed)


    def render_priority(
        self,
        data: bytes,
        *,
        content_type: str | None = None,
        flow: flow.Flow | None = None,
        http_message: http.Message | None = None,
        **unknown_metadata,
    ) -> float:
        if content_type == "application/json":
            return 1
        else:
            return 0


view = SorobanJsonRpcView()


def load(loader: Loader):
    contentviews.add(view)


def done():
    contentviews.remove(view)
