import codecs
import pickle

import jsonpickle
from circuit_knitting_toolbox.circuit_cutting.wire_cutting import (
    cut_circuit_wires,
    reconstruct_full_distribution,
)
from qiskit import QuantumCircuit

from app.model.cutting_request import CutCircuitsRequest, CombineResultsRequest
from app.model.cutting_response import CutCircuitsResponse, CombineResultsResponse
from app.utils import array_to_counts, counts_to_array


def cut_circuit(cuttingRequest: CutCircuitsRequest):
    if cuttingRequest.circuit_format == "openqasm2":
        try:
            circuit = QuantumCircuit.from_qasm_str(cuttingRequest.circuit)
        except Exception as e:
            return "Provided invalid OpenQASM 2.0 string"
    elif cuttingRequest.circuit_format == "qiskit":
        circuit = pickle.loads(codecs.decode(cuttingRequest.circuit.encode(), "base64"))
    else:
        return 'format must be "openqasm2" or "qiskit"'

    print(circuit)
    circuit.remove_final_measurements(inplace=True)

    if cuttingRequest.method == "automatic":
        res = cut_circuit_wires(
            circuit,
            method=cuttingRequest.method,
            max_subcircuit_width=cuttingRequest.max_subcircuit_width,
            max_cuts=cuttingRequest.max_cuts,
            num_subcircuits=cuttingRequest.num_subcircuits,
        )
    else:
        res = cut_circuit_wires(
            circuit,
            method=cuttingRequest.method,
            subcircuit_vertices=cuttingRequest.subcircuit_vertices,
        )

    return CutCircuitsResponse(format=cuttingRequest.circuit_format, **res)


def reconstruct_result(input_dict: CombineResultsRequest, quokka_format=False):
    if input_dict.circuit_format == "openqasm2":
        try:
            circuit = QuantumCircuit.from_qasm_str(input_dict.circuit)
            input_dict.cuts["subcircuits"] = [
                QuantumCircuit.from_qasm_str(qasm)
                for qasm in input_dict.cuts["subcircuits"]
            ]
        except Exception as e:
            return "Provided invalid OpenQASM 2.0 string"
    elif input_dict.circuit_format == "qiskit":
        circuit = pickle.loads(codecs.decode(input_dict.circuit.encode(), "base64"))
        input_dict.cuts["subcircuits"] = [
            QuantumCircuit.from_qasm_str(qasm)
            for qasm in input_dict.cuts["subcircuits"]
        ]
    else:
        return 'format must be "openqasm2" or "qiskit"'

    try:
        input_dict.cuts["complete_path_map"] = jsonpickle.decode(
            input_dict.cuts["complete_path_map"], keys=True
        )
    except Exception as e:
        # TODO refine exception
        return "The quantum circuit has to be provided as an OpenQASM 2.0 String"

    if quokka_format:
        input_dict.subcircuit_results = convert_subcircuit_results(
            input_dict.subcircuit_results, input_dict.cuts["subcircuits"]
        )

    res = reconstruct_full_distribution(
        circuit, input_dict.subcircuit_results, input_dict.cuts
    )
    if quokka_format:
        res = array_to_counts(res)

    return CombineResultsResponse(result=res)


def convert_subcircuit_results(subcircuit_results, subcircuits):
    converted_result = {}
    for circ_fragment, frag_results in subcircuit_results.items():
        converted_result[circ_fragment] = {}
        for sub_circ, counts_dict in frag_results.items():
            converted_result[circ_fragment][sub_circ] = counts_to_array(
                counts_dict, subcircuits[circ_fragment].num_qubits
            )
    return converted_result
