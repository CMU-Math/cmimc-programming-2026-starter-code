# Clockwork

Clockwork is a puzzle programming language based on concentric rotating rings. Markers on adjacent rings interact when they align, triggering operations that transfer values between them. Your goal is to design programs (as JSON files) that compute the correct output for each task.

## Program Format

A Clockwork program is a JSON file with three fields:

```json
{
  "bitwidth": 2,
  "operations": ["give", "drop"],
  "rings": [
    [{ "position": 0, "bitstring": "10" }],
    [{ "position": 90, "bitstring": "01" }, { "position": 180, "bitstring": "11", "input": 0 }],
    [{ "position": 45, "bitstring": "10", "input": 1 }]
  ]
}
```

- **`bitwidth`** — number of operation layers; also the length of each marker's `bitstring`.
- **`operations`** — list of `bitwidth` operations, applied in order of bit significance. Valid operations: `give`, `take`, `drop`, `gen`, `copy`, `send`, `ifzflip`, `ifzhalt`.
- **`rings`** — odd-indexed rings rotate; even-indexed rings are stationary. Must have at least one ring. The first ring (index 0) must contain exactly one marker — its value is the program's output when `ifzhalt` fires.

### Markers

Each marker has:
- **`position`** — integer 0–359, the marker's starting angle on the ring. No two markers on the same ring may share a position.
- **`bitstring`** — binary string of length `bitwidth`; determines which operation layers this marker participates in.
- **`input`** (optional) — integer index; marks this marker as carrying the corresponding input value.

### How it runs

Each step, odd-indexed rings advance by one degree (direction can flip via `ifzflip`). When a marker on an odd ring aligns with a marker on an adjacent even ring, the pair triggers the operation for each bit layer where both markers' bitstrings have a `1`. Operations run in bit-layer order; within a bit, alignments fire inside-out (ring pair (0,1) before (1,2), etc.) and clockwise within each ring pair.

The simulation halts (and returns the center marker's value) when an `ifzhalt` fires on a marker with value 0. The maximum number of steps is 360,000,000.

## Running Your Program

Requires Python 3 and `click`:

```bash
pip install click
```

Grade a solution against a task's test cases:

```bash
python cli.py -c solve1.json -t tests/task1.json
```

Add `-v` for verbose per-test output:

```bash
python cli.py -c solve1.json -t tests/task1.json -v
```

### Options

| Flag | Description |
|------|-------------|
| `-c`, `--code` | Path to your program JSON file (required) |
| `-t`, `--tests` | Path to the test cases JSON file (required) |
| `-v`, `--verbose` | Print pass/fail for each test case |
| `-d`, `--debug` | Enable debug output |

## Tasks

Test cases are in the `tests/` directory (`task1.json` through `task10.json`). Each file contains a list of `{ "input": [...], "output": [...] }` objects. Write your solutions as `solve1.json` through `solve10.json`.

## Visualizer

Open `visualizer.html` in a browser to watch your program run step by step. Load your program JSON and a test input to see the rings rotate and markers interact in real time.

## Constraints

- At most 256 total markers across all rings.
- Programs exceeding 360,000,000 steps are considered to have timed out.
