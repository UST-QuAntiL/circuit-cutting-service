import codecs
import json
import pickle
import unittest
from collections import defaultdict

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.random import random_circuit
from qiskit.quantum_info import SparsePauliOp
from qiskit_aer.primitives import Sampler, EstimatorV2

from app import create_app
from app.CKT_cutter import automatic_cut, reconstruct_distribution
from app.utils import counts_to_array, replace_str_index


class CutFindingTestCase(unittest.TestCase):
    def test_automatic_cut(self):
        circuit = random_circuit(7, 6, max_operands=2, seed=1242)
        result = automatic_cut(circuit, 4)
        self.assertTrue(len(result["individual_subcircuits"]) > 0)
        self.assertTrue(
            len(result["individual_subcircuits"]) == len(result["subcircuit_labels"])
        )

    def test_automatic_cut_exception(self):
        circuit = random_circuit(7, 6, max_operands=2, seed=1242)
        self.assertRaises(Exception, automatic_cut, circuit, 4, 0)


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        self.app_context.pop()

    def test_automatic_cutting(self):
        response = self.client.post(
            "/ckt/cutCircuits",
            data=json.dumps(
                {
                    "circuit": 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[4];\ncreg meas[4];\nh q[0];\ncx q[0],q[1];\ncx q[1],q[2];\ncx q[2],q[3];\nbarrier q[0],q[1],q[2],q[3];\nmeasure q[0] -> meas[0];\nmeasure q[1] -> meas[1];\nmeasure q[2] -> meas[2];\nmeasure q[3] -> meas[3];\n',
                    "method": "automatic",
                    "max_subcircuit_width": 2,
                    "max_num_subcircuits": 2,
                    "max_cuts": 2,
                    "circuit_format": "openqasm2",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        print(response.get_json())

    def test_automatic_cutting_2(self):
        circuit = random_circuit(7, 6, max_operands=2, seed=1242)
        pickle_bytes = codecs.encode(pickle.dumps(circuit), "base64").decode()
        response = self.client.post(
            "/ckt/cutCircuits",
            data=json.dumps(
                {
                    "circuit": pickle_bytes,
                    "method": "automatic",
                    "max_subcircuit_width": 4,
                    "max_num_subcircuits": 2,
                    "max_cuts": 2,
                    "circuit_format": "qiskit",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        print(response.get_json())

    def test_reconstruction(self):
        circuit = random_circuit(7, 6, max_operands=2, seed=1242)
        cut_result = automatic_cut(circuit, 4)

        individual_subcircuits = cut_result["individual_subcircuits"]
        subcircuit_labels = cut_result["subcircuit_labels"]
        coefficients = cut_result["coefficients"]
        metadata = cut_result["metadata"]
        qubit_map = metadata["qubit_map"]
        subobservables = metadata["subobservables"]

        sampler = Sampler(run_options={"shots": 2 ** 17})
        # Retrieve results from each partition's subexperiments
        results = sampler.run(individual_subcircuits).result()

        results_dict = defaultdict(list)
        for label, res in zip(subcircuit_labels, results.quasi_dists):
            results_dict[label].append(res)

        reconstructed_counts = reconstruct_distribution(
            results_dict, coefficients, qubit_map, subobservables
        )

        sampler_exact = Sampler(run_options={"shots": None})
        qc_meas = circuit.measure_all(inplace=False)
        result_exact = sampler_exact.run(qc_meas).result()

        exact_distribution = counts_to_array(
            result_exact.quasi_dists[0],
            result_exact.metadata[0]["simulator_metadata"]["num_qubits"],
        )
        reconstructed_dist = counts_to_array(reconstructed_counts, circuit.num_qubits)

        self.assertTrue(
            np.allclose(exact_distribution, reconstructed_dist, atol=0.01),
            msg=f"\nExact distribution: {exact_distribution}\nReconstruced distribution: {reconstructed_dist}\nDiff: {np.abs(exact_distribution- reconstructed_dist)}",
        )

    def test_reconstruction_2(self):

        circuit = QuantumCircuit(4)
        circuit.x(0)
        circuit.cx(0, 1)
        circuit.cx(1, 2)
        circuit.cx(2, 3)
        circuit.cx(3, 2)
        circuit.cx(2, 1)
        circuit.cx(1, 0)

        exact_expval_list, actual_expval_list, observable = get_expals(circuit, 2 ** 12)

        self.assertTrue(
            np.allclose(exact_expval_list, actual_expval_list, atol=0.1),
            msg=f"\nEObservables: {observable.paulis}\nExact expectations: {exact_expval_list}\nReconstruced expectations: {actual_expval_list}",
        )

    def test_reconstruction_3(self):

        circuit = QuantumCircuit(4)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.cx(1, 2)
        circuit.cx(2, 3)
        circuit.cx(3, 2)
        circuit.cx(2, 1)
        circuit.cx(1, 0)

        exact_expval_list, actual_expval_list, observable = get_expals(circuit, 2 ** 12)

        self.assertTrue(
            np.allclose(exact_expval_list, actual_expval_list, atol=0.1),
            msg=f"\nEObservables: {observable.paulis}\nExact expectations: {exact_expval_list}\nReconstruced expectations: {actual_expval_list}",
        )

    def test_reconstruction_4(self):

        circuit = QuantumCircuit(4)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.cx(1, 2)
        circuit.cx(2, 3)
        circuit.cx(3, 2)
        circuit.cx(2, 1)
        circuit.cx(1, 0)

        exact_expval_list, actual_expval_list, observable = get_expals(circuit, 2 ** 12)

        self.assertTrue(
            np.allclose(exact_expval_list, actual_expval_list, atol=0.1),
            msg=f"\nEObservables: {observable.paulis}\nExact expectations: {exact_expval_list}\nReconstruced expectations: {actual_expval_list}",
        )

    def test_reconstruction_5(self):

        circuit = QuantumCircuit(5)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.cx(1, 2)
        circuit.cx(1, 0)
        circuit.cx(2, 0)
        circuit.cx(2, 3)
        circuit.cx(3, 4)
        circuit.cx(2, 4)

        exact_expval_list, actual_expval_list, observable = get_expals(circuit, 2 ** 12)

        self.assertTrue(
            np.allclose(exact_expval_list, actual_expval_list, atol=0.1),
            msg=f"\nEObservables: {observable.paulis}\nExact expectations: {exact_expval_list}\nReconstruced expectations: {actual_expval_list}",
        )

    def test_reconstruction_6(self):

        circuit = QuantumCircuit(4)
        circuit.x(0)
        circuit.cx(0, 1)
        circuit.cx(1, 2)
        circuit.cx(3, 2)
        circuit.cx(2, 1)
        circuit.cx(1, 0)

        exact_expval_list, actual_expval_list, observable = get_expals(circuit, 2 ** 12)

        self.assertTrue(
            np.allclose(exact_expval_list, actual_expval_list, atol=0.1),
            msg=f"\nEObservables: {observable.paulis}\nExact expectations: {exact_expval_list}\nReconstruced expectations: {actual_expval_list}",
        )


def get_expals(circuit, shots):
    n_qubits = circuit.num_qubits
    i_string = "I" * n_qubits

    observable = SparsePauliOp(
        [replace_str_index(i_string, i, "Z") for i in range(n_qubits - 1, -1, -1)]
    )

    qubits_per_subcircuit = (n_qubits // 2) + (n_qubits % 2)
    optimization_seed = 111

    cut_result = automatic_cut(
        circuit, qubits_per_subcircuit, optimization_seed=optimization_seed
    )

    individual_subcircuits = cut_result["individual_subcircuits"]
    subcircuit_labels = cut_result["subcircuit_labels"]
    coefficients = cut_result["coefficients"]
    metadata = cut_result["metadata"]
    qubit_map = metadata["qubit_map"]
    subobservables = metadata["subobservables"]

    sampler = Sampler(run_options={"shots": shots})
    # Retrieve results from each partition's subexperiments
    results = sampler.run(individual_subcircuits).result()

    results_dict = defaultdict(list)
    for label, res in zip(subcircuit_labels, results.quasi_dists):
        results_dict[label].append(res)

    reconstructed_counts = reconstruct_distribution(
        results_dict, coefficients, qubit_map, subobservables
    )

    estimator = EstimatorV2()

    actual_expval_list = []
    exact_expval_list = []
    for i in range(n_qubits):
        actual_expval = 0
        for meas, count in reconstructed_counts.items():
            actual_expval += (-1) ** ((meas >> i) % 2) * count
        actual_expval_list.append(actual_expval)
        exact_expval = estimator.run([(circuit, observable.paulis[i])]).result()
        exact_expval_list.append(exact_expval[0].data.evs)

    return exact_expval_list, actual_expval_list, observable
