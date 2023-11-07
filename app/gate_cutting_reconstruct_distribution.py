from __future__ import annotations

import math
from collections import defaultdict, Counter
from typing import Hashable, Sequence

import numpy as np
from circuit_knitting.cutting.cutting_decomposition import decompose_observables
from circuit_knitting.cutting.cutting_reconstruction import _outcome_to_int
from circuit_knitting.cutting.qpd import WeightType
from circuit_knitting.utils.bitwise import bit_count
from circuit_knitting.utils.observable_grouping import (
    ObservableCollection,
)
from qiskit.primitives import SamplerResult
from qiskit.quantum_info import PauliList

from app.utils import (
    product_dicts,
    shift_bits_by_index,
    find_character_in_string,
)


def _process_outcome_distribution(
    qubits: int, outcome: int | str, /
) -> np.typing.NDArray[np.float64]:
    """
    Process a single outcome of a QPD experiment with observables.

    Args:
        cog: The observable set being measured by the current experiment
        outcome: The outcome of the classical bits

    Returns:
        A 1D array of the observable measurements.  The elements of
        this vector correspond to the elements of ``cog.commuting_observables``,
        and each result will be either +1 or -1.
    """
    num_meas_bits = qubits

    outcome = _outcome_to_int(outcome)
    meas_outcomes = outcome & ((1 << num_meas_bits) - 1)
    qpd_outcomes = outcome >> num_meas_bits

    # qpd_factor will be -1 or +1, depending on the overall parity of qpd
    # measurements.
    qpd_factor = 1 - 2 * (bit_count(qpd_outcomes) & 1)

    return qpd_factor, meas_outcomes


def reconstruct_distribution(
    results: SamplerResult | dict[Hashable, SamplerResult],
    coefficients: Sequence[tuple[float, WeightType]],
    partition_labels: str = None,
) -> dict[int, float]:
    r"""
    Reconstruct an expectation value from the results of the sub-experiments.

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
        observables: The observable(s) for which the expectation values will be calculated.
            This should be a :class:`~qiskit.quantum_info.PauliList` if ``results`` is a
            :class:`~qiskit.primitives.SamplerResult` instance. Otherwise, it should be a
            dictionary mapping partition labels to the observables associated with that partition.

    Returns:
        A ``list`` of ``float``\ s, such that each float is an expectation
        value corresponding to the input observable in the same position

    Raises:
        ValueError: ``observables`` and ``results`` are of incompatible types.
        ValueError: An input observable has a phase not equal to 1.
    """
    result_dict = defaultdict(float)

    labels = {*partition_labels}

    qubits = Counter(partition_labels)

    label_index_lists = {
        label: list(find_character_in_string(partition_labels, label))
        for label in labels
    }

    # Reconstruct the probability distribution
    for i, coeff in enumerate(coefficients):

        coeff_result_dict = {}

        for label in labels:
            coeff_result_dict[label] = defaultdict(float)
            quasi_probs = results[label].quasi_dists[i]
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
