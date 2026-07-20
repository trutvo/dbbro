from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol


class View(Protocol):
    def render(self, screen) -> None: ...

    def handle_key(self, key: int) -> "Transition | None": ...


class TransitionKind(Enum):
    PUSH = auto()
    POP = auto()


@dataclass(frozen=True)
class Transition:
    kind: TransitionKind
    view: View | None = None

    @staticmethod
    def push(view: View) -> "Transition":
        return Transition(kind=TransitionKind.PUSH, view=view)

    @staticmethod
    def pop() -> "Transition":
        return Transition(kind=TransitionKind.POP)


class ViewStack:
    def __init__(self, initial: View):
        self.frames: list[View] = [initial]

    @property
    def current(self) -> View:
        return self.frames[-1]

    def push(self, view: View) -> None:
        self.frames.append(view)

    def pop(self) -> None:
        if len(self.frames) > 1:
            self.frames.pop()

    def apply(self, transition: Transition | None) -> None:
        if transition is None:
            return
        if transition.kind is TransitionKind.PUSH:
            self.push(transition.view)
        elif transition.kind is TransitionKind.POP:
            self.pop()

    def reset_to(self, view: View) -> None:
        """Discard every frame above the bottom and push a fresh view.

        Used by the main loop's global `s` interception: it clears any
        view stacked above the underlying view and pushes a fresh
        SearchSelectionDialog, discarding whatever the previous top view
        held (FR19).
        """
        self.frames = [self.frames[0], view]
