from bots.basic import BasicBot, BasicGhost
from submission import SubmissionBot, SubmissionGhost

players = [("Submission", SubmissionBot, SubmissionGhost)]
bot = SubmissionBot  # Bot to test
ghost = SubmissionGhost # Ghost to test
seed = -1 # Random seed
graph_style = 2 # 0 is sparse, 1 is dense, 2 is a sparse set of dense clusters, 3 is tree with cycle of leaves
slots_style = 1 # 1 is distance, 2 is random

# Format message for visualization
def format_message(x: int) -> str:
    return str(x)
