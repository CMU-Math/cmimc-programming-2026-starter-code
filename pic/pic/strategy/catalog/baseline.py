import logging
import random

from pic.strategy.strategy import Strategy, RegionRequest, PixelMessage, Message, Request

logging.basicConfig(
    filename='debug.log',
    level=logging.DEBUG,
    format='%(levelname)s: %(message)s',
)


class Baseline(Strategy):
    def __init__(self, corrupted: list[list[float | None]]):
        self.corrupted = corrupted
        missing = sum(1 for row in corrupted for v in row if v is None)
        logging.debug(f"Baseline received {len(corrupted)}x{len(corrupted[0])} grid with {missing} missing pixels")

    def make_requests(self) -> list[Request]:
        bound = 50
        sorts = [(abs(0.5 - val) if val is not None else 0.5, (i, j)) for i, row in enumerate(self.corrupted) for j, val in enumerate(row)]
        sorts = sorted(sorts, reverse=True)[:bound]
        self.reqs = [RegionRequest(row_start=i, row_end=i+1, col_start=j, col_end=j+1) for _, (i, j) in sorts]
        logging.debug(f"Issuing {len(self.reqs)} pixel requests")
        return self.reqs

    def receive_requests(self, requests: list[Request]) -> list[Message | None]:
        messages = []
        for req in requests:
            row = random.randint(req.row_start, req.row_end - 1)
            col = random.randint(req.col_start, req.col_end - 1)
            val = self.corrupted[row][col]
            if val is None:
                messages.append(None)
            else:
                messages.append(PixelMessage(row=row, col=col, value=val))
        return messages

    def receive_messages(self, messages: list[Message | None]):
        self.messages = messages

    def recover(self) -> list[list[float | None]]:
        return [row[:] for row in self.corrupted]
