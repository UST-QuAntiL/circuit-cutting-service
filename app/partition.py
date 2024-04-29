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

import kahypar
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dagdependency
from qiskit.dagcircuit import DAGDependency
from pathlib import Path

PATH_KAHYPAR_CONFIG = str((Path(__file__).parent.parent / "kahypar.ini").resolve())


def dag_to_hypergraph(dag: DAGDependency, k=2):
    n = len(dag.qubits)
    e = -1
    index_vector = []
    edge_vector = []

    for node in dag.topological_nodes():
        # Get arguments for classical control (if any)
        if len(node.qargs) < 2:
            continue
        e += 1
        index_vector.append(len(edge_vector))
        for qarg in node.qargs:
            edge_vector.append(qarg._index)

    return kahypar.Hypergraph(n, e, index_vector, edge_vector, k)


def get_partitions(circuit_or_dag, num_partitions, max_partition_size):
    if isinstance(circuit_or_dag, QuantumCircuit):
        dag = circuit_to_dagdependency(circuit_or_dag)
    elif isinstance(circuit_or_dag, DAGDependency):
        dag = circuit_or_dag
    else:
        raise TypeError("Input has to be either a QuantumCircuit or DAGDependency")
    hypergraph = dag_to_hypergraph(dag, num_partitions)
    context = kahypar.Context()
    context.loadINIconfiguration(PATH_KAHYPAR_CONFIG)
    context.setK(num_partitions)
    if isinstance(max_partition_size, int):
        max_partition_size = [max_partition_size for _ in range(num_partitions)]
    elif not isinstance(max_partition_size, list):
        raise TypeError("max_partition_size must be an integer or a list of integers")
    context.setCustomTargetBlockWeights(max_partition_size)
    kahypar.partition(hypergraph, context)

    partitions = {n: hypergraph.blockID(n) for n in hypergraph.nodes()}
    partition_sizes = [hypergraph.blockSize(p) for p in range(num_partitions)]

    return partitions, partition_sizes


def get_two_dummy_partitions(circuit: QuantumCircuit):
    n = circuit.num_qubits
    partitions = {}
    for i in range(n // 2):
        partitions[i] = 0
    for i in range(n // 2, n):
        partitions[i] = 1
    return partitions


def get_partition_labels(partitions):
    return "".join([str(val) for _, val in sorted(partitions.items())])
