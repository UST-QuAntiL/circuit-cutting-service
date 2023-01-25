import time
import unittest
import os, sys
import json

import jsonpickle
import numpy as np
from circuit_knitting_toolbox.circuit_cutting.wire_cutting import (
    cut_circuit_wires,
    evaluate_subcircuits,
    reconstruct_full_distribution,
)
from circuit_knitting_toolbox.circuit_cutting.wire_cutting.wire_cutting_evaluation import (
    run_subcircuits,
)
from qiskit import QuantumCircuit, assemble, transpile
from qiskit.circuit.library import EfficientSU2
from qiskit.providers import JobError, JobTimeoutError
from qiskit.providers.jobstatus import JOB_FINAL_STATES
from qiskit_aer import AerSimulator

from app.circuit_cutter import _create_individual_subcircuits
from app.utils import array_to_counts

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from app import create_app


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


def generate_su2_test(num_qubits):
    circuit = EfficientSU2(
        num_qubits=num_qubits,
        reps=2,
        entanglement="linear",
        su2_gates=["ry"],
    )

    circuit = circuit.decompose()

    params = [(np.pi * i) / 16 for i in range(len(circuit.parameters))]
    circuit = circuit.bind_parameters(params)
    cuts = cut_circuit_wires(
        circuit=circuit,
        method="automatic",
        max_subcircuit_width=5,
        max_cuts=2,
        num_subcircuits=[2],
    )
    subcircuit_instance_probs_test = evaluate_subcircuits(cuts)
    expected = reconstruct_full_distribution(
        circuit, subcircuit_instance_probs_test, cuts
    )
    individual_subcircuits, init_meas_subcircuit_map = _create_individual_subcircuits(
        cuts["subcircuits"], cuts["complete_path_map"], cuts["num_cuts"]
    )

    subcircuit_instance_probabilities = run_subcircuits(individual_subcircuits)

    cuts["subcircuits"] = [sc.qasm() for sc in cuts["subcircuits"]]
    cuts["complete_path_map"] = jsonpickle.encode(cuts["complete_path_map"], keys=True)
    cuts["individual_subcircuits"] = [sc.qasm() for sc in individual_subcircuits]
    cuts["init_meas_subcircuit_map"] = jsonpickle.encode(
        init_meas_subcircuit_map, keys=True
    )
    return circuit, subcircuit_instance_probabilities, cuts, expected


