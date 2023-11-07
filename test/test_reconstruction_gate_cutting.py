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

    observables = PauliList(["Z" * num_qubits])

    partitioned_problem = partition_problem(
        circuit=circuit, partition_labels=partition_labels, observables=observables
    )
    subcircuits = partitioned_problem.subcircuits
    subobservables = partitioned_problem.subobservables
    bases = partitioned_problem.bases

    subexperiments, coefficients = generate_cutting_experiments(
        circuits=subcircuits, observables=subobservables, num_samples=np.inf
    )
    # Set up a Qiskit Aer Sampler primitive for each circuit partition
    samplers = {
        label: Sampler(run_options={"shots": 2 ** 12})
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

    reconstructed_counts = reconstruct_distribution(
        results, coefficients, partition_labels
    )
    reconstructed_dist = counts_to_array(reconstructed_counts, num_qubits)
    return exact_distribution, reconstructed_dist


class ReconstructionTestCase(unittest.TestCase):
    def test_generate_test_data(self):
        num_qubits = 4
        exact_distribution, reconstructed_dist = _generate_reconstruction_test(
            num_qubits, "AABB"
        )
        self.assertTrue(
            np.allclose(exact_distribution, reconstructed_dist, atol=0.025),
            msg=f"\nExact distribution: {exact_distribution}\nReconstruced distribution: {reconstructed_dist}\nDiff: {np.abs(exact_distribution- reconstructed_dist)}",
        )

    def test_generate_test_data_2(self):
        num_qubits = 4
        exact_distribution, reconstructed_dist = _generate_reconstruction_test(
            num_qubits, "ABBA", reps=1
        )
        self.assertTrue(
            np.allclose(exact_distribution, reconstructed_dist, atol=0.025),
            msg=f"\nExact distribution: {exact_distribution}\nReconstruced distribution: {reconstructed_dist}\nDiff: {np.abs(exact_distribution- reconstructed_dist)}",
        )

    def test_generate_test_data_3(self):
        num_qubits = 5
        exact_distribution, reconstructed_dist = _generate_reconstruction_test(
            num_qubits, "ABBCD", reps=1
        )
        self.assertTrue(
            np.allclose(exact_distribution, reconstructed_dist, atol=0.025),
            msg=f"\nExact distribution: {exact_distribution}\nReconstruced distribution: {reconstructed_dist}\nDiff: {np.abs(exact_distribution- reconstructed_dist)}",
        )

    def test_generate_test_data_4(self):
        num_qubits = 8
        exact_distribution, reconstructed_dist = _generate_reconstruction_test(
            num_qubits, "AAAABBBB"
        )
        self.assertTrue(
            np.allclose(exact_distribution, reconstructed_dist, atol=0.025),
            msg=f"\nExact distribution: {exact_distribution}\nReconstruced distribution: {reconstructed_dist}\nDiff: {np.abs(exact_distribution- reconstructed_dist)}",
        )
