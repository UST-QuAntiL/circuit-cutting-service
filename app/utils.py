from typing import Dict

import numpy as np


def array_to_counts(array: np.ndarray) -> Dict:
    bit_length = int(np.log2(len(array)))
    format_str = '{0:0' + str(bit_length) + 'b}'
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
