from typing import List, Tuple, Optional, Dict, Any
import json

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
    def __init__(self, bitwidth: int, operations: int, rings: List[List[Marker]], inputs: int, debug: bool = False):
        self.bitwidth = bitwidth
        self.bitmax = 2 ** bitwidth
        self.operations = operations
        self.rings = rings
        self.debug = debug
        self.inputs = inputs

        self.reset()

    def reset(self) -> None:
        for ring in self.rings:
            for m in ring:
                m.pos = m.original
                m.value = 0

        self.dir = 1
        self._step = 0
    
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
        if self._step >= MAX_STEPS:
            return None
        self._step += 1

        connections = []

        for i in range(1, len(self.rings), 2):
            for j, m in enumerate(self.rings[i]):
                m.pos = (m.pos + self.dir + 360) % 360
                for k, mark in enumerate(self.rings[i - 1]):
                    if mark.pos == m.pos:
                        connections.append([i - 1, k, i, j])
                if i + 1 != len(self.rings):
                    for k, mark in enumerate(self.rings[i + 1]):
                        if mark.pos == m.pos:
                            connections.append([i, j, i + 1, k])

        connections.sort(key=lambda c: (c[0], self.rings[c[0]][c[1]].pos))
        
        index = 0
        i = 1
        while i < self.bitmax:
            for c in connections:
                m1 = self.rings[c[0]][c[1]]
                m2 = self.rings[c[2]][c[3]]
                if m1.bitstring & m2.bitstring & i > 0:
                    ret = self.handle_op(c[0], c[1], c[2], c[3], self.operations[index])
                    if ret:
                        return self.rings[0][0].value
            i *= 2
            index += 1

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
