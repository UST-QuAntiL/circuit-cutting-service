import unittest
import os, sys
import json

import jsonpickle
import numpy as np
from circuit_knitting_toolbox.circuit_cutting.wire_cutting import (
    cut_circuit_wires,
    evaluate_subcircuits, reconstruct_full_distribution,
)
from circuit_knitting_toolbox.circuit_cutting.wire_cutting.wire_cutting_evaluation import run_subcircuits
from qiskit.circuit.library import EfficientSU2

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
    expected = reconstruct_full_distribution(circuit, subcircuit_instance_probs_test, cuts)
    individual_subcircuits, init_meas_subcircuit_map = _create_individual_subcircuits(cuts["subcircuits"],
                                                                                      cuts["complete_path_map"],
                                                                                      cuts["num_cuts"])

    subcircuit_instance_probabilities = run_subcircuits(individual_subcircuits)

    cuts["subcircuits"] = [sc.qasm() for sc in cuts["subcircuits"]]
    cuts["complete_path_map"] = jsonpickle.encode(cuts["complete_path_map"], keys=True)
    cuts['individual_subcircuits'] = [sc.qasm() for sc in individual_subcircuits]
    cuts['init_meas_subcircuit_map'] = jsonpickle.encode(init_meas_subcircuit_map, keys=True)
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
        return [array_to_counts(probability) for probability in subcircuit_probabilities]


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        self.app_context.pop()

    def test_reconstruction(self):
        circuit, subcircuit_instance_probabilities, cuts, expected = generate_su2_test(8)
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
        self.assertTrue((expected == np.array(response.get_json()['result'])).all())

    def test_reconstruction_quokka(self):
        circuit, subcircuit_instance_probabilities, cuts, expected = generate_su2_test(8)
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
