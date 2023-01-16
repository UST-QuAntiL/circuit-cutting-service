import marshmallow as ma
import numpy as np
import argschema


class CutCircuitsRequest:
    def __init__(
            self,
            circuit,
            method,
            max_subcircuit_width=500,
            max_cuts=100,
            num_subcircuits=None,
            subcircuit_vertices=None,
            circuit_format="openqasm2",
    ):
        if num_subcircuits is None:
            num_subcircuits = [2]
        self.circuit = circuit
        self.method = method
        self.max_subcircuit_width = max_subcircuit_width
        self.max_cuts = max_cuts
        self.num_subcircuits = num_subcircuits
        self.subcircuit_vertices = subcircuit_vertices
        self.circuit_format = circuit_format.lower()


class CutCircuitsRequestSchema(ma.Schema):
    circuit = ma.fields.Str(required=True)
    method = ma.fields.Str(required=True, default="automatic")
    max_subcircuit_width = ma.fields.Int(required=False)
    max_cuts = ma.fields.Int(required=False)
    num_subcircuits = ma.fields.List(ma.fields.Int, required=False)
    subcircuit_vertices = ma.fields.List(ma.fields.List(ma.fields.Int), required=False)
    circuit_format = ma.fields.String(required=False)


class CombineResultsRequest:
    def __init__(self, circuit, subcircuit_results, cuts, circuit_format="openqasm2"):
        self.circuit = circuit
        self.subcircuit_results = subcircuit_results
        self.cuts = cuts
        self.circuit_format = circuit_format


class CombineResultsRequestSchema(ma.Schema):
    circuit = ma.fields.Str(required=True)
    subcircuit_results = ma.fields.List(argschema.fields.NumpyArray(dtype=np.float), required=True)
    cuts = ma.fields.Dict(required=True)
    circuit_format = ma.fields.String(required=False)


class CombineResultsRequestQuokkaSchema(ma.Schema):
    circuit = ma.fields.Str(required=True)
    subcircuit_results = ma.fields.List(
        ma.fields.Dict(keys=ma.fields.Str(), values=ma.fields.Float()),
        required=True
    )
    cuts = ma.fields.Dict(required=True)
    circuit_format = ma.fields.String(required=False)
