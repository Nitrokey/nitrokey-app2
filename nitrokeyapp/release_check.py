"""Look up the latest release of a GitHub repository.

The REST API (api.github.com) is asked first. It allows only 60 unauthenticated requests per hour
and IP address, and that budget is shared with everything else behind the same address (NAT,
university or office networks). When it is used up, GitHub answers 403 and the update check used
to fail with "403 Client Error: rate limit exceeded".

In that case we fall back to the redirect behind ``https://github.com/<owner>/<name>/releases/latest``.
It is an ordinary web request, not part of the API budget, and it is only a stopgap: it depends on
GitHub keeping that redirect, so it may stop working at any time. Like the API's "latest release",
both lookups skip drafts and pre-releases.
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
    try:
        return _api_latest_tag(owner, name)
    except RateLimited as e:
        logger.info(f"GitHub API rate limit reached ({e}), using the releases page instead")
    return _web_latest_tag(owner, name)


def _api_latest_tag(owner: str, name: str) -> str:
    url = f"https://api.github.com/repos/{owner}/{name}/releases/latest"
    try:
        response = requests.get(
            url, headers={"Accept": "application/vnd.github+json"}, timeout=TIMEOUT_SECONDS
        )
    except requests.RequestException as e:
        raise Unreachable(str(e)) from e

    if response.status_code in (403, 429):
        raise RateLimited(f"GitHub API answered with HTTP {response.status_code}")
    if response.status_code != 200:
        raise ReleaseCheckError(f"GitHub API answered with HTTP {response.status_code}")

    try:
        tag = response.json()["tag_name"]
    except (ValueError, KeyError, TypeError) as e:
        raise ReleaseCheckError(f"unexpected answer from GitHub API: {e}") from e
    if not isinstance(tag, str) or not tag:
        raise ReleaseCheckError(f"unexpected tag from GitHub API: {tag!r}")
    logger.info(f"latest release of {owner}/{name}: {tag}")
    return tag


def _web_latest_tag(owner: str, name: str) -> str:
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
