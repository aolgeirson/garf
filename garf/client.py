from garminconnect import Garmin

from garf.config import Config
import os


def build_client(config: Config) -> Garmin:
    """Return an authenticated Garmin client.

    PLACEHOLDER — auth is handled by you. Wire up credentials/MFA and the
    garth token store here; everything downstream just consumes the client.
    """
    try:
        client = Garmin(
            os.getenv("GC_EMAIL"),
            os.getenv("GC_PASSWD"),
            prompt_mfa=lambda: input("MFA code: "),
        )
        client.login("~/.garminconnect")
        return client
    except Exception as e:
        print("Login Failed")
        print("Error: ", e)
        exit(1)
