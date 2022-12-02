import jsonpickle
import marshmallow as ma


class CutCircuitsResponse:
    def __init__(self, max_subcircuit_width, subcircuits, complete_path_map, num_cuts, counter, classical_cost):
        super().__init__()
        self.max_subcircuit_width = max_subcircuit_width
        self.subcircuits = [circ.qasm() for circ in subcircuits]
        self.complete_path_map = jsonpickle.encode(complete_path_map, keys=True)
        self.num_cuts = num_cuts
        self.counter = counter
        self.classical_cost = classical_cost

    def to_json(self):
        json_execution_response = {
            "max_subcircuit_width": self.max_subcircuit_width,
            "subcircuits": self.subcircuits,
            "complete_path_map": self.complete_path_map,
            "num_cuts": self.num_cuts,
            "counter": self.counter,
            "classical_cost": self.classical_cost
        }
        return json_execution_response


class CutCircuitsResponseSchema(ma.Schema):
    max_subcircuit_width = ma.fields.Int()
    subcircuits = ma.fields.List(ma.fields.Str())
    complete_path_map = ma.fields.Str()
    num_cuts = ma.fields.Int()
    counter = ma.fields.Dict(keys=ma.fields.Int(), values=ma.fields.Dict(keys=ma.fields.Str(), values=ma.fields.Int))
    classical_cost = ma.fields.Int()


class CombineResultsResponse:
    def __init__(self, counts, meas_qubits, transpiled_circuit_depth):
        super().__init__()
        self.counts = counts
        self.meas_qubits = meas_qubits
        self.transpiled_circuit_depth = transpiled_circuit_depth

    def to_json(self):
        json_execution_response = {
            "counts": self.counts,
            "meas_qubits": self.meas_qubits,
            "transpiled_circuit_depth": self.transpiled_circuit_depth,
        }
        return json_execution_response


class CombineResultsResponseSchema(ma.Schema):
    counts = ma.fields.Dict(keys=ma.fields.Str(), values=ma.fields.Float())
    meas_qubits = ma.fields.List(ma.fields.Int())
    transpiled_circuit_depth = ma.fields.Int()
