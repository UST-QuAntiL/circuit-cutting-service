from flask_smorest import Blueprint

from app import CKT_cutter
from app.model.request_cut_circuits import CutCircuitsRequestSchema, CutCircuitsRequest
from app.model.response_ckt_cut_circuits import CKTCutCircuitsResponseSchema

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
        "method": "automatic_gate_cutting",
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
