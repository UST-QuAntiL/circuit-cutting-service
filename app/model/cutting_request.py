import marshmallow as ma
import numpy as np
import argschema


class CutCircuitsRequest:
    def __init__(
        self,
        circuit,
        provider,
        qpu,
        credentials,
        shots=1000,
        noise_model=None,
        only_measurement_errors=False,
    ):
        self.circuit = circuit
        self.provider = provider
        self.qpu = qpu
        self.credentials = credentials
        self.shots = shots
        self.noise_model = noise_model
        self.only_measurement_errors = only_measurement_errors


class CutCircuitsRequestSchema(ma.Schema):
    circuit = ma.fields.Str(required=True)
    method = ma.fields.Str(required=True, default='automatic')
    max_subcircuit_width = ma.fields.Int(required=False)
    max_cuts = ma.fields.Int(required=False)
    num_subcircuits = ma.fields.List(ma.fields.Int, required=False)
    subcircuit_vertices = ma.fields.List(ma.fields.List(ma.fields.Int), required=False)


class CombineResultsRequest:
    def __init__(
            self,
            circuit,
            subcircuit_results,
            cuts
    ):
        self.circuit = circuit
        self.subcircuit_results = subcircuit_results
        self.cuts = cuts


class CombineResultsRequestSchema(ma.Schema):
    circuit = ma.fields.Str(required=True)
    subcircuit_results = ma.fields.Dict(required=True,
                                        keys=ma.fields.Int(),
                                        values=ma.fields.Dict(keys=ma.fields.Int(),
                                                              values=argschema.fields.NumpyArray(dtype=np.float)))
    cuts = ma.fields.Dict(required=True)
