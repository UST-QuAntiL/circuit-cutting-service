import kahypar
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dagdependency
from qiskit.dagcircuit import DAGDependency

PATH_KAHYPAR_CONFIG = "./../kahypar.ini"


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
            edge_vector.append(qarg.index)

    return kahypar.Hypergraph(n, e, index_vector, edge_vector, k)


def dag_to_wire_gate_hypergraph(dag: DAGDependency, k=2):
    n = 0
    e = -1
    index_vector = []
    edge_vector = []

    for node in dag.topological_nodes():
        # Get arguments for classical control (if any)
        print(dag.predecessors(node.node_id))
        if len(node.qargs) < 2:
            continue
        e += 1
        index_vector.append(len(edge_vector))
        for qarg in node.qargs:
            edge_vector.append(qarg.index)

    return kahypar.Hypergraph(n, e, index_vector, edge_vector, k)


def get_partitions(circuit_or_dag, num_partitions, max_partition_size, verbose=False):
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
