import json
import gzip
from io import BytesIO
from typing import Any, Dict, Optional

import brotli
import requests

from . import utils
from .exceptions import API_REQUEST_FAILED, API_IMAGE_GENERATION_INSUFFICIENT_POINTS


DEFAULT_ASSISTANT_ID = "513695"
VERSION_CODE = "5.8.0"
PLATFORM_CODE = "7"
DEVICE_ID = utils.generate_device_id()
WEB_ID = utils.generate_web_id()
USER_ID = utils.generate_uuid(False)


FAKE_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-language": "zh-CN,zh;q=0.9",
    "Cache-control": "no-cache",
    "Last-event-id": "undefined",
    "Appid": DEFAULT_ASSISTANT_ID,
    "Appvr": VERSION_CODE,
    "Origin": "https://jimeng.jianying.com",
    "Pragma": "no-cache",
    "Priority": "u=1, i",
    "Referer": "https://jimeng.jianying.com",
    "Pf": PLATFORM_CODE,
    "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


def acquire_token(refresh_token: str) -> str:
    return refresh_token


def generate_cookie(token: str) -> str:
    return f"sessionid={token}; sessionid_ss={token}; sid_tt={token}; uid_tt={token}; uid_tt_ss={token}"


def decompress_response(response: requests.Response) -> str:
    content = response.content
    encoding = (response.headers.get("Content-Encoding") or "").lower()

    if encoding == "gzip":
        buffer = BytesIO(content)
        with gzip.GzipFile(fileobj=buffer) as f:
            content = f.read()
    elif encoding == "br":
        content = brotli.decompress(content)

    return content.decode("utf-8")


def request(
    method: str,
    uri: str,
    refresh_token: str,
    params: Optional[Dict] = None,
    data: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    **kwargs,
) -> Dict[str, Any]:
    token = acquire_token(refresh_token)
    device_time = utils.get_timestamp()
    sign = utils.md5(f"9e2c|{uri[-7:]}|{PLATFORM_CODE}|{VERSION_CODE}|{device_time}||11ac")

    _headers = {
        **FAKE_HEADERS,
        "Cookie": generate_cookie(token),
        "Device-Time": str(device_time),
        "Sign": sign,
        "Sign-Ver": "1",
    }
    if headers:
        _headers.update(headers)

    _params = {
        "aid": DEFAULT_ASSISTANT_ID,
        "device_platform": "web",
        "region": "CN",
        "web_id": WEB_ID,
    }
    if params:
        _params.update(params)

    response = requests.request(
        method=method.lower(),
        url=f"https://jimeng.jianying.com{uri}",
        params=_params,
        json=data,
        headers=_headers,
        timeout=15,
        verify=True,
        **kwargs,
    )

    try:
        content = decompress_response(response)
        result = json.loads(content)
    except Exception:
        raise API_REQUEST_FAILED("响应格式错误")

    ret = result.get("ret")
    if ret is None:
        return result

    if str(ret) == "0":
        return result.get("data", {})

    if str(ret) == "5000":
        raise API_IMAGE_GENERATION_INSUFFICIENT_POINTS(
            f"[无法生成图像]: 即梦积分可能不足，{result.get('errmsg')}"
        )

    raise API_REQUEST_FAILED(f"[请求jimeng失败]: {result.get('errmsg')}")

