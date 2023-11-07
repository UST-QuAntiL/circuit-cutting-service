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
from app.wire_cutter import _get_circuit, automatic_gate_cut
from app.model.cutting_request import CutCircuitsRequest
from app.model.cutting_response import GateCutCircuitsResponse


def gate_cut_circuit(cutting_request: CutCircuitsRequest):
    circuit = _get_circuit(cutting_request)

    if cutting_request.method == "automatic_gate_cutting":
        res = automatic_gate_cut(
            circuit,
            num_subcircuits=cutting_request.num_subcircuits,
            max_subcircuit_width=cutting_request.max_subcircuit_width,
            max_cuts=cutting_request.max_cuts,
        )
    else:
        raise ValueError(f"{cutting_request.method} is an unkown cutting method.")

    return GateCutCircuitsResponse(format=cutting_request.circuit_format, **res)
