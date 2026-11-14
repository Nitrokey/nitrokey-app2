"""Look up the latest release of a GitHub repository without using the REST API.

The REST API (api.github.com) allows only 60 unauthenticated requests per hour and IP address.
That budget is shared with everything else behind the same address (NAT, university or office
networks) and is easily used up, which made the update check fail with
"403 Client Error: rate limit exceeded".

The redirect behind ``https://github.com/<owner>/<name>/releases/latest`` is an ordinary web
request that does not count against that budget. Like the API's "latest release" it skips
drafts and pre-releases.
"""

import logging
import re
from urllib.parse import unquote

import requests

logger = logging.getLogger(__name__)

# the check runs on the UI thread, so do not wait for long
TIMEOUT_SECONDS = 5

_TAG_PATTERN = re.compile(r"/releases/tag/([^/?#]+)$")


class ReleaseCheckError(Exception):
    """The latest release could not be determined."""


class RateLimited(ReleaseCheckError):
    """GitHub asked us to slow down."""


class Unreachable(ReleaseCheckError):
    """GitHub could not be reached (no network, DNS failure, timeout, ...)."""


def releases_url(owner: str, name: str) -> str:
    return f"https://github.com/{owner}/{name}/releases"


def get_latest_tag(owner: str, name: str) -> str:
    """Return the tag (for example "v2.7.1") of the latest release of owner/name."""
    url = f"{releases_url(owner, name)}/latest"
    try:
        response = requests.head(url, allow_redirects=False, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as e:
        raise Unreachable(str(e)) from e

    if response.status_code in (403, 429):
        raise RateLimited(f"GitHub answered with HTTP {response.status_code}")

    location = response.headers.get("Location", "")
    match = _TAG_PATTERN.search(location) if response.is_redirect else None
    if not match:
        raise ReleaseCheckError(
            f"unexpected answer from GitHub: HTTP {response.status_code}, Location {location!r}"
        )

    tag = unquote(match.group(1))
    logger.info(f"latest release of {owner}/{name}: {tag}")
    return tag
