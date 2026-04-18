from typing import List, Tuple, Optional, Dict, Any
import json, bisect

MAX_STEPS = 360 * 1000000
ops = ["give", "take", "drop", "gen", "copy", "send", "ifzflip", "ifzhalt"]

class ClockworkResult:
    def __init__(self, test_path: str, num_tests: int, num_pass_tests: int, num_bits: int, num_markers: int, num_rings: int):
        self.test_path = test_path
        self.num_tests = num_tests
        self.num_pass_tests = num_pass_tests
        self.num_bits = num_bits
        self.num_markers = num_markers
        self.num_rings = num_rings

class Marker:
    def __init__(self, position: int, bitstring: int, input_pos: int = -1, value: int = 0):
        self.original = position
        self.pos = position
        self.bitstring = bitstring
        self.input_pos = input_pos
        self.value = value

class ClockworkSimulator:
    def __init__(self, bitwidth: int, operations: List[str], rings: List[List[Marker]], inputs: int, debug: bool = False):
        self.bitwidth = bitwidth
        self.bitmax = 2 ** bitwidth
        self.operations = operations
        self.rings = rings
        self.debug = debug
        self.inputs = inputs

        # layer_alignments[k] maps offset -> list of (i1, i2, j1, j2)
        # sorted clockwise from 0° (the pair's alignment angle).
        # Since all rotating rings share one global offset, a pair (k, k+1) aligns
        # iff offset == (stationary.pos - rotating.pos) % 360.
        num_layers = len(rings) - 1
        self.layer_alignments = [{} for _ in range(num_layers)]
        offsets_set = set()
        for k in range(num_layers):
            k_rotating = (k % 2 == 1)
            bucket = {}
            for i2, inner in enumerate(rings[k]):
                for j2, outer in enumerate(rings[k + 1]):
                    if k_rotating:
                        offset = (outer.original - inner.original) % 360
                        angle = outer.original
                    else:
                        offset = (inner.original - outer.original) % 360
                        angle = inner.original
                    bucket.setdefault(offset, []).append((angle, k, i2, k + 1, j2))
                    offsets_set.add(offset)
            for offset, entries in bucket.items():
                entries.sort(key=lambda e: e[0])
                self.layer_alignments[k][offset] = [(e[1], e[2], e[3], e[4]) for e in entries]
        self.offsets_sorted = sorted(offsets_set)
        self.reset()

    def reset(self) -> None:
        for ring in self.rings:
            for m in ring:
                m.pos = m.original
                m.value = 0

        self.dir = 1
        self._step = 0
        self.offset = 0
    
    def inject(self, inp: List[int]) -> None:
        if len(inp) != self.inputs:
            raise ValueError(f"Wrong input count: {len(inp)}")
        
        for ring in self.rings:
            for m in ring:
                if m.input_pos != -1:
                    m.value = inp[m.input_pos]

    def handle_op(self, i1, i2, j1, j2, op) -> bool:
        if i1 > j1:
            raise Exception("Bug in code.")
        if op == "give":
            if self.rings[j1][j2].value != 0:
                self.rings[j1][j2].value -= 1
                self.rings[i1][i2].value += 1
        elif op == "take":
            if self.rings[i1][i2].value != 0:
                self.rings[j1][j2].value += 1
                self.rings[i1][i2].value -= 1
        elif op == "drop":
            if self.rings[i1][i2].value != 0 and self.rings[j1][j2].value != 0:
                self.rings[i1][i2].value -= 1
                self.rings[j1][j2].value -= 1
        elif op == "gen":
            self.rings[i1][i2].value += 1
            self.rings[j1][j2].value += 1
        elif op == "copy":
            self.rings[j1][j2].value += self.rings[i1][i2].value
        elif op == "send":
            self.rings[i1][i2].value += self.rings[j1][j2].value
            self.rings[j1][j2].value = 0
        elif op == "ifzflip":
            if self.rings[i1][i2].value == 0:
                self.dir *= -1
        elif op == "ifzhalt":
            if self.rings[i1][i2].value == 0:
                return True
        return False


    def step(self) -> Optional[int]:
        if self._step >= MAX_STEPS or not self.offsets_sorted:
            self._step = MAX_STEPS
            return None
        n = len(self.offsets_sorted)
        if self.dir == 1:
            idx = bisect.bisect_right(self.offsets_sorted, self.offset) % n
            next_off = self.offsets_sorted[idx]
            delta = (next_off - self.offset) % 360
            if delta == 0:
                delta = 360
        else:
            idx = bisect.bisect_left(self.offsets_sorted, self.offset) - 1
            next_off = self.offsets_sorted[idx]
            delta = (self.offset - next_off) % 360
            if delta == 0:
                delta = 360

        if self._step + delta > MAX_STEPS:
            self._step = MAX_STEPS
            return None
        self._step += delta
        self.offset = next_off

        for bit_idx in range(self.bitwidth):
            bit = 1 << bit_idx
            for layer in self.layer_alignments:
                entries = layer.get(self.offset)
                if not entries:
                    continue
                for (i1, i2, j1, j2) in entries:
                    m1 = self.rings[i1][i2]
                    m2 = self.rings[j1][j2]
                    if m1.bitstring & m2.bitstring & bit:
                        if self.handle_op(i1, i2, j1, j2, self.operations[bit_idx]):
                            return self.rings[0][0].value
        return None

    def initialize(self, inp: List[int]) -> None:
        self.reset()
        self.inject(inp)

    def simulate(self, inp: List[int]) -> Optional[int]:
        self.initialize(inp)
        while self._step < MAX_STEPS:
            result = self.step()
            if result is not None:
                return result
        return None

