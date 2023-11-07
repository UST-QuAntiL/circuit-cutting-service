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
    CombineResultsRequest,
    CombineResultsRequestQuokkaSchema,
)
from app.model.cutting_response import (
    GateCutCircuitsResponseSchema,
    CombineResultsResponseQuokkaSchema,
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


@blp_gate_cutting.route("/gate-cutting/combineResultsQuokka", methods=["POST"])
@blp_gate_cutting.arguments(
    CombineResultsRequestQuokkaSchema,
    example={
        "circuit": 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[6];\nry(3.65201816844744) q[0];\nry(1.86914714247146) q[1];\ncx q[0],q[1];\nry(4.29668327383582) q[0];\nry(3.78320230781079) q[2];\ncx q[1],q[2];\nry(3.9348411572113) q[1];\nry(2.56591926281996) q[3];\ncx q[2],q[3];\nry(3.98698245166312) q[2];\nry(2.77957484387872) q[4];\ncx q[3],q[4];\nry(2.77046779740946) q[3];\nry(4.34760986661033) q[5];\ncx q[4],q[5];\nry(1.67983539831451) q[4];\nry(4.89050090588416) q[5];\n',
        "subcircuit_results": [
            {
                "001": 0.019775390625,
                "110": 0.131103515625,
                "100": 0.05712890625,
                "101": 0.10791015625,
                "111": 0.138427734375,
                "011": 0.251953125,
                "000": 0.022216796875,
                "010": 0.271484375,
            },
            {
                "101": 0.106689453125,
                "000": 0.0224609375,
                "010": 0.258544921875,
                "111": 0.14599609375,
                "011": 0.259033203125,
                "001": 0.0283203125,
                "110": 0.123046875,
                "100": 0.055908203125,
            },
            {
                "1001": 0.0029296875,
                "0000": 0.012939453125,
                "1000": 0.008056640625,
                "0110": 0.0810546875,
                "1100": 0.001708984375,
                "0100": 0.054443359375,
                "0011": 0.02294921875,
                "0001": 0.019775390625,
                "0010": 0.013916015625,
                "1110": 0.04736328125,
                "1010": 0.24365234375,
                "1011": 0.24267578125,
                "0101": 0.109375,
                "1111": 0.042236328125,
                "0111": 0.096923828125,
            },
            {
                "1000": 0.007080078125,
                "1001": 0.003173828125,
                "0010": 0.012939453125,
                "0000": 0.011962890625,
                "0101": 0.100341796875,
                "0110": 0.075927734375,
                "0011": 0.018310546875,
                "0001": 0.021728515625,
                "1100": 0.00146484375,
                "0100": 0.052734375,
                "1110": 0.048583984375,
                "1010": 0.25341796875,
                "1011": 0.2470703125,
                "1101": 0.00048828125,
                "1111": 0.04833984375,
                "0111": 0.096435546875,
            },
            {
                "011": 0.128662109375,
                "111": 0.291015625,
                "001": 0.041259765625,
                "110": 0.228271484375,
                "100": 0.03857421875,
                "000": 0.0380859375,
                "010": 0.143310546875,
                "101": 0.0908203125,
            },
            {
                "001": 0.0078125,
                "100": 0.072265625,
                "110": 0.00146484375,
                "010": 0.382568359375,
                "101": 0.13232421875,
                "111": 0.0068359375,
                "011": 0.396728515625,
            },
            {
                "000": 0.0029296875,
                "010": 0.00341796875,
                "001": 0.013671875,
                "110": 0.22119140625,
                "100": 0.239501953125,
                "111": 0.0927734375,
                "011": 0.021484375,
                "101": 0.405029296875,
            },
            {
                "000": 0.001708984375,
                "010": 0.003662109375,
                "001": 0.014892578125,
                "110": 0.224609375,
                "100": 0.234375,
                "111": 0.090576171875,
                "011": 0.023681640625,
                "101": 0.406494140625,
            },
            {
                "111": 0.001953125,
                "011": 0.004150390625,
                "101": 0.131591796875,
                "000": 0.00146484375,
                "010": 0.007568359375,
                "001": 0.002197265625,
                "110": 0.36669921875,
                "100": 0.484375,
            },
            {
                "000": 0.001953125,
                "100": 0.006103515625,
                "110": 0.0693359375,
                "001": 0.0283203125,
                "111": 0.19091796875,
                "011": 0.034423828125,
                "101": 0.6689453125,
            },
            {
                "0010": 0.0009765625,
                "0000": 0.00244140625,
                "1011": 0.00244140625,
                "1010": 0.002197265625,
                "1001": 0.00439453125,
                "1111": 0.043212890625,
                "1101": 0.052490234375,
                "0001": 0.01318359375,
                "0011": 0.016357421875,
                "0111": 0.053466796875,
                "1110": 0.0283203125,
                "0100": 0.150390625,
                "1100": 0.093017578125,
                "0101": 0.35205078125,
                "0110": 0.18505859375,
            },
            {
                "1011": 0.00244140625,
                "0000": 0.001953125,
                "0010": 0.00146484375,
                "1010": 0.003173828125,
                "1111": 0.04345703125,
                "1101": 0.052001953125,
                "1001": 0.00390625,
                "0011": 0.018310546875,
                "0001": 0.014404296875,
                "0110": 0.188720703125,
                "1100": 0.09521484375,
                "0100": 0.1494140625,
                "1110": 0.027587890625,
                "0111": 0.054931640625,
                "0101": 0.343017578125,
            },
        ],
        "cuts": {
            "subcircuit_labels": [
                "A",
                "A",
                "A",
                "A",
                "A",
                "A",
                "B",
                "B",
                "B",
                "B",
                "B",
                "B",
            ],
            "coefficients": [
                (0.5, 1),
                (0.5, 1),
                (0.5, 1),
                (-0.5, 1),
                (0.5, 1),
                (-0.5, 1),
            ],
            "partition_label": "AAABBB",
        },
    },
)
@blp_gate_cutting.response(200, CombineResultsResponseQuokkaSchema)
def combine_results(json: dict):
    """Recombine the results of the subcircuits from the gate cut."""
    print("request combine", json)
    return gate_cutter.reconstruct_result(
        CombineResultsRequest(**json), quokka_format=True
    )
