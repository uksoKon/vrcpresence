"""Optional VRChat API lookups for world thumbnails and capacity.

Everything else in vrcpresence works without credentials - the log already
gives us the world's name, the players and the mode. The API is only needed
to turn a world ID into a picture, so it is strictly an enhancement and every
failure path here degrades quietly instead of breaking the session.

VRChat blocks clients that don't identify themselves, so a descriptive
User-Agent is mandatory, not optional.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

USER_AGENT = "vrcpresence/0.1.0 (https://github.com/uksoKon/vrcpresence)"
CACHE_VERSION = 1


@dataclass(frozen=True)
class WorldInfo:
    world_id: str
    name: str
    image_url: str | None
    capacity: int | None


class WorldCache:
    """World metadata barely changes; cache it hard to stay under rate limits."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._entries: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            return
        try:
            data = json.loads(self.path.read_text())
        except (json.JSONDecodeError, OSError):
            return
        if data.get("version") == CACHE_VERSION:
            self._entries = data.get("worlds", {})

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": CACHE_VERSION, "worlds": self._entries}
        try:
            self.path.write_text(json.dumps(payload, indent=2))
        except OSError:
            pass

    def get(self, world_id: str) -> WorldInfo | None:
        entry = self._entries.get(world_id)
        if entry is None:
            return None
        return WorldInfo(
            world_id=world_id,
            name=entry.get("name", ""),
            image_url=entry.get("image_url"),
            capacity=entry.get("capacity"),
        )

    def put(self, info: WorldInfo) -> None:
        self._entries[info.world_id] = {
            "name": info.name,
            "image_url": info.image_url,
            "capacity": info.capacity,
        }
        self._save()


class VRChatClient:
    """Minimal authenticated client. Unavailable credentials are not an error."""

    def __init__(self, cookie_path: Path, cache: WorldCache) -> None:
        self.cookie_path = Path(cookie_path)
        self.cache = cache
        self._api: Any = None
        self._worlds_api: Any = None
        self.last_error: str | None = None

    @property
    def authenticated(self) -> bool:
        return self._worlds_api is not None

    def _build_client(self, username: str = "", password: str = "") -> Any:
        import vrchatapi

        configuration = vrchatapi.Configuration(username=username, password=password)
        api_client = vrchatapi.ApiClient(configuration)
        api_client.user_agent = USER_AGENT
        return api_client

    def login(self, username: str, password: str, two_factor_code: str | None = None) -> bool:
        """Log in, optionally supplying a 2FA code. Returns success."""
        self.last_error = None
        try:
            from vrchatapi.api import authentication_api, worlds_api
            from vrchatapi.exceptions import UnauthorizedException
            from vrchatapi.models.two_factor_auth_code import TwoFactorAuthCode
        except ImportError:
            self.last_error = "vrchatapi package is not installed"
            return False

        api_client = self._build_client(username, password)
        auth_api = authentication_api.AuthenticationApi(api_client)

        try:
            auth_api.get_current_user()
        except UnauthorizedException:
            if two_factor_code is None:
                self.last_error = "two-factor code required"
                return False
            try:
                auth_api.verify2_fa(TwoFactorAuthCode(two_factor_code))
                auth_api.get_current_user()
            except Exception as inner:  # noqa: BLE001 - surfaced to the UI as text
                self.last_error = f"two-factor verification failed: {inner}"
                return False
        except Exception as exc:  # noqa: BLE001 - surfaced to the UI as text
            self.last_error = f"login failed: {exc}"
            return False

        self._api = api_client
        self._worlds_api = worlds_api.WorldsApi(api_client)
        self._save_cookies()
        return True

    def _save_cookies(self) -> None:
        if self._api is None:
            return
        try:
            self.cookie_path.parent.mkdir(parents=True, exist_ok=True)
            jar = self._api.rest_client.cookie_jar
            jar.save(str(self.cookie_path), ignore_discard=True, ignore_expires=True)
            self.cookie_path.chmod(0o600)
        except Exception as exc:  # noqa: BLE001 - never block login on cookie storage
            self.last_error = f"could not save session: {exc}"

    def restore_session(self) -> bool:
        """Reuse a saved session so people log in once, not every launch."""
        if not self.cookie_path.is_file():
            return False
        try:
            from vrchatapi.api import authentication_api, worlds_api
        except ImportError:
            return False

        try:
            api_client = self._build_client()
            api_client.rest_client.cookie_jar.load(
                str(self.cookie_path), ignore_discard=True, ignore_expires=True
            )
            authentication_api.AuthenticationApi(api_client).get_current_user()
        except Exception:  # noqa: BLE001 - expired sessions just mean "log in again"
            return False

        self._api = api_client
        self._worlds_api = worlds_api.WorldsApi(api_client)
        return True

    def get_world(self, world_id: str) -> WorldInfo | None:
        """Cached world lookup. Returns None when unauthenticated or failing."""
        if cached := self.cache.get(world_id):
            return cached
        if self._worlds_api is None:
            return None

        try:
            world = self._worlds_api.get_world(world_id)
        except Exception as exc:  # noqa: BLE001 - surfaced to the UI as text
            self.last_error = f"world lookup failed: {exc}"
            return None

        info = WorldInfo(
            world_id=world_id,
            name=getattr(world, "name", "") or "",
            image_url=getattr(world, "thumbnail_image_url", None) or getattr(world, "image_url", None),
            capacity=getattr(world, "capacity", None),
        )
        self.cache.put(info)
        return info

    def logout(self) -> None:
        self._api = None
        self._worlds_api = None
        try:
            self.cookie_path.unlink(missing_ok=True)
        except OSError:
            pass
