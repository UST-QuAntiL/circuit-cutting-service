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

from typing import Dict

import numpy as np
from qiskit.primitives import SamplerResult


def array_to_counts(array: np.ndarray) -> Dict:
    bit_length = int(np.log2(len(array)))
    format_str = "{0:0" + str(bit_length) + "b}"
    return {format_str.format(i): v for i, v in enumerate(array) if v != 0}


def counts_to_array(counts_dict: Dict, n_qubits: int) -> np.ndarray:
    array = np.zeros(2 ** n_qubits)
    for key, value in counts_dict.items():
        if isinstance(key, int):
            pass
        elif isinstance(key, str):
            if key.startswith("0x"):
                key = int(key, 16)
            elif key.startswith("0") or key.startswith("1"):
                key = int(key, 2)
            else:
                raise ValueError("String could not be decoded")
        else:
            raise TypeError("Type has to be either integer or string")
        array[key] = value
    return array


def normalize_array(array: np.ndarray) -> np.ndarray:
    return array / np.sum(array)


def sampler_result_to_array_dict(sampler_result: SamplerResult):
    result_array_dict = {}
    for idx, exp in enumerate(sampler_result.experiments):
        result_array_dict[idx] = counts_to_array(
            exp["quasi_dists"], exp["metadata"]["simulator_metadata"]["num_qubits"]
        )

    return result_array_dict


def find_character_in_string(string, ch):
    for i, ltr in enumerate(string):
        if ltr == ch:
            yield i


def shift_bits_by_index(num, idx_list):
    n_bits = len(idx_list)
    new_num = 0
    sorted_idx_list = sorted(idx_list, reverse=True)
    prev_index = sorted_idx_list[0]
    for i, idx in enumerate(sorted_idx_list):
        new_num = new_num << (prev_index - idx)
        new_num += (num >> (n_bits - i - 1)) & 1
        prev_index = idx

    return new_num << prev_index


def product_dicts(*dicts):
    # Base case: If there is only one dictionary, convert its values to lists
    if len(dicts) == 1:
        return {(key,): [value] for key, value in dicts[0].items()}

    # Recursive case: Compute the product of n-1 dictionaries
    dicts_except_last = dicts[:-1]
    product_except_last = product_dicts(*dicts_except_last)

    # Get the last dictionary
    last_dict = dicts[-1]

    # Compute the product of the last dictionary with the result from the previous step using dictionary comprehensions
    return {
        (*prod_key, key): prod_val + [val]
        for prod_key, prod_val in product_except_last.items()
        for key, val in last_dict.items()
    }


def remove_bits(number, bit_positions):
    """
    Removes multiple bits from the binary representation of an integer at specified positions.

    :param number: The integer from which bits will be removed.
    :param bit_positions: A list of positions of the bits to remove, where 0 is the least significant bit.
    :return: The integer resulting from the removal of the specified bits.
    """
    for bit_position in sorted(bit_positions, reverse=True):
        # Create a mask with all bits set except the bit at 'bit_position'
        mask = ~(1 << bit_position)

        # Apply the mask to the number using bitwise AND
        new_number = number & mask

        # Shift the bits to the right of 'bit_position' one place to the left
        right_part = number & ((1 << bit_position) - 1)
        left_part = (new_number >> (bit_position + 1)) << bit_position

        # Combine the left and right parts
        number = left_part | right_part

    return number


def replace_str_index(text, index=0, replacement=""):
    return f"{text[:index]}{replacement}{text[index+1:]}"
