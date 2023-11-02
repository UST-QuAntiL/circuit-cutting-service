import unittest
import numpy as np
from qiskit.circuit.library import EfficientSU2

from app.partition import get_partitions


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
