# ******************************************************************************
#  Copyright (c) 2023 University of Stuttgart
#
#  See the NOTICE file(s) distributed with this work for additional
#  information regarding copyright ownership.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ******************************************************************************

import codecs
import pickle

import jsonpickle
import marshmallow as ma
from qiskit import qasm3, qasm2


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
            self.subcircuits = [qasm2.dumps(circ) for circ in subcircuits]
            self.individual_subcircuits = [
                qasm2.dumps(circ) for circ in individual_subcircuits
            ]
        elif format == "openqasm3":
            self.subcircuits = [qasm3.dumps(circ) for circ in subcircuits]
            self.individual_subcircuits = [
                qasm3.dumps(circ) for circ in individual_subcircuits
            ]
        elif format == "qiskit":
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
