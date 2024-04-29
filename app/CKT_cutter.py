import numpy as np
from circuit_knitting.cutting import (
    OptimizationParameters,
    DeviceConstraints,
    find_cuts,
    cut_wires,
    expand_observables,
    partition_problem,
    generate_cutting_experiments,
    partition_circuit_qubits,
)
from circuit_knitting.cutting.qpd import TwoQubitQPDGate
from circuit_knitting.utils.transforms import (
    _partition_labels_from_circuit,
    separate_circuit,
)
from qiskit.quantum_info import SparsePauliOp

from app.model.request_cut_circuits import CutCircuitsRequest
from app.model.response_ckt_cut_circuits import CKTCutCircuitsResponse
from app.wire_cutter import _get_circuit


def cut_circuit(cutting_request: CutCircuitsRequest):
    circuit = _get_circuit(cutting_request)

    if cutting_request.method == "automatic":
        res = automatic_cut(
            circuit,
            qubits_per_subcircuit=cutting_request.max_subcircuit_width,
            max_cuts=cutting_request.max_cuts,
        )
    else:
        raise ValueError(f"{cutting_request.method} is an unkown cutting method.")

    return CKTCutCircuitsResponse(format=cutting_request.circuit_format, **res)


def automatic_cut(circuit, qubits_per_subcircuit, max_cuts=None):
    # Specify settings for the cut-finding optimizer
    optimization_settings = OptimizationParameters(seed=111)

    # Specify the size of the QPUs available
    device_constraints = DeviceConstraints(qubits_per_subcircuit=qubits_per_subcircuit)

    try:
        cut_circuit, metadata = find_cuts(
            circuit, optimization_settings, device_constraints
        )
    except ValueError:
        cut_circuit, metadata = find_cuts(
            circuit.decompose(), optimization_settings, device_constraints
        )

    if max_cuts is not None:
        if len(metadata["cuts"]) > max_cuts:
            raise Exception(
                "More than the specified maximum number of cuts are required"
            )

    observable = SparsePauliOp(["Z" * circuit.num_qubits])

    qc_w_ancilla = cut_wires(cut_circuit)
    observables_expanded = expand_observables(observable.paulis, circuit, qc_w_ancilla)
    partitioned_problem = partition_problem(
        circuit=qc_w_ancilla, observables=observables_expanded
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

    partition_labels = _partition_labels_from_circuit(
        qc_w_ancilla,
        ignore=lambda inst: isinstance(inst.operation, TwoQubitQPDGate),
    )

    qpd_circuit = partition_circuit_qubits(qc_w_ancilla, partition_labels)
    qpd_circuit_dx = qpd_circuit.decompose(TwoQubitQPDGate)
    separated_circs = separate_circuit(qpd_circuit_dx, partition_labels)

    custom_metadata = {}
    custom_metadata.update(**metadata)
    custom_metadata["partition_labels"] = partition_labels
    custom_metadata["qubit_map"] = separated_circs.qubit_map

    return {
        "individual_subcircuits": individual_subcircuits,
        "subcircuit_labels": subcircuit_labels,
        "coefficients": coefficients,
        "metadata": custom_metadata,
    }
