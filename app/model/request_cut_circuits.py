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
        max_num_subcircuits=None,
        subcircuit_vertices=None,
        circuit_format="openqasm2",
    ):
        self.circuit = circuit
        self.method = method
        self.max_subcircuit_width = max_subcircuit_width
        self.max_cuts = max_cuts
        self.num_subcircuits = (
            list(range(2, max_num_subcircuits + 1))
            if max_num_subcircuits is not None
            else [2]
        )
        self.subcircuit_vertices = subcircuit_vertices
        self.circuit_format = circuit_format.lower()


class CutCircuitsRequestSchema(ma.Schema):
    circuit = ma.fields.Str(required=True)
    method = ma.fields.Str(required=True, default="automatic")
    max_subcircuit_width = ma.fields.Int(required=False)
    max_cuts = ma.fields.Int(required=False)
    max_num_subcircuits = ma.fields.Int(required=False)
    subcircuit_vertices = ma.fields.List(ma.fields.List(ma.fields.Int), required=False)
    circuit_format = ma.fields.String(required=False)
