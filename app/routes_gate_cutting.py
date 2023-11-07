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


from flask_smorest import Blueprint

from app import gate_cutter
from app.model.cutting_request import (
    CutCircuitsRequestSchema,
    CutCircuitsRequest,
)
from app.model.cutting_response import (
    GateCutCircuitsResponseSchema,
)

blp_gate_cutting = Blueprint(
    "gate-cutting",
    __name__,
    description="Use gate-cutting to cut a quantum circuit",
)


@blp_gate_cutting.route("/gate-cutting/cutCircuits", methods=["POST"])
@blp_gate_cutting.arguments(
    CutCircuitsRequestSchema,
    example={
        "circuit": 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[4];\ncreg meas[4];\nh q[0];\ncx q[0],q[1];\ncx q[1],q[2];\ncx q[2],q[3];\nbarrier q[0],q[1],q[2],q[3];\nmeasure q[0] -> meas[0];\nmeasure q[1] -> meas[1];\nmeasure q[2] -> meas[2];\nmeasure q[3] -> meas[3];\n',
        "method": "automatic_gate_cutting",
        "max_subcircuit_width": 3,
        "max_num_subcircuits": 2,
        "max_cuts": 2,
        "circuit_format": "openqasm2",
    },
)
@blp_gate_cutting.response(200, GateCutCircuitsResponseSchema)
def gate_cut_circuit(json: dict):
    print("request", json)
    result = gate_cutter.gate_cut_circuit(CutCircuitsRequest(**json))
    print("result", result)
    return result
