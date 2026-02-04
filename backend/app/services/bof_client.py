import httpx
import logging
from typing import Optional, List

from ..models import ProtectedDischarge

logger = logging.getLogger(__name__)


class BOFClient:
    """BOF API Client for protected discharges (dimissioni protette)."""

    def __init__(self, base_url: Optional[str] = None,
                 token: Optional[str] = None, timeout: int = 10, enabled: bool = False):
        self.base_url = base_url or "https://bof.asst-brianza.it/api/v1/index.php"
        self.token = token
        self.timeout = timeout
        self.enabled = enabled and token is not None and base_url is not None
        self._api_available: Optional[bool] = None

        if self.enabled:
            logger.info(f"BOFClient: enabled with token, timeout={timeout}s")
        else:
            logger.info(f"BOFClient: disabled (enabled={enabled}, has_token={token is not None}, has_url={base_url is not None})")

    async def get_protected_discharges(self, fiscal_code: str) -> List[ProtectedDischarge]:
        if not self.enabled:
            return []

        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.post(
                    self.base_url,
                    json={
                        "action": "dimissioniprotette.getpatitient",
                        "token": self.token,
                        "data": fiscal_code.upper()
                    }
                )
                logger.info(f"BOF API response status: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    self._api_available = True

                    # API returns: {"status": 1, "error": null, "data": <data or null>}
                    if result.get("status") == 1 and result.get("data"):
                        data = result["data"]
                        if isinstance(data, list):
                            logger.info(f"BOF: Found {len(data)} protected discharge(s) for {fiscal_code}")
                            return [ProtectedDischarge(data=item) for item in data if item]
                        elif isinstance(data, dict):
                            logger.info(f"BOF: Found 1 protected discharge for {fiscal_code}")
                            return [ProtectedDischarge(data=data)]

                    logger.info(f"BOF: No protected discharge data for {fiscal_code}")
                    return []
                return []
        except Exception as e:
            logger.error(f"BOF API error: {e}")
            self._api_available = False
            return []

    def is_available(self) -> bool:
        if self._api_available is not None:
            return self._api_available
        return self.enabled
