from __future__ import annotations

import math
from collections import defaultdict
from typing import Hashable, Sequence

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
from circuit_knitting.cutting.qpd import TwoQubitQPDGate, WeightType
from circuit_knitting.utils.transforms import (
    _partition_labels_from_circuit,
    separate_circuit,
)
from qiskit.primitives import SamplerResult
from qiskit.quantum_info import SparsePauliOp

from app.gate_cutting_reconstruct_distribution import _process_outcome_distribution
from app.model.request_combine_results import CombineResultsRequest
from app.model.request_cut_circuits import CutCircuitsRequest
from app.model.response_ckt_cut_circuits import CKTCutCircuitsResponse
from app.model.response_combine_results import CombineResultsResponse
from app.utils import (
    product_dicts,
    shift_bits_by_index,
    find_character_in_string,
    remove_bits,
    counts_to_array,
)
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


def automatic_cut(
    circuit, qubits_per_subcircuit, max_cuts=None, optimization_seed=None
):
    # Specify settings for the cut-finding optimizer
    optimization_settings = OptimizationParameters(seed=optimization_seed)

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

    subobservables = {}

    for partition, subobs in partitioned_problem.subobservables.items():
        subobservables[partition] = subobs.to_labels()[0]

    custom_metadata["subobservables"] = subobservables

    return {
        "individual_subcircuits": individual_subcircuits,
        "subcircuit_labels": subcircuit_labels,
        "coefficients": coefficients,
        "metadata": custom_metadata,
    }


def reconstruct_distribution(
    results: dict[Hashable, SamplerResult] | dict[Hashable, list],
    coefficients: Sequence[tuple[float, WeightType]],
    qubit_map: Sequence[tuple[int, int]],
    subobservables: dict[str, str],
) -> dict[int, float]:
    result_dict = defaultdict(float)
    labels = []
    # ensure order of the labels
    for label, _ in qubit_map:
        if label not in labels:
            labels.append(label)

    if isinstance(labels[0], int):
        subobservables = {int(key): val for key, val in subobservables.items()}
        results = {int(key): val for key, val in results.items()}

    qubits = {key: val.count("Z") for key, val in subobservables.items()}
    observable = "".join([subobservables[l] for l in reversed(labels)])

    label_index_lists = defaultdict(list)
    for ind, (label, _) in enumerate(qubit_map):
        label_index_lists[label].append(ind)

    if isinstance(results, dict) and isinstance(
        results[next(iter(labels))], SamplerResult
    ):
        results = {
            label: [results[label].quasi_dists[i] for i in range(len(coefficients))]
            for label in labels
        }

    # Reconstruct the probability distribution
    for i, coeff in enumerate(coefficients):

        coeff_result_dict = {}

        for label in labels:
            coeff_result_dict[label] = defaultdict(float)
            quasi_probs = results[label][i]
            for outcome, quasi_prob in quasi_probs.items():
                qpd_factor, meas_outcomes = _process_outcome_distribution(
                    qubits[label], outcome
                )
                coeff_result_dict[label][meas_outcomes] += qpd_factor * quasi_prob

        for meas_keys, quasi_prob_vals in product_dicts(
            *list(coeff_result_dict.values())
        ).items():
            combined_meas = 0
            for meas, label in zip(meas_keys, coeff_result_dict.keys()):
                combined_meas += shift_bits_by_index(meas, label_index_lists[label])
            result_dict[combined_meas] += coeff[0] * math.prod(quasi_prob_vals)

    if not "I" in observable:
        return result_dict

    result_dict_traced_out = defaultdict(float)
    qubits_to_trace_out = []
    for label, sub_obs in subobservables.items():
        qubits_to_trace_out_in_sub_obs = list(find_character_in_string(sub_obs, "I"))
        qubits_to_trace_out_in_sub_obs = [
            len(sub_obs) - i - 1 for i in qubits_to_trace_out_in_sub_obs
        ]
        for qubit_in_sub_obs in qubits_to_trace_out_in_sub_obs:
            qubit = label_index_lists[label][qubit_in_sub_obs]
            qubits_to_trace_out.append(qubit)

    for meas, val in result_dict.items():
        meas_traced_out = remove_bits(meas, qubits_to_trace_out)
        result_dict_traced_out[meas_traced_out] += val

    return result_dict_traced_out


def reconstruct_result(input_dict: CombineResultsRequest, quokka_format=False):
    subcircuit_results_dict = defaultdict(list)
    for label, res in zip(
        input_dict.cuts["subcircuit_labels"], input_dict.subcircuit_results
    ):
        subcircuit_results_dict[label].append(res)

    result = reconstruct_distribution(
        subcircuit_results_dict,
        input_dict.cuts["coefficients"],
        input_dict.cuts["metadata"]["qubit_map"],
        input_dict.cuts["metadata"]["subobservables"],
    )
    num_qubits = 0
    for key, val in input_dict.cuts["metadata"]["subobservables"].items():
        num_qubits += val.count("Z")
    if not quokka_format:
        result = counts_to_array(result, num_qubits)
    else:
        result = {
            "{0:b}".format(key).zfill(num_qubits): val for key, val in result.items()
        }

    return CombineResultsResponse(result=result)
