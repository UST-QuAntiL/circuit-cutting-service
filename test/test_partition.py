import unittest
import numpy as np
from qiskit.circuit.library import EfficientSU2

from app.partition import get_partitions, get_partition_labels


class PartitionTestCase(unittest.TestCase):
    def test_get_partitions(self):
        num_qubits = 7
        num_partitions = 2
        circuit = EfficientSU2(
            num_qubits=num_qubits,
            reps=2,
            entanglement="full",
            su2_gates=["ry"],
        )
        circuit = circuit.decompose()

        params = [(np.pi * i) / 16 for i in range(len(circuit.parameters))]
        circuit = circuit.bind_parameters(params)
        partitions, partition_sizes = get_partitions(
            circuit,
            num_partitions=num_partitions,
            max_partition_size=int(np.ceil(num_qubits / 2)),
        )
        print(partitions)
        print(partition_sizes)
        self.assertEquals(len(partition_sizes), num_partitions)
        self.assertTrue(
            all([size <= np.ceil(num_qubits / 2) for size in partition_sizes])
        )

    def test_get_partition_labels(self):
        partitions = {0: 0, 1: 1, 2: 1, 3: 0, 4: 1, 5: 1, 6: 0}
        expected_partition_labels = "0110110"
        partition_labels = get_partition_labels(partitions)
        self.assertEqual(partition_labels, expected_partition_labels)
