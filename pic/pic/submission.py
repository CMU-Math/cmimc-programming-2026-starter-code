from pic.strategy.strategy import Strategy, RegionRequest, PixelMessage, Message, Request
import random
import logging

logging.basicConfig(
    filename='debug.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)


# Don't change the name of this class when you submit!
class SubmissionStrategy(Strategy):
    def __init__(self, corrupted: list[list[float | None]]):
        self.corrupted = corrupted

    def make_requests(self) -> list[Request]:
        return []

    def receive_requests(self, requests: list[Request]) -> list[Message | None]:
        return [None] * len(requests)

    def receive_messages(self, messages: list[Message | None]):
        pass

    def recover(self) -> list[list[float | None]]:
        return [row[:] for row in self.corrupted]
