import codecs
import pickle

import numpy as np

import argschema.fields
import jsonpickle
import marshmallow as ma


class CutCircuitsResponse:
    def __init__(
        self,
        max_subcircuit_width,
        subcircuits,
        complete_path_map,
        num_cuts,
        counter,
        classical_cost,
        format,
        individual_subcircuits,
        init_meas_subcircuit_map,
    ):
        super().__init__()
        self.max_subcircuit_width = max_subcircuit_width
        if format == "openqasm2":
            self.subcircuits = [circ.qasm() for circ in subcircuits]
            self.individual_subcircuits = [
                circ.qasm() for circ in individual_subcircuits
            ]
        if format == "qiskit":
            self.subcircuits = [
                codecs.encode(pickle.dumps(circ), "base64").decode()
                for circ in subcircuits
            ]
            self.individual_subcircuits = [
                codecs.encode(pickle.dumps(circ), "base64").decode()
                for circ in individual_subcircuits
            ]
        self.complete_path_map = jsonpickle.encode(complete_path_map, keys=True)
        self.num_cuts = num_cuts
        self.counter = counter
        self.classical_cost = classical_cost
        self.init_meas_subcircuit_map = jsonpickle.encode(
            init_meas_subcircuit_map, keys=True
        )

    def to_json(self):
        json_execution_response = {
            "max_subcircuit_width": self.max_subcircuit_width,
            "subcircuits": self.subcircuits,
            "complete_path_map": self.complete_path_map,
            "num_cuts": self.num_cuts,
            "counter": self.counter,
            "classical_cost": self.classical_cost,
        }
        return json_execution_response


class CutCircuitsResponseSchema(ma.Schema):
    max_subcircuit_width = ma.fields.Int()
    subcircuits = ma.fields.List(ma.fields.Str())
    complete_path_map = ma.fields.Str()
    num_cuts = ma.fields.Int()
    counter = ma.fields.Dict(
        keys=ma.fields.Int(),
        values=ma.fields.Dict(keys=ma.fields.Str(), values=ma.fields.Int),
    )
    classical_cost = ma.fields.Int()
    individual_subcircuits = ma.fields.List(ma.fields.Str())
    init_meas_subcircuit_map = ma.fields.Str()


class CombineResultsResponse:
    def __init__(self, result):
        super().__init__()
        self.result = result

    def to_json(self):
        json_execution_response = {
            "result": self.result,
        }
        return json_execution_response


class CombineResultsResponseSchema(ma.Schema):
    result = argschema.fields.NumpyArray(dtype=np.float)


class CombineResultsResponseQuokkaSchema(ma.Schema):
    result = ma.fields.Dict(keys=ma.fields.Str(), values=ma.fields.Float())
