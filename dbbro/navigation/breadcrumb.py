from dataclasses import dataclass


@dataclass(frozen=True)
class BreadcrumbStop:
    table: str
    primary_key_value: str


class Breadcrumb:
    def __init__(self):
        self.stops: list[BreadcrumbStop] = []

    def push(self, stop: BreadcrumbStop) -> None:
        self.stops.append(stop)

    def reset(self) -> None:
        self.stops = []

    def as_list(self) -> list[BreadcrumbStop]:
        return list(self.stops)
