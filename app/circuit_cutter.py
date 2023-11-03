import codecs
import pickle

import jsonpickle
import numpy as np
from circuit_knitting.cutting import partition_problem, generate_cutting_experiments
from circuit_knitting.cutting.cutqc import (
    generate_summation_terms,
    cut_circuit_wires,
    reconstruct_full_distribution,
)
from circuit_knitting.cutting.cutqc.wire_cutting_evaluation import (
    modify_subcircuit_instance,
    mutate_measurement_basis,
    measure_prob,
)
from qiskit import QuantumCircuit
from qiskit.quantum_info import PauliList
from qiskit.transpiler.passes import RemoveBarriers

from app.model.cutting_request import CutCircuitsRequest, CombineResultsRequest
from app.model.cutting_response import (
    CutCircuitsResponse,
    CombineResultsResponse,
    GateCutCircuitsResponse,
)
from app.partition import get_partitions, get_partition_labels
from app.utils import array_to_counts, counts_to_array, normalize_array


def _create_individual_subcircuits(subcircuits, complete_path_map, num_cuts):
    (
        summation_terms,
        subcircuit_entries,
        subcircuit_instances,
    ) = generate_summation_terms(subcircuits, complete_path_map, num_cuts)
    individual_subcircuits = []
    init_meas_subcircuit_map = {}

    for subcircuit_idx, subcircuit in enumerate(subcircuits):
        _init_meas_subcircuit_map = {}
        subcircuit_instance = subcircuit_instances[subcircuit_idx]
        subcircuit_idx_set = set()
        for init_meas, subcircuit_instance_idx in subcircuit_instance.items():
            if subcircuit_instance_idx not in subcircuit_idx_set:
                modified_subcircuit_instance = modify_subcircuit_instance(
                    subcircuit=subcircuit,
                    init=init_meas[0],
                    meas=tuple(init_meas[1]),
                )
                i = len(individual_subcircuits)
                individual_subcircuits.append(modified_subcircuit_instance)
                _init_meas_subcircuit_map[init_meas] = i
                subcircuit_idx_set.add(subcircuit_instance_idx)
                mutated_meas = mutate_measurement_basis(meas=tuple(init_meas[1]))
                for meas in mutated_meas:
                    key = (init_meas[0], meas)
                    mutated_subcircuit_instance_idx = subcircuit_instance[key]
                    subcircuit_idx_set.add(mutated_subcircuit_instance_idx)
                    _init_meas_subcircuit_map[key] = i

        init_meas_subcircuit_map[subcircuit_idx] = _init_meas_subcircuit_map

    return individual_subcircuits, init_meas_subcircuit_map


def _get_circuit(cutting_request):
    if cutting_request.circuit_format == "openqasm2":
        try:
            circuit = QuantumCircuit.from_qasm_str(cutting_request.circuit)
        except Exception as e:
            return "Provided invalid OpenQASM 2.0 string"
    elif cutting_request.circuit_format == "qiskit":
        circuit = pickle.loads(
            codecs.decode(cutting_request.circuit.encode(), "base64")
        )
    else:
        return 'format must be "openqasm2" or "qiskit"'

    if cutting_request.max_subcircuit_width > circuit.num_qubits:
        raise ValueError(
            f"The subcircuit width ({cutting_request.max_subcircuit_width}) is larger than the width of the original circuit ({circuit.num_qubits})"
        )
    circuit.remove_final_measurements(inplace=True)
    return RemoveBarriers()(circuit)


def cut_circuit(cutting_request: CutCircuitsRequest):
    circuit = _get_circuit(cutting_request)

    if cutting_request.method == "automatic":
        res = cut_circuit_wires(
            circuit,
            method=cutting_request.method,
            max_subcircuit_width=cutting_request.max_subcircuit_width,
            max_cuts=cutting_request.max_cuts,
            num_subcircuits=cutting_request.num_subcircuits,
        )
    elif cutting_request.method == "automatic_gate_cutting":
        res = automatic_gate_cut(
            circuit,
            num_subcircuits=cutting_request.num_subcircuits,
            max_subcircuit_width=cutting_request.max_subcircuit_width,
            max_cuts=cutting_request.max_cuts,
        )
        return GateCutCircuitsResponse(format=cutting_request.circuit_format, **res)
    else:
        res = cut_circuit_wires(
            circuit,
            method=cutting_request.method,
            subcircuit_vertices=cutting_request.subcircuit_vertices,
        )
    individual_subcircuits, init_meas_subcircuit_map = _create_individual_subcircuits(
        res["subcircuits"], res["complete_path_map"], res["num_cuts"]
    )

    for individual_subcircuit in individual_subcircuits:
        individual_subcircuit.measure_all()
    res["individual_subcircuits"] = individual_subcircuits
    res["init_meas_subcircuit_map"] = init_meas_subcircuit_map

    return CutCircuitsResponse(format=cutting_request.circuit_format, **res)


