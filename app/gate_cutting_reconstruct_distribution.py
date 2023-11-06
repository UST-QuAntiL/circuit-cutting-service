from __future__ import annotations

from collections import defaultdict
from typing import Hashable, Sequence

import numpy as np
from circuit_knitting.cutting.cutting_decomposition import decompose_observables
from circuit_knitting.cutting.cutting_experiments import _get_pauli_indices
from circuit_knitting.cutting.cutting_reconstruction import _outcome_to_int
from circuit_knitting.cutting.qpd import WeightType
from circuit_knitting.utils.bitwise import bit_count
from circuit_knitting.utils.observable_grouping import (
    CommutingObservableGroup,
    ObservableCollection,
)
from qiskit.primitives import SamplerResult
from qiskit.quantum_info import PauliList

from app.utils import counts_to_array


def _process_outcome_distribution(
    cog: CommutingObservableGroup, outcome: int | str, /
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
    num_meas_bits = len(_get_pauli_indices(cog))

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
    observables: PauliList | dict[Hashable, PauliList],
) -> list[float]:
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
    if isinstance(observables, PauliList) and not isinstance(results, SamplerResult):
        raise ValueError(
            "If observables is a PauliList, results must be a SamplerResult instance."
        )
    if isinstance(observables, dict) and not isinstance(results, dict):
        raise ValueError(
            "If observables is a dictionary, results must also be a dictionary."
        )

    # If circuit was not separated, transform input data structures to dictionary format
    if isinstance(observables, PauliList):
        if any(obs.phase != 0 for obs in observables):
            raise ValueError("An input observable has a phase not equal to 1.")
        subobservables_by_subsystem = decompose_observables(
            observables, "A" * len(observables[0])
        )
        results_dict: dict[Hashable, SamplerResult] = {"A": results}
        expvals = np.zeros(len(observables))

    else:
        results_dict = results
        for label, subobservable in observables.items():
            if any(obs.phase != 0 for obs in subobservable):
                raise ValueError("An input observable has a phase not equal to 1.")
        subobservables_by_subsystem = observables
        expvals = np.zeros(len(list(observables.values())[0]))

    subsystem_observables = {
        label: ObservableCollection(subobservables)
        for label, subobservables in subobservables_by_subsystem.items()
    }

    qubits = {
        label: len(subobservables[0])
        for label, subobservables in subobservables_by_subsystem.items()
    }

    result = np.zeros(2 ** sum(qubits.values()))

    # Reconstruct the expectation values
    for i, coeff in enumerate(coefficients):
        current_expvals = np.ones((len(expvals),))

        coeff_result_dict = {}

        for label, so in subsystem_observables.items():
            coeff_result_dict[label] = defaultdict(float)
            subsystem_expvals = [
                np.zeros(len(cog.commuting_observables)) for cog in so.groups
            ]
            for k, cog in enumerate(so.groups):
                quasi_probs = results_dict[label].quasi_dists[i * len(so.groups) + k]
                for outcome, quasi_prob in quasi_probs.items():
                    qpd_factor, meas_outcomes = _process_outcome_distribution(
                        cog, outcome
                    )
                    coeff_result_dict[label][meas_outcomes] += qpd_factor * quasi_prob

            for k, subobservable in enumerate(subobservables_by_subsystem[label]):
                current_expvals[k] *= np.mean(
                    [subsystem_expvals[m][n] for m, n in so.lookup[subobservable]]
                )

        temp = np.ones(1)
        for label, r in coeff_result_dict.items():
            temp = np.kron(counts_to_array(r, qubits[label]), temp)

        result += coeff[0] * temp

    return result
