import httpx
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ConsolidatedAPIClient:
    """Client for the Healthbridge Care+ Consolidated API running on AI1 (10.30.229.21:8080).

    This replaces direct Registry and BOF API calls from AWS EC2.
    AI1 has internal hospital network access so it can reach Registry, BOF, and Aurora directly.
    AWS EC2 calls AI1 over the Site-to-Site VPN tunnel.
    """

    def __init__(self, base_url: str, token: str, timeout: int = 15, enabled: bool = True):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.enabled = enabled
        self._available: Optional[bool] = None
        logger.info(f"ConsolidatedAPIClient initialized: url={self.base_url}, enabled={enabled}")

    async def get_patient(self, fiscal_code: str) -> Optional[Dict[str, Any]]:
        """Fetch complete patient data (demographics + clinical events + discharges) from AI1."""
        if not self.enabled:
            logger.debug(f"Consolidated API disabled, skipping request for {fiscal_code}")
            return None

        url = f"{self.base_url}/api/v1/patient/{fiscal_code.upper().strip()}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }

        logger.info(f"Calling Consolidated API: {url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.get(url, headers=headers)
                logger.info(f"Consolidated API response: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    self._available = True
                    if data.get("patient_found"):
                        return data
                    else:
                        logger.info(f"Patient {fiscal_code} not found in consolidated DB")
                        return None
                elif response.status_code == 404:
                    self._available = True
                    logger.info(f"Patient {fiscal_code} not found (404)")
                    return None
                else:
                    logger.warning(f"Consolidated API returned status {response.status_code}")
                    return None

        except httpx.TimeoutException:
            logger.warning(f"Consolidated API timeout for {fiscal_code}")
            self._available = False
            return None
        except httpx.ConnectError as e:
            logger.warning(f"Consolidated API connection error (VPN down?): {e}")
            self._available = False
            return None
        except Exception as e:
            logger.error(f"Consolidated API error ({type(e).__name__}): {e}")
            self._available = False
            return None

    def is_available(self) -> Optional[bool]:
        return self._available