def gate_cut_circuit(cutting_request: CutCircuitsRequest):
    circuit = _get_circuit(cutting_request)

    if cutting_request.method == "automatic_gate_cutting":
        res = automatic_gate_cut(
            circuit,
            num_subcircuits=cutting_request.num_subcircuits,
            max_subcircuit_width=cutting_request.max_subcircuit_width,
            max_cuts=cutting_request.max_cuts,
        )
    else:
        raise ValueError(f"{cutting_request.method} is an unkown cutting method.")

    return GateCutCircuitsResponse(format=cutting_request.circuit_format, **res)


def reconstruct_result(input_dict: CombineResultsRequest, quokka_format=False):
    if input_dict.circuit_format == "openqasm2":
        try:
            circuit = QuantumCircuit.from_qasm_str(input_dict.circuit)
            input_dict.cuts["subcircuits"] = [
                QuantumCircuit.from_qasm_str(qasm)
                for qasm in input_dict.cuts["subcircuits"]
            ]
            input_dict.cuts["individual_subcircuits"] = [
                QuantumCircuit.from_qasm_str(qasm)
                for qasm in input_dict.cuts["individual_subcircuits"]
            ]
        except Exception as e:
            return "Provided invalid OpenQASM 2.0 string"
    elif input_dict.circuit_format == "qiskit":
        circuit = pickle.loads(codecs.decode(input_dict.circuit.encode(), "base64"))
        input_dict.cuts["subcircuits"] = [
            pickle.loads(codecs.decode(subcirc.encode(), "base64"))
            for subcirc in input_dict.cuts["subcircuits"]
        ]
        input_dict.cuts["individual_subcircuits"] = [
            pickle.loads(codecs.decode(ind_circ.encode(), "base64"))
            for ind_circ in input_dict.cuts["individual_subcircuits"]
        ]
    else:
        return 'format must be "openqasm2" or "qiskit"'

    try:
        input_dict.cuts["complete_path_map"] = jsonpickle.decode(
            input_dict.cuts["complete_path_map"], keys=True
        )
        input_dict.cuts["init_meas_subcircuit_map"] = jsonpickle.decode(
            input_dict.cuts["init_meas_subcircuit_map"], keys=True
        )
    except Exception as e:
        # TODO refine exception
        return "The quantum circuit has to be provided as an OpenQASM 2.0 String"

    normalize = input_dict.unnormalized_results

    subcircuit_results = process_subcircuit_results(
        input_dict.subcircuit_results,
        input_dict.cuts["init_meas_subcircuit_map"],
        input_dict.cuts["subcircuits"],
        input_dict.cuts["complete_path_map"],
        input_dict.cuts["num_cuts"],
        quokka_format,
        normalize,
    )

    res = reconstruct_full_distribution(circuit, subcircuit_results, input_dict.cuts)
    if input_dict.shot_scaling_factor is not None:
        res = res * input_dict.shot_scaling_factor

    if quokka_format:
        res = array_to_counts(res)

    return CombineResultsResponse(result=res)


def automatic_gate_cut(circuit, num_subcircuits, max_subcircuit_width, max_cuts):
    partitions, _ = get_partitions(circuit, num_subcircuits[0], max_subcircuit_width)
    partition_labels = get_partition_labels(partitions)
    partitioned_problem = partition_problem(
        circuit=circuit,
        partition_labels=partition_labels,
        observables=PauliList(["Z" * circuit.num_qubits]),
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

    return {
        "individual_subcircuits": individual_subcircuits,
        "subcircuit_labels": subcircuit_labels,
        "coefficients": coefficients,
        "subobservables": partitioned_problem.subobservables,
    }


def convert_subcircuit_results(subcircuit_results, subcircuits):
    converted_result = {}
    for circ_fragment, frag_results in subcircuit_results.items():
        converted_result[circ_fragment] = {}
        for sub_circ, counts_dict in frag_results.items():
            converted_result[circ_fragment][sub_circ] = counts_to_array(
                counts_dict, subcircuits[circ_fragment].num_qubits
            )
    return converted_result


def process_subcircuit_results(
    subcircuit_results,
    init_meas_subcircuit_map,
    subcircuits,
    complete_path_map,
    num_cuts,
    quokka_format=False,
    normalize=False,
):
    (
        summation_terms,
        subcircuit_entries,
        subcircuit_instances,
    ) = generate_summation_terms(subcircuits, complete_path_map, num_cuts)

    results = {}
    for circuit_fragment_idx, circuit_fragment in enumerate(subcircuits):
        subcircuit_instance = subcircuit_instances[circuit_fragment_idx]
        fragment_results = []
        for init_meas, subcircuit_instance_idx in subcircuit_instance.items():
            res = subcircuit_results[
                init_meas_subcircuit_map[circuit_fragment_idx][init_meas]
            ]
            if quokka_format:
                res = counts_to_array(res, circuit_fragment.num_qubits)
            if normalize:
                res = normalize_array(res)
            measured_prob = measure_prob(unmeasured_prob=res, meas=init_meas[1])
            fragment_results.append(measured_prob)
        results[circuit_fragment_idx] = fragment_results
    return results
