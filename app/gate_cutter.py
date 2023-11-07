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
from collections import defaultdict

import numpy as np
from circuit_knitting.cutting import partition_problem, generate_cutting_experiments
from qiskit.quantum_info import PauliList

from app.gate_cutting_reconstruct_distribution import reconstruct_distribution
from app.model.cutting_request import CutCircuitsRequest, CombineResultsRequest
from app.model.cutting_response import GateCutCircuitsResponse, CombineResultsResponse
from app.partition import get_partitions, get_partition_labels
from app.utils import counts_to_array
from app.wire_cutter import _get_circuit


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
        "partition_labels": partition_labels,
    }


def reconstruct_result(input_dict: CombineResultsRequest, quokka_format=False):
    subcircuit_results_dict = defaultdict(list)
    for label, res in zip(
        input_dict.cuts["subcircuit_labels"], input_dict.subcircuit_results
    ):
        subcircuit_results_dict[label].append(res)

    result = reconstruct_distribution(
        subcircuit_results_dict,
        input_dict.cuts["coefficients"],
        input_dict.cuts["partition_labels"],
    )
    num_qubits = len(input_dict.cuts["partition_labels"])

    if not quokka_format:
        result = counts_to_array(result, num_qubits)
    else:
        result = {
            "{0:b}".format(key).zfill(num_qubits): val for key, val in result.items()
        }

    return CombineResultsResponse(result=result)