class ClockworkEngine:
    @staticmethod
    def _parse_code(code_path: str) -> (ClockworkSimulator, int, int):
        with open(code_path) as f:
            code = json.load(f)

        if not code:
            raise ValueError("Empty")

        bitwidth = code["bitwidth"]
        operations = code["operations"]
        rings = code["rings"]
        if type(bitwidth) is not int:
            raise ValueError("bitwidth not present")
        if type(operations) is not list:
            raise ValueError("operations not present")
        if type(rings) is not list:
            raise ValueError("rings not present")

        if len(operations) != bitwidth:
            raise ValueError("bitwidth not equal to operations length")
        for o in operations:
            if o not in ops:
                raise ValueError(f"invalid operation: {o}")

        inputs = []
        markers = 0
        real_rings = []
        for ring in rings:
            next_ring = []
            if type(ring) is not list:
                raise ValueError("ring is not a list")
            markers += len(ring)
            positions = set()
            for m in ring:
                if len(m["bitstring"]) != bitwidth:
                    raise ValueError(f"invalid bitstring for marker: {m}")
                if type(m["position"]) != int or m["position"] > 359 or m["position"] < 0:
                    raise ValueError(f"invalid position: {m["position"]}")
                if m["position"] in positions:
                    raise ValueError(f"duplicate positions: {m["position"]}")
                positions.add(m["position"])
                marker = Marker(m["position"], int(m["bitstring"][::-1], 2))
                if type(m.get("input")) is int:
                    inputs.append(m["input"])
                    marker.input_pos = m["input"]
                next_ring.append(marker)
            real_rings.append(next_ring)
        inputs = sorted(inputs)
        for i in range(len(inputs)):
            if inputs[i] != i:
                raise ValueError("bad input labeling")
            
        if len(real_rings) == 0 or len(real_rings[0]) != 1:
            raise ValueError("Must have a center ring of one marker")
        if markers > 256:
            raise ValueError("Too many markers in program.")

        return (ClockworkSimulator(bitwidth, operations, real_rings, len(inputs)), len(real_rings), markers)

    @staticmethod
    def _parse_tests(test_path: str) -> List[Dict[str, List[int]]]:
        with open(test_path) as f:
            return json.loads(f.read())

    def grade(self, code_path: str, test_path: str, debug: bool = False, verbose: bool = False) -> ClockworkResult:
        simulator, num_rings, num_markers = self._parse_code(code_path)

        tests = self._parse_tests(test_path)

        num_tests = len(tests)
        num_pass_tests = 0
        for test_case in tests:
            if verbose:
                print(f"Running test with input {test_case['input']}")
            
            output = simulator.simulate(test_case["input"])
            if output is None:
                if verbose:
                    print("Maximum steps exceeded")
            else:
                if output == test_case["output"][0]:
                    num_pass_tests += 1
                    if verbose:
                        print("Success")
                else:
                    if verbose:
                        print(f"Fail, gave {output} when expected is {test_case['output'][0]}")

        return ClockworkResult(test_path, num_tests, num_pass_tests, simulator.bitwidth, num_markers, num_rings)
