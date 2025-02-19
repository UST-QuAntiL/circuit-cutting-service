from qiskit import QuantumCircuit
from qiskit.circuit.random import random_circuit


def circuit_1():
    num_qubits = 7
    circuit = random_circuit(num_qubits, 6, max_operands=2, seed=1242)
    return circuit


def circuit_2():
    circuit = QuantumCircuit(4)
    circuit.x(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.cx(2, 3)
    circuit.cx(3, 2)
    circuit.cx(2, 1)
    circuit.cx(1, 0)
    return circuit


def circuit_3():
    circuit = QuantumCircuit(4)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.cx(2, 3)
    circuit.cx(3, 2)
    circuit.cx(2, 1)
    circuit.cx(1, 0)
    return circuit


def circuit_4():
    circuit = QuantumCircuit(5)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.cx(1, 0)
    circuit.cx(2, 0)
    circuit.cx(2, 3)
    circuit.cx(3, 4)
    circuit.cx(2, 4)
    return circuit


def circuit_5():
    circuit = QuantumCircuit(4)
    circuit.x(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.cx(3, 2)
    circuit.cx(2, 1)
    circuit.cx(1, 0)
    return circuit
