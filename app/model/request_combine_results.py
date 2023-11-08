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


class CombineResultsRequest:
    def __init__(
        self,
        circuit,
        subcircuit_results,
        cuts,
        circuit_format="openqasm2",
        unnormalized_results=False,
        shot_scaling_factor=None,
    ):
        self.circuit = circuit
        self.subcircuit_results = subcircuit_results
        self.cuts = cuts
        self.circuit_format = circuit_format
        self.unnormalized_results = unnormalized_results
        self.shot_scaling_factor = shot_scaling_factor


class CombineResultsRequestSchema(ma.Schema):
    circuit = ma.fields.Str(required=True)
    subcircuit_results = ma.fields.List(
        argschema.fields.NumpyArray(dtype=np.float), required=True
    )
    cuts = ma.fields.Dict(required=True)
    circuit_format = ma.fields.String(required=False)
    unnormalized_results = ma.fields.Boolean(required=False)
    shot_scaling_factor = ma.fields.Int(required=False)


class CombineResultsRequestQuokkaSchema(ma.Schema):
    circuit = ma.fields.Str(required=True)
    subcircuit_results = ma.fields.List(
        ma.fields.Dict(keys=ma.fields.Str(), values=ma.fields.Float()), required=True
    )
    cuts = ma.fields.Dict(required=True)
    circuit_format = ma.fields.String(required=False)
    unnormalized_results = ma.fields.Boolean(required=False)
    shot_scaling_factor = ma.fields.Int(required=False)
