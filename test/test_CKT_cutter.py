import codecs
import json
import pickle
import unittest

from qiskit.circuit.random import random_circuit

from app import create_app
from app.CKT_cutter import automatic_cut


class CutFindingTestCase(unittest.TestCase):
    def test_automatic_cut(self):
        circuit = random_circuit(7, 6, max_operands=2, seed=1242)
        result = automatic_cut(circuit, 4)
        self.assertTrue(len(result["individual_subcircuits"]) > 0)
        self.assertTrue(
            len(result["individual_subcircuits"]) == len(result["subcircuit_labels"])
        )

    def test_automatic_cut_exception(self):
        circuit = random_circuit(7, 6, max_operands=2, seed=1242)
        self.assertRaises(Exception, automatic_cut, circuit, 4, 0)


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
            "/ckt/cutCircuits",
            data=json.dumps(
                {
                    "circuit": 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[4];\ncreg meas[4];\nh q[0];\ncx q[0],q[1];\ncx q[1],q[2];\ncx q[2],q[3];\nbarrier q[0],q[1],q[2],q[3];\nmeasure q[0] -> meas[0];\nmeasure q[1] -> meas[1];\nmeasure q[2] -> meas[2];\nmeasure q[3] -> meas[3];\n',
                    "method": "automatic",
                    "max_subcircuit_width": 2,
                    "max_num_subcircuits": 2,
                    "max_cuts": 2,
                    "circuit_format": "openqasm2",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        print(response.get_json())

    def test_automatic_cutting_2(self):
        circuit = random_circuit(7, 6, max_operands=2, seed=1242)
        pickle_bytes = codecs.encode(pickle.dumps(circuit), "base64").decode()
        response = self.client.post(
            "/ckt/cutCircuits",
            data=json.dumps(
                {
                    "circuit": pickle_bytes,
                    "method": "automatic",
                    "max_subcircuit_width": 4,
                    "max_num_subcircuits": 2,
                    "max_cuts": 2,
                    "circuit_format": "qiskit",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        print(response.get_json())
