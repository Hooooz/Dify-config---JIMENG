import json
import random
import time
import uuid
import hashlib
from typing import Any, List
from urllib.parse import quote


def is_finite(value: Any) -> bool:
    try:
        float_val = float(value)
        return not (
            float_val == float("inf")
            or float_val == float("-inf")
            or float_val != float_val
        )
    except (TypeError, ValueError):
        return False


def get_timestamp() -> int:
    return int(time.time())


def generate_uuid(with_hyphen: bool = True) -> str:
    value = str(uuid.uuid4())
    return value if with_hyphen else value.replace("-", "")


def md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def generate_device_id() -> int:
    return int(random.random() * 999999999999999999 + 7000000000000000000)


def generate_web_id() -> int:
    return int(random.random() * 999999999999999999 + 7000000000000000000)


def token_split(auth: str) -> List[str]:
    if not auth:
        return []
    auth = auth.replace("Bearer", "").strip()
    return [t.strip() for t in auth.split(",") if t.strip()]


def json_encode(obj: object) -> str:
    return json.dumps(obj, separators=(",", ":"))


def url_encode(text: str) -> str:
    return quote(text)

