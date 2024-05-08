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

from __future__ import annotations

import math
from collections import defaultdict, Counter
from typing import Hashable, Sequence

import numpy as np
from circuit_knitting.cutting.cutting_reconstruction import _outcome_to_int
from circuit_knitting.cutting.qpd import WeightType
from circuit_knitting.utils.bitwise import bit_count
from qiskit.primitives import SamplerResult

from app.utils import (
    product_dicts,
    shift_bits_by_index,
    find_character_in_string,
)


def _process_outcome_distribution(
    num_meas_bits: int, outcome: int | str, /
) -> np.typing.NDArray[np.float64]:
    """
    Process a single outcome of a QPD experiment

    Args:
        num_meas_bits: The number of measured qubits in the result
        outcome: The outcome of the classical bits

    Returns:
        A tuple with the QPD factor in the measurement outcome
    """
    outcome = _outcome_to_int(outcome)
    # remove outcome of mid-circuit measurements
    meas_outcomes = outcome & ((1 << num_meas_bits) - 1)
    qpd_outcomes = outcome >> num_meas_bits

    # qpd_factor will be -1 or +1, depending on the overall parity of qpd
    # measurements, thereby it accounts for mid-circuit measurements
    qpd_factor = 1 - 2 * (bit_count(qpd_outcomes) & 1)

    return qpd_factor, meas_outcomes


def reconstruct_distribution(
    results: dict[Hashable, SamplerResult] | dict[Hashable, list],
    coefficients: Sequence[tuple[float, WeightType]],
    partition_labels: str,
) -> dict[int, float]:
    r"""
    Reconstruct the probability distribution from the results of the sub-experiments.

    Args:
        results: The results from running the cutting subexperiments. If the cut circuit
            was not partitioned between qubits and run separately, this argument should be
            a :class:`~qiskit.primitives.SamplerResult` instance or a dictionary mapping
            a single partition to the results. If the circuit was partitioned and its
            pieces were run separately, this argument should be a dictionary mapping partition labels
            to the results from each partition's subexperiments.

            The subexperiment results are expected to be ordered in the same way the subexperiments
            are ordered in the output of :func:`.generate_cutting_experiments` -- one result for every
            sample and observable, as shown below. The Qiskit Sampler primitive will return the results
            in the same order the experiments are submitted, so users who do not use :func:`.generate_cutting_experiments`
            to generate their experiments should take care to order their subexperiments as follows before submitting them
            to the sampler primitive:

            :math:`[sample_{0}observable_{0}, \ldots, sample_{0}observable_{N-1}, sample_{1}observable_{0}, \ldots, sample_{M-1}observable_{N-1}]`

        coefficients: A sequence containing the coefficient associated with each unique subexperiment. Each element is a tuple
            containing the coefficient (a ``float``) together with its :class:`.WeightType`, which denotes
            how the value was generated. The contribution from each subexperiment will be multiplied by
            its corresponding coefficient, and the resulting terms will be summed to obtain the reconstructed expectation value.

        partition_labels: Describing the cut of the circuit


    Returns:
        The probability distribution as dict
    """
    result_dict = defaultdict(float)

    labels = {*partition_labels}

    qubits = Counter(partition_labels)

    label_index_lists = {
        label: list(find_character_in_string(partition_labels, label))
        for label in labels
    }

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

    return result_dict
