from dataclasses import dataclass
from abc import ABC


def _check_type(name: str, value, expected):
    if not isinstance(value, expected):
        if isinstance(expected, tuple):
            expected_names = "/".join(t.__name__ for t in expected)
        else:
            expected_names = expected.__name__
        raise TypeError(f"{name} must be {expected_names}, got {type(value).__name__}")


class Request(ABC):
    pass

class Message(ABC):
    pass

@dataclass
class RegionRequest(Request):
    row_start: int
    row_end: int
    col_start: int
    col_end: int

    def __post_init__(self):
        _check_type("row_start", self.row_start, int)
        _check_type("row_end", self.row_end, int)
        _check_type("col_start", self.col_start, int)
        _check_type("col_end", self.col_end, int)

@dataclass
class RegionAverageRequest(Request):
    row_start: int
    row_end: int
    col_start: int
    col_end: int

    def __post_init__(self):
        _check_type("row_start", self.row_start, int)
        _check_type("row_end", self.row_end, int)
        _check_type("col_start", self.col_start, int)
        _check_type("col_end", self.col_end, int)

@dataclass
class PixelMessage(Message):
    row: int
    col: int
    value: float

    def __post_init__(self):
        _check_type("row", self.row, int)
        _check_type("col", self.col, int)
        _check_type("value", self.value, (int, float))

@dataclass
class RegionAverageMessage(Message):
    value: float

    def __post_init__(self):
        _check_type("value", self.value, (int, float))

@dataclass
class SplitRequest(Request):
    row1: int
    col1: int
    row2: int
    col2: int

    def __post_init__(self):
        _check_type("row1", self.row1, int)
        _check_type("col1", self.col1, int)
        _check_type("row2", self.row2, int)
        _check_type("col2", self.col2, int)

@dataclass
class SplitMessage(Message):
    split_axis: str | None  # "row", "col", or None (no boundary)
    split_pos: int | None   # where to cut, or None if no boundary

    def __post_init__(self):
        if self.split_axis is not None:
            _check_type("split_axis", self.split_axis, str)
        if self.split_pos is not None:
            _check_type("split_pos", self.split_pos, int)

class Strategy(ABC):
    def __init__(self, corrupted: list[list[float | None]]):
        pass

    def make_requests(self) -> list[Request]:
        pass

    def receive_requests(self, requests: list[Request]) -> list[Message | None]:
        pass

    def receive_messages(self, messages: list[Message | None]):
        pass

    def recover(self) -> list[list[float]]:
        pass
