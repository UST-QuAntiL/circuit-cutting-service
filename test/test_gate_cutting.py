import json
import math
import os
import sys
import unittest
from collections import defaultdict

import numpy as np
from circuit_knitting.cutting import partition_problem, generate_cutting_experiments
from qiskit.circuit.library import EfficientSU2
from qiskit.quantum_info import PauliList
from qiskit_aer.primitives import Sampler

from app.gate_cutting_reconstruct_distribution import reconstruct_distribution
from app.utils import counts_to_array
from test.test_reconstruction import NumpyEncoder

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from app import create_app


def _generate_reconstruction_test(num_qubits=4, partition_labels=None, reps=2):

    if partition_labels is None:
        partition_labels = ("A" * (num_qubits // 2)) + ("B" * math.ceil(num_qubits / 2))

    circuit = EfficientSU2(
        num_qubits=num_qubits,
        reps=reps,
        entanglement="linear",
        su2_gates=["ry"],
    )

    circuit = circuit.decompose()

    params = [np.random.random() * 2 * np.pi for _ in circuit.parameters]
    circuit = circuit.bind_parameters(params)

    partitioned_problem = partition_problem(
        circuit=circuit,
        partition_labels=partition_labels,
        observables=PauliList(["Z" * circuit.num_qubits]),
    )
    subexperiments, coefficients = generate_cutting_experiments(
        circuits=partitioned_problem.subcircuits,
        observables=partitioned_problem.subobservables,
        num_samples=np.inf,
    )

    individual_subcircuits = []
    subcircuit_labels = []

    for label, circs in subexperiments.items():
        for sub_circ in circs:
            individual_subcircuits.append(sub_circ)
            subcircuit_labels.append(label)

    sampler = Sampler(run_options={"shots": 2 ** 12})
    # Retrieve results from each partition's subexperiments
    results = sampler.run(individual_subcircuits).result()

    results_dict = defaultdict(list)
    for label, res in zip(subcircuit_labels, results.quasi_dists):
        results_dict[label].append(res)

    reconstructed_counts = reconstruct_distribution(
        results_dict, coefficients, partition_labels
    )

    reconstructed_dist = counts_to_array(reconstructed_counts, num_qubits)

    results = [
        {"{0:b}".format(key): val for key, val in res.items()}
        for res in results.quasi_dists
    ]

    return (
        circuit,
        individual_subcircuits,
        subcircuit_labels,
        reconstructed_dist,
        results,
        coefficients,
        partition_labels,
    )


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        self.app_context.pop()

    def test_automatic_gate_cut(self):
        response = self.client.post(
            "gate-cutting/cutCircuits",
            data=json.dumps(
                {
                    "circuit": 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[4];\ncreg meas[4];\nh q[0];\ncx q[0],q[1];\ncx q[1],q[2];\ncx q[2],q[3];\nmeasure q[0] -> meas[0];\nmeasure q[1] -> meas[1];\nmeasure q[2] -> meas[2];\nmeasure q[3] -> meas[3];\n',
                    "method": "automatic_gate_cutting",
                    "max_subcircuit_width": 2,
                    "max_num_subcircuits": 2,
                    "max_cuts": 2,
                    "circuit_format": "openqasm2",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        print(response.get_json())

    def test_reconstruction(self):
        (
            circuit,
            subcircuits,
            subcircuit_labels,
            expected,
            results,
            coefficients,
            partition_label,
        ) = _generate_reconstruction_test(6, reps=1)

        response = self.client.post(
            "/gate-cutting/combineResultsQuokka",
            data=json.dumps(
                {
                    "circuit": circuit.qasm(),
                    "subcircuit_results": results,
                    "cuts": {
                        "subcircuit_labels": subcircuit_labels,
                        "coefficients": [(c, w.value) for c, w in coefficients],
                        "partition_label": partition_label,
                    },
                },
                cls=NumpyEncoder,
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        print(response.get_json())
        actual = counts_to_array(
            {int(key, 2): val for key, val in response.get_json()["result"].items()}, 6
        )
        self.assertTrue((expected == actual).all())
