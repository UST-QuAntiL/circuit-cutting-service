from flask_smorest import Blueprint

from app import CKT_cutter
from app.model.request_combine_results import (
    CombineResultsRequest,
    CombineResultsRequestQuokkaSchema,
)
from app.model.request_cut_circuits import CutCircuitsRequestSchema, CutCircuitsRequest
from app.model.response_ckt_cut_circuits import CKTCutCircuitsResponseSchema
from app.model.response_combine_results import CombineResultsResponseQuokkaSchema

blp_ckt_cutting = Blueprint(
    "ckt-cutting",
    __name__,
    description="Use the circuit knitting toolbox to cut a quantum circuit",
)


@blp_ckt_cutting.route("/ckt/cutCircuits", methods=["POST"])
@blp_ckt_cutting.arguments(
    CutCircuitsRequestSchema,
    example={
        "circuit": 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[4];\ncreg meas[4];\nh q[0];\ncx q[0],q[1];\ncx q[1],q[2];\ncx q[2],q[3];\nbarrier q[0],q[1],q[2],q[3];\nmeasure q[0] -> meas[0];\nmeasure q[1] -> meas[1];\nmeasure q[2] -> meas[2];\nmeasure q[3] -> meas[3];\n',
        "method": "automatic",
        "max_subcircuit_width": 3,
        "max_num_subcircuits": 2,
        "max_cuts": 2,
        "circuit_format": "openqasm2",
    },
)
@blp_ckt_cutting.response(200, CKTCutCircuitsResponseSchema)
def gate_cut_circuit(json: dict):
    print("request", json)
    result = CKT_cutter.cut_circuit(CutCircuitsRequest(**json))
    print("result", result)
    return result


@blp_ckt_cutting.route("/ctk/combineResultsQuokka", methods=["POST"])
@blp_ckt_cutting.arguments(
    CombineResultsRequestQuokkaSchema,
    example={
        "circuit": 'OPENQASM 2.0;\ninclude "qelib1.inc";\ngate r(param0,param1) q0 { u3(param0,param1 - pi/2,pi/2 - 1.0*param1) q0; }\ngate csdg q0,q1 { p(-pi/4) q0; cx q0,q1; p(pi/4) q1; cx q0,q1; p(-pi/4) q1; }\ngate dcx q0,q1 { cx q0,q1; cx q1,q0; }\ngate xx_plus_yy(param0,param1) q0,q1 { rz(param1) q0; rz(-pi/2) q1; sx q1; rz(pi/2) q1; s q0; cx q1,q0; ry(-0.5*param0) q1; ry(-0.5*param0) q0; cx q1,q0; sdg q0; rz(-pi/2) q1; sxdg q1; rz(pi/2) q1; rz(-1.0*param1) q0; }\nqreg q[4];\ncx q[1],q[0];\ns q[3];\nh q[2];\ntdg q[0];\np(3.4659576145717144) q[3];\nh q[2];\nu(2.837928239342311,1.0860294820363718,1.9538151112148405) q[1];\nr(5.2153760273282765,1.112299858268304) q[2];\ncsdg q[1],q[3];\np(1.6595916488339455) q[0];\nrzz(4.834730724435432) q[3],q[1];\ncz q[2],q[0];\ns q[2];\ndcx q[3],q[1];\nu(1.9716621086763826,3.601792450292146,1.7975767653248311) q[0];\nrx(3.297725929225818) q[0];\nxx_plus_yy(5.946199660330775,2.231187837029287) q[1],q[3];\ny q[2];',
        "subcircuit_results": [
            {
                "001": 0.06201171875,
                "010": 0.1748046875,
                "000": 0.199615478515625,
                "011": 0.563568115234375,
            },
            {
                "000": 0.05902099609375,
                "011": 0.1737060546875,
                "010": 0.566619873046875,
                "001": 0.200653076171875,
            },
            {
                "001": 0.073028564453125,
                "011": 0.203460693359375,
                "000": 0.188079833984375,
                "010": 0.535430908203125,
            },
            {
                "001": 0.185821533203125,
                "000": 0.070220947265625,
                "010": 0.203460693359375,
                "011": 0.540496826171875,
            },
            {
                "011": 0.316680908203125,
                "111": 0.049224853515625,
                "010": 0.05072021484375,
                "000": 0.11358642578125,
                "001": 0.015716552734375,
                "100": 0.017852783203125,
                "110": 0.32440185546875,
                "101": 0.11181640625,
            },
            {
                "101": 0.11199951171875,
                "100": 0.0172119140625,
                "110": 0.3223876953125,
                "001": 0.01629638671875,
                "111": 0.049896240234375,
                "011": 0.316741943359375,
                "010": 0.05084228515625,
                "000": 0.1146240234375,
            },
            {"000": 0.02398681640625, "011": 0.97601318359375},
            {"000": 0.022796630859375, "011": 0.977203369140625},
            {"000": 0.02337646484375, "011": 0.97662353515625},
            {"000": 0.023101806640625, "011": 0.976898193359375},
            {"000": 0.022613525390625, "011": 0.977386474609375},
            {"000": 0.02386474609375, "011": 0.97613525390625},
        ],
        "cuts": {
            "subcircuit_labels": [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
            "coefficients": [
                (0.5, 1),
                (0.5, 1),
                (0.5, 1),
                (-0.5, 1),
                (0.5, 1),
                (-0.5, 1),
            ],
            "metadata": {
                "cuts": [("Gate Cut", 0)],
                "sampling_overhead": 9.0,
                "partition_labels": [0, 1, 0, 1],
                "qubit_map": [(0, 0), (1, 0), (0, 1), (1, 1)],
                "subobservables": {0: "ZZ", 1: "ZZ"},
            },
        },
    },
)
@blp_ckt_cutting.response(200, CombineResultsResponseQuokkaSchema)
def combine_results(json: dict):
    """Recombine the results of the subcircuits from the ckt cut."""
    print("request combine", json)
    return CKT_cutter.reconstruct_result(
        CombineResultsRequest(**json), quokka_format=True
    )
