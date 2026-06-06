from garminconnect import Garmin

from garf.config import Config


def build_client(config: Config) -> Garmin:
    """Return an authenticated Garmin client.

    PLACEHOLDER — auth is handled by you. Wire up credentials/MFA and the
    garth token store here; everything downstream just consumes the client.
    """
    raise NotImplementedError("Garmin authentication not yet wired up")
