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

import marshmallow as ma
from qiskit import qasm3, qasm2


class GateCutCircuitsResponse:
    def __init__(
        self,
        format,
        individual_subcircuits,
        subcircuit_labels,
        coefficients,
        partition_labels,
    ):
        super().__init__()
        if format == "openqasm2":
            self.individual_subcircuits = [
                qasm2.dumps(circ) for circ in individual_subcircuits
            ]
        elif format == "openqasm3":
            self.individual_subcircuits = [
                qasm3.dumps(circ) for circ in individual_subcircuits
            ]
        elif format == "qiskit":
            self.individual_subcircuits = [
                codecs.encode(pickle.dumps(circ), "base64").decode()
                for circ in individual_subcircuits
            ]

        self.subcircuit_labels = subcircuit_labels
        self.coefficients = [(c, w.value) for c, w in coefficients]
        self.partition_labels = partition_labels

    def to_json(self):
        json_execution_response = {
            "individual_subcircuits": self.individual_subcircuits,
            "subcircuit_labels": self.subcircuit_labels,
            "coefficients": self.coefficients,
            "partition_labels": self.partition_labels,
        }
        return json_execution_response


class GateCutCircuitsResponseSchema(ma.Schema):
    max_subcircuit_width = ma.fields.Int()
    individual_subcircuits = ma.fields.List(ma.fields.Str())
    subcircuit_labels = ma.fields.List(ma.fields.Str())
    coefficients = ma.fields.List(ma.fields.Tuple((ma.fields.Float, ma.fields.Int)))
    partition_labels = ma.fields.Str()
