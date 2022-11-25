from circuit_knitting_toolbox.circuit_cutting.wire_cutting import cut_circuit_wires
from qiskit import QuantumCircuit


def cut_circuit(input_dict):
    circuit = input_dict.get('circuit')
    method = input_dict.get('method')

    try:
        circuit = QuantumCircuit.from_qasm_str(circuit)
    except Exception as e:
        # TODO refine exception
        return "The quantum circuit has to be provided as an OpenQASM 2.0 String"

    if method == 'automatic':
        max_subcircuit_width = input_dict.get('max_subcircuit_width')
        max_cuts = input_dict.get('max_cuts')
        num_subcircuits = input_dict.get('num_subcircuits')
        return cut_circuit_wires(circuit, method=method, max_subcircuit_width=max_subcircuit_width, max_cuts=max_cuts,
                                 num_subcircuits=num_subcircuits)

    else:
        subcircuit_vertices = input_dict.get('subcircuit_vertices')
        return cut_circuit_wires(circuit, method=method, subcircuit_vertices=subcircuit_vertices)
