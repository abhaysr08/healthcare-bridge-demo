import httpx
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

from ..models import RegistryPatient, LuogoNascita, Indirizzo

logger = logging.getLogger(__name__)


# Mock Registry data for all Aurora patients (demo mode)
# In production, this data comes from the real Central Registry API
MOCK_REGISTRY_DATA = {
    "MNRMRA51R52H490N": {
        "CodiceFiscale": "MNRMRA51R52H490N",
        "Cognome": "MINARDI",
        "Nome": "MARIA",
        "DataNascita": "1951-10-12",
        "Sesso": "F",
        "IDAC": "2175296",
        "LuogoNascita": {"CodiceISTATComune": "078105", "DescrizioneComune": "ROGLIANO"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA VENTICINQUE APRILE 10 INT 2"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "V. XXV APRILE"}
    },
    "BRMSDR55B51C952D": {
        "CodiceFiscale": "BRMSDR55B51C952D",
        "Cognome": "BRAMBILLA",
        "Nome": "SANDRA",
        "DataNascita": "1955-02-11",
        "Sesso": "F",
        "IDAC": "980199467",
        "LuogoNascita": {"CodiceISTATComune": "015146", "DescrizioneComune": "MONZA"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA ROMA 45"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA ROMA 45"}
    },
    "BRMVNI67C25F205T": {
        "CodiceFiscale": "BRMVNI67C25F205T",
        "Cognome": "BRAMBILLA",
        "Nome": "IVANO",
        "DataNascita": "1967-03-25",
        "Sesso": "M",
        "IDAC": "CC06046127",
        "LuogoNascita": {"CodiceISTATComune": "015146", "DescrizioneComune": "MONZA"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA GARIBALDI 12"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA GARIBALDI 12"}
    },
    "MSRRNA51A11M140K": {
        "CodiceFiscale": "MSRRNA51A11M140K",
        "Cognome": "MISURACA",
        "Nome": "ARNO",
        "DataNascita": "1951-01-11",
        "Sesso": "M",
        "IDAC": "CC06046128",
        "LuogoNascita": {"CodiceISTATComune": "019121", "DescrizioneComune": "VOGHERA"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA MANZONI 8"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA MANZONI 8"}
    },
    "RVLNGL68L06F839G": {
        "CodiceFiscale": "RVLNGL68L06F839G",
        "Cognome": "IERVOLINO",
        "Nome": "ANGELO",
        "DataNascita": "1968-07-06",
        "Sesso": "M",
        "IDAC": "CC06046134",
        "LuogoNascita": {"CodiceISTATComune": "063049", "DescrizioneComune": "NAPOLI"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA DANTE 22"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA DANTE 22"}
    },
    "PLLNGL68M24F704K": {
        "CodiceFiscale": "PLLNGL68M24F704K",
        "Cognome": "PELLICCIOLI",
        "Nome": "ANGELO",
        "DataNascita": "1968-08-24",
        "Sesso": "M",
        "IDAC": "980268295",
        "LuogoNascita": {"CodiceISTATComune": "015146", "DescrizioneComune": "MONZA"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA VERDI 5"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA VERDI 5"}
    },
    "CSNRRT57P18B758Q": {
        "CodiceFiscale": "CSNRRT57P18B758Q",
        "Cognome": "COSENTINO",
        "Nome": "ROBERTO",
        "DataNascita": "1957-09-18",
        "Sesso": "M",
        "IDAC": "980268296",
        "LuogoNascita": {"CodiceISTATComune": "078045", "DescrizioneComune": "COSENZA"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA LEOPARDI 15"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA LEOPARDI 15"}
    },
    "STFGMG54P17B289R": {
        "CodiceFiscale": "STFGMG54P17B289R",
        "Cognome": "STEFFANI",
        "Nome": "GIACOMO GIOVANNI",
        "DataNascita": "1954-09-17",
        "Sesso": "M",
        "IDAC": "980268297",
        "LuogoNascita": {"CodiceISTATComune": "016024", "DescrizioneComune": "BERGAMO"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA PASCOLI 3"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA PASCOLI 3"}
    },
    "MZZCRL46T24F205U": {
        "CodiceFiscale": "MZZCRL46T24F205U",
        "Cognome": "MOZZI",
        "Nome": "CARLO",
        "DataNascita": "1946-12-24",
        "Sesso": "M",
        "IDAC": "980268298",
        "LuogoNascita": {"CodiceISTATComune": "015146", "DescrizioneComune": "MONZA"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA CARDUCCI 7"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA CARDUCCI 7"}
    },
    "CVNMRT81R64M052V": {
        "CodiceFiscale": "CVNMRT81R64M052V",
        "Cognome": "CAVENAGHI",
        "Nome": "MARTA",
        "DataNascita": "1981-10-24",
        "Sesso": "F",
        "IDAC": "980268299",
        "LuogoNascita": {"CodiceISTATComune": "015146", "DescrizioneComune": "MONZA"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA FOSCOLO 18"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA FOSCOLO 18"}
    },
    "GSTSLV93E60L667X": {
        "CodiceFiscale": "GSTSLV93E60L667X",
        "Cognome": "GASTI",
        "Nome": "SILVIA",
        "DataNascita": "1993-05-20",
        "Sesso": "F",
        "IDAC": "980268300",
        "LuogoNascita": {"CodiceISTATComune": "012133", "DescrizioneComune": "VARESE"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA PETRARCA 9"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA PETRARCA 9"}
    },
    "GLTNNA53B52A177T": {
        "CodiceFiscale": "GLTNNA53B52A177T",
        "Cognome": "GALATI",
        "Nome": "ANNA",
        "DataNascita": "1953-02-12",
        "Sesso": "F",
        "IDAC": "980268301",
        "LuogoNascita": {"CodiceISTATComune": "080001", "DescrizioneComune": "AGRIGENTO"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA TASSO 11"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA TASSO 11"}
    },
    "NDYTCK11B42M052K": {
        "CodiceFiscale": "NDYTCK11B42M052K",
        "Cognome": "NDOYE",
        "Nome": "TACKO",
        "DataNascita": "2011-02-02",
        "Sesso": "F",
        "IDAC": "980268302",
        "LuogoNascita": {"CodiceISTATComune": "015146", "DescrizioneComune": "MONZA"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA ARIOSTO 4"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA ARIOSTO 4"}
    },
    "BRGLSN78H10F704N": {
        "CodiceFiscale": "BRGLSN78H10F704N",
        "Cognome": "BROGNA",
        "Nome": "ALESSANDRO",
        "DataNascita": "1978-06-10",
        "Sesso": "M",
        "IDAC": "980268303",
        "LuogoNascita": {"CodiceISTATComune": "015146", "DescrizioneComune": "MONZA"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA BOCCACCIO 6"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA BOCCACCIO 6"}
    },
    "PRGMRA72P24F704P": {
        "CodiceFiscale": "PRGMRA72P24F704P",
        "Cognome": "PEREGO",
        "Nome": "MAURO",
        "DataNascita": "1972-09-24",
        "Sesso": "M",
        "IDAC": "980268304",
        "LuogoNascita": {"CodiceISTATComune": "015146", "DescrizioneComune": "MONZA"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA GOLDONI 14"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA GOLDONI 14"}
    },
    "CSTVNT09D52F704Z": {
        "CodiceFiscale": "CSTVNT09D52F704Z",
        "Cognome": "CASATI",
        "Nome": "VALENTINA ANNA",
        "DataNascita": "2009-04-12",
        "Sesso": "F",
        "IDAC": "980268305",
        "LuogoNascita": {"CodiceISTATComune": "015146", "DescrizioneComune": "MONZA"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA ALFIERI 20"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA ALFIERI 20"}
    },
    "FMGFLR57B45B798T": {
        "CodiceFiscale": "FMGFLR57B45B798T",
        "Cognome": "FUMAGALLI",
        "Nome": "FLORA",
        "DataNascita": "1957-02-05",
        "Sesso": "F",
        "IDAC": "980268306",
        "LuogoNascita": {"CodiceISTATComune": "013075", "DescrizioneComune": "COMO"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA PARINI 16"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA PARINI 16"}
    },
    "RSSFNC65S70G273A": {
        "CodiceFiscale": "RSSFNC65S70G273A",
        "Cognome": "RUSSO",
        "Nome": "FRANCESCA",
        "DataNascita": "1965-11-30",
        "Sesso": "F",
        "IDAC": "980268307",
        "LuogoNascita": {"CodiceISTATComune": "058091", "DescrizioneComune": "ROMA"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA MONTALE 2"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA MONTALE 2"}
    },
    "BRLDTM65T48F704I": {
        "CodiceFiscale": "BRLDTM65T48F704I",
        "Cognome": "BARLASSINA",
        "Nome": "DONATA MARIA",
        "DataNascita": "1965-12-08",
        "Sesso": "F",
        "IDAC": "980268308",
        "LuogoNascita": {"CodiceISTATComune": "015146", "DescrizioneComune": "MONZA"},
        "Residenza": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA QUASIMODO 10"},
        "Domicilio": {"CodiceISTATComune": "108050", "DescrizioneComune": "VIMERCATE", "Indirizzo": "VIA QUASIMODO 10"}
    }
}


class RegistryClient:
    def __init__(self, base_url: Optional[str] = None,
                 timeout: int = 5, enabled: bool = True, mock: bool = False, cache_ttl_minutes: int = 30):
        default_url = "https://clumiddle.aodv.local/AC/pac/rest/paziente"
        self.base_url = (base_url or default_url).rstrip("/")
        self.timeout = timeout
        # Disable if no URL provided and not in mock mode
        self.enabled = enabled and (base_url is not None or mock)
        self.mock = mock
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self._cache: Dict[str, tuple] = {}
        self._api_available: Optional[bool] = None
        logger.info(f"RegistryClient: enabled={self.enabled}, mock={mock}, timeout={timeout}s, url={self.base_url}")

    def _is_cache_valid(self, fiscal_code: str) -> bool:
        if fiscal_code not in self._cache:
            return False
        _, timestamp = self._cache[fiscal_code]
        return datetime.now() - timestamp < self.cache_ttl

    def _parse_response(self, data: dict) -> Optional[RegistryPatient]:
        try:
            luogo_nascita = None
            if data.get("LuogoNascita"):
                luogo_nascita = LuogoNascita(
                    codice_istat_comune=data["LuogoNascita"].get("CodiceISTATComune"),
                    descrizione_comune=data["LuogoNascita"].get("DescrizioneComune")
                )

            residenza = None
            if data.get("Residenza"):
                residenza = Indirizzo(
                    codice_istat_comune=data["Residenza"].get("CodiceISTATComune"),
                    descrizione_comune=data["Residenza"].get("DescrizioneComune"),
                    indirizzo=data["Residenza"].get("Indirizzo")
                )

            domicilio = None
            if data.get("Domicilio"):
                domicilio = Indirizzo(
                    codice_istat_comune=data["Domicilio"].get("CodiceISTATComune"),
                    descrizione_comune=data["Domicilio"].get("DescrizioneComune"),
                    indirizzo=data["Domicilio"].get("Indirizzo")
                )

            return RegistryPatient(
                codice_fiscale=data.get("CodiceFiscale", ""),
                cognome=data.get("Cognome", ""),
                nome=data.get("Nome", ""),
                data_nascita=data.get("DataNascita", ""),
                sesso=data.get("Sesso", ""),
                idac=data.get("IDAC"),
                luogo_nascita=luogo_nascita,
                residenza=residenza,
                domicilio=domicilio
            )
        except Exception as e:
            logger.error(f"Failed to parse Registry response: {e}")
            return None

    async def get_patient(self, fiscal_code: str) -> Optional[RegistryPatient]:
        fiscal_code = fiscal_code.upper().strip()

        if not self.enabled:
            return None

        if self._is_cache_valid(fiscal_code):
            patient, _ = self._cache[fiscal_code]
            return patient

        if self.mock:
            logger.info(f"Using mock Registry data for: {fiscal_code}")
            mock_data = MOCK_REGISTRY_DATA.get(fiscal_code)
            if mock_data:
                patient = self._parse_response(mock_data)
                self._cache[fiscal_code] = (patient, datetime.now())
                self._api_available = True
                return patient
            return None

        url = f"{self.base_url}/{fiscal_code}"
        logger.info(f"Calling Registry API: {url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.get(url, headers={"Accept": "application/json"})
                logger.info(f"Registry API response: {response.status_code}")

                if response.status_code == 200:
                    patient = self._parse_response(response.json())
                    self._cache[fiscal_code] = (patient, datetime.now())
                    self._api_available = True
                    return patient
                elif response.status_code == 404:
                    self._cache[fiscal_code] = (None, datetime.now())
                    self._api_available = True
                    return None
                return None

        except httpx.TimeoutException as e:
            logger.warning(f"Registry API timeout: {e}")
            self._api_available = False
            return None
        except httpx.ConnectError as e:
            logger.warning(f"Registry API connection error: {e}")
            self._api_available = False
            return None
        except Exception as e:
            logger.error(f"Registry API error: {type(e).__name__}: {e}")
            self._api_available = False
            return None

    def is_available(self) -> Optional[bool]:
        return self._api_available

    def clear_cache(self):
        self._cache.clear()
