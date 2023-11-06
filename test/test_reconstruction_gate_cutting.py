import math
import unittest

import numpy as np
from circuit_knitting.cutting import (
    partition_problem,
    generate_cutting_experiments,
)
from qiskit.circuit.library import EfficientSU2
from qiskit.quantum_info import PauliList
from qiskit_aer.primitives import Sampler

from app.gate_cutting_reconstruct_distribution import reconstruct_distribution
from app.utils import counts_to_array


def _generate_reconstruction_test(num_qubits=4, partition_label=None, reps=2):

    if partition_label is None:
        partition_label = ("A" * (num_qubits // 2)) + ("B" * math.ceil(num_qubits / 2))

    circuit = EfficientSU2(
        num_qubits=num_qubits,
        reps=reps,
        entanglement="linear",
        su2_gates=["ry"],
    )

    circuit = circuit.decompose()

    params = [np.random.random() * 2 * np.pi for _ in circuit.parameters]
    circuit = circuit.bind_parameters(params)

    observables = PauliList(["Z" * num_qubits])

    partitioned_problem = partition_problem(
        circuit=circuit, partition_labels=partition_label, observables=observables
    )
    subcircuits = partitioned_problem.subcircuits
    subobservables = partitioned_problem.subobservables
    bases = partitioned_problem.bases

    subexperiments, coefficients = generate_cutting_experiments(
        circuits=subcircuits, observables=subobservables, num_samples=np.inf
    )
    # Set up a Qiskit Aer Sampler primitive for each circuit partition
    samplers = {
        label: Sampler(run_options={"shots": 2 ** 15})
        for label in subexperiments.keys()
    }

    # Retrieve results from each partition's subexperiments
    results = {
        label: sampler.run(subexperiments[label]).result()
        for label, sampler in samplers.items()
    }

    sampler_exact = Sampler(run_options={"shots": None})
    qc_meas = circuit.measure_all(inplace=False)
    result_exact = sampler_exact.run(qc_meas).result()

    exact_experiment = result_exact.experiments[0]
    exact_distribution = counts_to_array(
        exact_experiment["quasi_dists"],
        exact_experiment["metadata"]["simulator_metadata"]["num_qubits"],
    )

    reconstructed_dist = reconstruct_distribution(
        results,
        coefficients,
        subobservables,
    )
    return exact_distribution, reconstructed_dist


class ReconstructionTestCase(unittest.TestCase):
    def test_generate_test_data(self):
        num_qubits = 4
        exact_distribution, reconstructed_dist = _generate_reconstruction_test(
            num_qubits, "AABB"
        )
        self.assertTrue(
            np.allclose(exact_distribution, reconstructed_dist, atol=2 ** (-num_qubits))
        )

    def test_generate_test_data_2(self):
        num_qubits = 4
        exact_distribution, reconstructed_dist = _generate_reconstruction_test(
            num_qubits, "ABBA", reps=1
        )
        self.assertTrue(
            np.allclose(exact_distribution, reconstructed_dist, atol=2 ** (-num_qubits))
        )
