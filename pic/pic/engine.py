import copy

from pic.generate import Generate, GenerateConfig
from pic.corrupt import Corrupt, CorruptConfig
from pic.strategy.strategy import Strategy, RegionRequest, RegionAverageRequest, SplitRequest, PixelMessage, RegionAverageMessage, SplitMessage

class Engine:
    def __init__(self, generate: Generate, generate_config: GenerateConfig, corrupt: Corrupt, corrupt_config: CorruptConfig):
        self.generate = generate
        self.generate_config = generate_config
        self.corrupt = corrupt
        self.corrupt_config = corrupt_config

    def play(self, player_one: Strategy, player_two: Strategy, return_images: bool = False):
        og_pic = self.generate.generate(self.generate_config)
        corrupt_pic_one, corrupt_pic_two = self.corrupt.corrupt_pair(self.corrupt_config, og_pic)

        player_one = player_one(corrupt_pic_one)
        player_two = player_two(corrupt_pic_two)

        requests_one = player_one.make_requests()
        requests_two = player_two.make_requests()

        messages_one = player_one.receive_requests(copy.deepcopy(requests_two))
        messages_two = player_two.receive_requests(copy.deepcopy(requests_one))

        if len(messages_one) != len(requests_two):
            raise ValueError(f"Player one returned {len(messages_one)} messages for {len(requests_two)} requests")
        if len(messages_two) != len(requests_one):
            raise ValueError(f"Player two returned {len(messages_two)} messages for {len(requests_one)} requests")

        def _validate_message(msg, req, player_name):
            if msg is None:
                return
            if isinstance(req, RegionRequest):
                if not isinstance(msg, PixelMessage):
                    raise ValueError(f"{player_name} responded with wrong message type for RegionRequest")
                if not (req.row_start <= msg.row < req.row_end and req.col_start <= msg.col < req.col_end):
                    raise ValueError(f"{player_name} responded with pixel ({msg.row}, {msg.col}) outside requested region")
            elif isinstance(req, RegionAverageRequest):
                if not isinstance(msg, RegionAverageMessage):
                    raise ValueError(f"{player_name} responded with wrong message type for RegionAverageRequest")
            elif isinstance(req, SplitRequest):
                if not isinstance(msg, SplitMessage):
                    raise ValueError(f"{player_name} responded with wrong message type for SplitRequest")
                if msg.split_axis is not None:
                    if msg.split_axis not in ("row", "col"):
                        raise ValueError(f"{player_name} responded with invalid split_axis: {msg.split_axis}")
                    if msg.split_axis == "row" and not (req.row1 < msg.split_pos < req.row2):
                        raise ValueError(f"{player_name} responded with split_pos {msg.split_pos} outside row range ({req.row1}, {req.row2})")
                    if msg.split_axis == "col" and not (req.col1 < msg.split_pos < req.col2):
                        raise ValueError(f"{player_name} responded with split_pos {msg.split_pos} outside col range ({req.col1}, {req.col2})")

        for msg, req in zip(messages_one, requests_two):
            _validate_message(msg, req, "Player one")
        for msg, req in zip(messages_two, requests_one):
            _validate_message(msg, req, "Player two")

        player_one.receive_messages(copy.deepcopy(messages_two))
        player_two.receive_messages(copy.deepcopy(messages_one))

        player_pic_one = player_one.recover()
        player_pic_two = player_two.recover()

        total_pixels = len(og_pic) * len(og_pic[0])
        n = len(og_pic)  # image side length

        # A None value, missing row, short row, or non-numeric value in a
        # recovered image counts as the maximum per-pixel error (1.0).
        def _mae(recovered, original):
            if not isinstance(recovered, list):
                return 1.0
            total = 0.0
            for i, row_o in enumerate(original):
                row_r = recovered[i] if i < len(recovered) and isinstance(recovered[i], list) else []
                for j, o in enumerate(row_o):
                    r = row_r[j] if j < len(row_r) else None
                    if not isinstance(r, (int, float)) or isinstance(r, bool):
                        total += 1.0
                    else:
                        total += min(1.0, abs(r - o))
            return total / total_pixels

        mae_one = _mae(player_pic_one, og_pic)
        mae_two = _mae(player_pic_two, og_pic)

        responses_one = sum(1 for m in messages_one if m is not None)
        responses_two = sum(1 for m in messages_two if m is not None)

        # requests_answered = how many of a player's requests got a response from the opponent
        requests_answered_one = sum(1 for m in messages_two if m is not None)
        requests_answered_two = sum(1 for m in messages_one if m is not None)

        score_one = mae_one + 0.5 * mae_two + 0.25 * (requests_answered_one / n) ** 2 + 0.1 * (responses_one / n) ** 2
        score_two = mae_two + 0.5 * mae_one + 0.25 * (requests_answered_two / n) ** 2 + 0.1 * (responses_two / n) ** 2

        if return_images:
            return (score_one, score_two), (og_pic, corrupt_pic_one, corrupt_pic_two, player_pic_one, player_pic_two)
        return (score_one, score_two)
