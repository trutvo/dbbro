from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    name: str
    user: str
    password: str
    port: int | None = None
