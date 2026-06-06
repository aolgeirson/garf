import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    database_url: str
    tokenstore: str
    trailing_days: int

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            database_url=os.environ["DATABASE_URL"],
            tokenstore=os.environ.get("GARF_TOKENSTORE", "~/.garminconnect"),
            trailing_days=int(os.environ.get("GARF_TRAILING_DAYS", "3")),
        )
