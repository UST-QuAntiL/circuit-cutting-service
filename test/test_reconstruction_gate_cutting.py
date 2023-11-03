import unittest
from collections import defaultdict

import numpy as np
from circuit_knitting.cutting import reconstruct_expectation_values
from qiskit.circuit.library import EfficientSU2
from qiskit_aer.primitives import Sampler

from app import create_app
from app.circuit_cutter import automatic_gate_cut


def _generate_test_data(num_qubits):

    circuit = EfficientSU2(
        num_qubits=num_qubits,
        reps=2,
        entanglement="linear",
        su2_gates=["ry"],
    )

    circuit = circuit.decompose()

    params = [(np.pi * i) / 16 for i in range(len(circuit.parameters))]
    circuit = circuit.bind_parameters(params)
    res = automatic_gate_cut(
        circuit,
        num_subcircuits=[2],
        max_subcircuit_width=int(np.ceil(num_qubits / 2)),
        max_cuts=10,
    )

    individual_subcircuits = res["individual_subcircuits"]
    subcircuit_labels = res["subcircuit_labels"]
    coefficients = res["coefficients"]
    subobservables = res["subobservables"]

    labels = set(subcircuit_labels)

    # Set up a Qiskit Aer Sampler primitive for each circuit partition
    samplers = {label: Sampler(run_options={"shots": 2 ** 12}) for label in labels}

    subexperiments = defaultdict(list)
    for l, c in zip(subcircuit_labels, individual_subcircuits):
        subexperiments[l].append(c)

    # Retrieve results from each partition's subexperiments
    results = {
        label: sampler.run(subexperiments[label]).result()
        for label, sampler in samplers.items()
    }

    reconstructed_expvals = reconstruct_expectation_values(
        results,
        coefficients,
        subobservables,
    )
    return reconstructed_expvals, results, res


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        self.app_context.pop()

    def test_reconstruction(self):
        reconstructed_expvals, results, res = _generate_test_data(8)