def convert_subcircuit_probabilites(subcircuit_probabilities):
    if isinstance(subcircuit_probabilities, dict):
        converted_result = {}
        for circ_fragment, frag_results in subcircuit_probabilities.items():
            converted_result[circ_fragment] = {}
            for sub_circ, probability in frag_results.items():
                converted_result[circ_fragment][sub_circ] = array_to_counts(probability)
        return converted_result
    else:
        return [
            array_to_counts(probability) for probability in subcircuit_probabilities
        ]


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        self.app_context.pop()

    def test_reconstruction(self):
        circuit, subcircuit_instance_probabilities, cuts, expected = generate_su2_test(
            8
        )
        print(expected)
        response = self.client.post(
            "/combineResults",
            data=json.dumps(
                {
                    "circuit": circuit.qasm(),
                    "subcircuit_results": subcircuit_instance_probabilities,
                    "cuts": cuts,
                },
                cls=NumpyEncoder,
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        print(response.get_json())
        self.assertTrue((expected == np.array(response.get_json()["result"])).all())

    def test_reconstruction_quokka(self):
        circuit, subcircuit_instance_probabilities, cuts, expected = generate_su2_test(
            8
        )
        subcircuit_instance_probabilities = convert_subcircuit_probabilites(
            subcircuit_instance_probabilities
        )

        response = self.client.post(
            "/combineResultsQuokka",
            data=json.dumps(
                {
                    "circuit": circuit.qasm(),
                    "subcircuit_results": subcircuit_instance_probabilities,
                    "cuts": cuts,
                },
                cls=NumpyEncoder,
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        print(response.get_json())

    def test_based_on_cutting_request(self):
        cutting_response_json = {'classical_cost': 64,
         'complete_path_map': '{"json://{\\"py/object\\": \\"qiskit.circuit.quantumregister.Qubit\\", \\"_index\\": 0, \\"_register\\": {\\"py/object\\": \\"qiskit.circuit.quantumregister.QuantumRegister\\", \\"py/state\\": {\\"py/tuple\\": [\\"q\\", 4, -6491360347166058145, \\"QuantumRegister(4, \'q\')\\", [{\\"py/id\\": 1}, {\\"py/object\\": \\"qiskit.circuit.quantumregister.Qubit\\", \\"_index\\": 1, \\"_register\\": {\\"py/id\\": 2}, \\"_hash\\": -1236161107715967576, \\"_repr\\": \\"Qubit(QuantumRegister(4, \'q\'), 1)\\"}, {\\"py/object\\": \\"qiskit.circuit.quantumregister.Qubit\\", \\"_index\\": 2, \\"_register\\": {\\"py/id\\": 2}, \\"_hash\\": -6129235136688663942, \\"_repr\\": \\"Qubit(QuantumRegister(4, \'q\'), 2)\\"}, {\\"py/object\\": \\"qiskit.circuit.quantumregister.Qubit\\", \\"_index\\": 3, \\"_register\\": {\\"py/id\\": 2}, \\"_hash\\": 378405619413334483, \\"_repr\\": \\"Qubit(QuantumRegister(4, \'q\'), 3)\\"}]]}}, \\"_hash\\": -3345444480833597873, \\"_repr\\": \\"Qubit(QuantumRegister(4, \'q\'), 0)\\"}": [{"subcircuit_idx": 0, "subcircuit_qubit": {"py/object": "qiskit.circuit.quantumregister.Qubit", "_index": 0, "_register": {"py/object": "qiskit.circuit.quantumregister.QuantumRegister", "py/state": {"py/tuple": ["q", 3, 2800071064791006349, "QuantumRegister(3, \'q\')", [{"py/id": 9}, {"py/object": "qiskit.circuit.quantumregister.Qubit", "_index": 1, "_register": {"py/id": 10}, "_hash": -199321695443646933, "_repr": "Qubit(QuantumRegister(3, \'q\'), 1)"}, {"py/object": "qiskit.circuit.quantumregister.Qubit", "_index": 2, "_register": {"py/id": 10}, "_hash": -5092395724416343299, "_repr": "Qubit(QuantumRegister(3, \'q\'), 2)"}]]}}, "_hash": -2308605068561277230, "_repr": "Qubit(QuantumRegister(3, \'q\'), 0)"}}], "json://{\\"py/id\\": 4}": [{"subcircuit_idx": 0, "subcircuit_qubit": {"py/object": "qiskit.circuit.quantumregister.Qubit", "_index": 1, "_register": {"py/object": "qiskit.circuit.quantumregister.QuantumRegister", "py/state": {"py/tuple": ["q", 3, 2800071064791006349, "QuantumRegister(3, \'q\')", [{"py/object": "qiskit.circuit.quantumregister.Qubit", "_index": 0, "_register": {"py/id": 17}, "_hash": -2308605068561277230, "_repr": "Qubit(QuantumRegister(3, \'q\'), 0)"}, {"py/id": 16}, {"py/object": "qiskit.circuit.quantumregister.Qubit", "_index": 2, "_register": {"py/id": 17}, "_hash": -5092395724416343299, "_repr": "Qubit(QuantumRegister(3, \'q\'), 2)"}]]}}, "_hash": -199321695443646933, "_repr": "Qubit(QuantumRegister(3, \'q\'), 1)"}}], "json://{\\"py/id\\": 5}": [{"subcircuit_idx": 0, "subcircuit_qubit": {"py/object": "qiskit.circuit.quantumregister.Qubit", "_index": 2, "_register": {"py/object": "qiskit.circuit.quantumregister.QuantumRegister", "py/state": {"py/tuple": ["q", 3, 2800071064791006349, "QuantumRegister(3, \'q\')", [{"py/object": "qiskit.circuit.quantumregister.Qubit", "_index": 0, "_register": {"py/id": 24}, "_hash": -2308605068561277230, "_repr": "Qubit(QuantumRegister(3, \'q\'), 0)"}, {"py/object": "qiskit.circuit.quantumregister.Qubit", "_index": 1, "_register": {"py/id": 24}, "_hash": -199321695443646933, "_repr": "Qubit(QuantumRegister(3, \'q\'), 1)"}, {"py/id": 23}]]}}, "_hash": -5092395724416343299, "_repr": "Qubit(QuantumRegister(3, \'q\'), 2)"}}, {"subcircuit_idx": 1, "subcircuit_qubit": {"py/object": "qiskit.circuit.quantumregister.Qubit", "_index": 0, "_register": {"py/object": "qiskit.circuit.quantumregister.QuantumRegister", "py/state": {"py/tuple": ["q", 2, -3707569691310992076, "QuantumRegister(2, \'q\')", [{"py/id": 29}, {"py/object": "qiskit.circuit.quantumregister.Qubit", "_index": 1, "_register": {"py/id": 30}, "_hash": -7284043906015339508, "_repr": "Qubit(QuantumRegister(2, \'q\'), 1)"}]]}}, "_hash": 4655059411592213683, "_repr": "Qubit(QuantumRegister(2, \'q\'), 0)"}}], "json://{\\"py/id\\": 6}": [{"subcircuit_idx": 1, "subcircuit_qubit": {"py/object": "qiskit.circuit.quantumregister.Qubit", "_index": 1, "_register": {"py/object": "qiskit.circuit.quantumregister.QuantumRegister", "py/state": {"py/tuple": ["q", 2, -3707569691310992076, "QuantumRegister(2, \'q\')", [{"py/object": "qiskit.circuit.quantumregister.Qubit", "_index": 0, "_register": {"py/id": 36}, "_hash": 4655059411592213683, "_repr": "Qubit(QuantumRegister(2, \'q\'), 0)"}, {"py/id": 35}]]}}, "_hash": -7284043906015339508, "_repr": "Qubit(QuantumRegister(2, \'q\'), 1)"}}]}',
         'counter': {'0': {'O': 1, 'd': 3, 'depth': 3, 'effective': 2, 'rho': 0, 'size': 3},
                     '1': {'O': 0, 'd': 2, 'depth': 1, 'effective': 2, 'rho': 1, 'size': 1}},
         'individual_subcircuits': [
             'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[3];\nh q[0];\ncx q[0],q[1];\ncx q[1],q[2];\n',
             'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[3];\nh q[0];\ncx q[0],q[1];\ncx q[1],q[2];\nh q[2];\n',
             'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[3];\nh q[0];\ncx q[0],q[1];\ncx q[1],q[2];\nsdg q[2];\nh q[2];\n',
             'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncx q[0],q[1];\n',
             'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\nx q[0];\ncx q[0],q[1];\n',
             'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\nh q[0];\ncx q[0],q[1];\n',
             'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\nh q[0];\ns q[0];\ncx q[0],q[1];\n'],
         'init_meas_subcircuit_map': '{"0": {"((\'zero\', \'zero\', \'zero\'), (\'comp\', \'comp\', \'I\'))": 0, "((\'zero\', \'zero\', \'zero\'), (\'comp\', \'comp\', \'Z\'))": 0, "((\'zero\', \'zero\', \'zero\'), (\'comp\', \'comp\', \'X\'))": 1, "((\'zero\', \'zero\', \'zero\'), (\'comp\', \'comp\', \'Y\'))": 2}, "1": {"((\'zero\', \'zero\'), (\'comp\', \'comp\'))": 3, "((\'one\', \'zero\'), (\'comp\', \'comp\'))": 4, "((\'plus\', \'zero\'), (\'comp\', \'comp\'))": 5, "((\'plusI\', \'zero\'), (\'comp\', \'comp\'))": 6}}',
         'max_subcircuit_width': 3, 'num_cuts': 1,
         'subcircuits': ['OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[3];\nh q[0];\ncx q[0],q[1];\ncx q[1],q[2];\n',
                         'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncx q[0],q[1];\n']}

        circuits = [QuantumCircuit.from_qasm_str(circ_string) for circ_string in cutting_response_json['individual_subcircuits']]
        [circ.measure_all() for circ in circuits]
        ibm_qpu = AerSimulator()
        transpiled_circuits = [transpile(c, backend=ibm_qpu) for c in circuits]

        def execute(transpiled_circuit, shots, backend):
            """Execute the quantum circuit."""
            try:
                job = backend.run(assemble(transpiled_circuit, shots=shots))
                sleep_timer = 0.5
                job_status = job.status()
                while job_status not in JOB_FINAL_STATES:
                    print("The execution is still running")
                    time.sleep(sleep_timer)
                    job_status = job.status()
                    if sleep_timer < 10:
                        sleep_timer = sleep_timer + 1

                return job.result().get_counts()
            except (JobError, JobTimeoutError):
                return None

        exec_results = execute(transpiled_circuits, 1000, ibm_qpu)
        print(exec_results)

        response = self.client.post(
            "/combineResultsQuokka",
            data=json.dumps(
                {
                    "circuit": 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[4];\ncreg meas[4];\nh q[0];\ncx q[0],q[1];\ncx q[1],q[2];\ncx q[2],q[3];\nbarrier q[0],q[1],q[2],q[3];\nmeasure q[0] -> meas[0];\nmeasure q[1] -> meas[1];\nmeasure q[2] -> meas[2];\nmeasure q[3] -> meas[3];\n',
                    "subcircuit_results": exec_results,

                    "cuts": {
                        "individual_subcircuits": cutting_response_json['individual_subcircuits'],
                        "subcircuits": cutting_response_json['subcircuits'],
                        "complete_path_map": cutting_response_json['complete_path_map'],
                        "init_meas_subcircuit_map": cutting_response_json['init_meas_subcircuit_map'],
                        "num_cuts": cutting_response_json['num_cuts'],

                    },
                    "circuit_format": "openqasm2"
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        print(response.get_json())




