from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; NZITJobApplicationAutomation/0.1)"


def fetch_json(url: str, timeout_seconds: int = 20) -> Any:
    if url.startswith("file://"):
        path = _path_from_file_url(url)
        return json.loads(path.read_text(encoding="utf-8"))

    request = Request(url, headers={"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=timeout_seconds) as response:
        body = response.read()
        encoding = response.headers.get_content_charset() or "utf-8"
        return json.loads(body.decode(encoding, errors="replace"))


def _path_from_file_url(url: str) -> Path:
    parsed_path = urlparse(url).path
    if len(parsed_path) >= 3 and parsed_path[0] == "/" and parsed_path[2] == ":":
        parsed_path = parsed_path[1:]
    return Path(parsed_path)

