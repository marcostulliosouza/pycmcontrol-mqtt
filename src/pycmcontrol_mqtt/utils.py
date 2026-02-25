import base64
import time


def now_ts() -> int:
    return int(time.time())


def b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")