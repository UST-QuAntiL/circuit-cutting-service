import codecs
import json
import os
import pickle
import sys
import unittest

from qiskit import qasm3

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from app import create_app


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        self.app_context.pop()

    def test_automatic_cutting(self):
        response = self.client.post(
            "/cutCircuits",
            data=json.dumps(
                {
                    "circuit": 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[4];\ncreg meas[4];\nh q[0];\ncx q[0],q[1];\ncx q[1],q[2];\ncx q[2],q[3];\nbarrier q[0],q[1],q[2],q[3];\nmeasure q[0] -> meas[0];\nmeasure q[1] -> meas[1];\nmeasure q[2] -> meas[2];\nmeasure q[3] -> meas[3];\n',
                    "method": "automatic",
                    "max_subcircuit_width": 3,
                    "max_num_subcircuits": 2,
                    "max_cuts": 2,
                    "circuit_format": "openqasm2",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        print(response.get_json())

    def test_automatic_cutting_qasm3(self):
        response = self.client.post(
            "/cutCircuits",
            data=json.dumps(
                {
                    "circuit": 'OPENQASM 3;\ninclude "stdgates.inc";\nbit[4] meas;\nqubit[4] _all_qubits;\nlet q = _all_qubits[0:3];\nh q[0];\ncx q[0], q[1];\ncx q[1], q[2];\ncx q[2], q[3];\nmeas[0] = measure q[0];\nmeas[1] = measure q[1];\nmeas[2] = measure q[2];\nmeas[3] = measure q[3];\n',
                    "method": "automatic",
                    "max_subcircuit_width": 3,
                    "max_num_subcircuits": 2,
                    "max_cuts": 2,
                    "circuit_format": "openqasm3",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        print(response.get_json())

    def test_automatic_cutting_qiskit(self):
        circuit = qasm3.loads(
            'OPENQASM 3;\ninclude "stdgates.inc";\nbit[4] meas;\nqubit[4] _all_qubits;\nlet q = _all_qubits[0:3];\nh q[0];\ncx q[0], q[1];\ncx q[1], q[2];\ncx q[2], q[3];\nmeas[0] = measure q[0];\nmeas[1] = measure q[1];\nmeas[2] = measure q[2];\nmeas[3] = measure q[3];\n'
        )
        pickle_bytes = codecs.encode(pickle.dumps(circuit), "base64").decode()
        response = self.client.post(
            "/cutCircuits",
            data=json.dumps(
                {
                    "max_subcircuit_width": 3,
                    "circuit": pickle_bytes,
                    "method": "automatic",
                    "max_num_subcircuits": 2,
                    "max_cuts": 2,
                    "circuit_format": "qiskit",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        print(response.get_json())
