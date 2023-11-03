import unittest
import os, sys
import json

from app.circuit_cutter import automatic_gate_cut

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

    def test_automatic_cutting_qiskit(self):
        response = self.client.post(
            "/cutCircuits",
            data=json.dumps(
                {
                    "max_subcircuit_width": 4,
                    "circuit": "gASV+CAAAAAAAACMHXFpc2tpdC5jaXJjdWl0LnF1YW50dW1jaXJjdWl0lIwOUXVhbnR1bUNpcmN1\naXSUk5QpgZR9lCiMCl9iYXNlX25hbWWUjAdjaXJjdWl0lIwEbmFtZZSMDGNpcmN1aXQtMTU0M5SM\nBV9kYXRhlF2UKIwhcWlza2l0LmNpcmN1aXQucXVhbnR1bWNpcmN1aXRkYXRhlIwSQ2lyY3VpdElu\nc3RydWN0aW9ulJOUKYGUTn2UKIwJb3BlcmF0aW9ulIwocWlza2l0LmNpcmN1aXQubGlicmFyeS5z\ndGFuZGFyZF9nYXRlcy5yeZSMBlJZR2F0ZZSTlCmBlH2UKIwLX2RlZmluaXRpb26UTowFX25hbWWU\njAJyeZSMC19udW1fcXViaXRzlEsBjAtfbnVtX2NsYml0c5RLAIwHX3BhcmFtc5RdlIwVbnVtcHku\nY29yZS5tdWx0aWFycmF5lIwGc2NhbGFylJOUjAVudW1weZSMBWR0eXBllJOUjAJmOJSJiIeUUpQo\nSwOMATyUTk5OSv////9K/////0sAdJRiQwhmcy04UsHwP5SGlFKUYYwGX2xhYmVslE6MCWNvbmRp\ndGlvbpROjAlfZHVyYXRpb26UTowFX3VuaXSUjAJkdJR1YowGcXViaXRzlIwecWlza2l0LmNpcmN1\naXQucXVhbnR1bXJlZ2lzdGVylIwFUXViaXSUk5QpgZROfZQojAVfcmVwcpSMIVF1Yml0KFF1YW50\ndW1SZWdpc3Rlcig1LCAncScpLCAwKZSMBl9pbmRleJRLAIwJX3JlZ2lzdGVylGgxjA9RdWFudHVt\nUmVnaXN0ZXKUk5QpgZQojAFxlEsFiggpY49Ss0szeowXUXVhbnR1bVJlZ2lzdGVyKDUsICdxJymU\nXZQoaDRoMymBlE59lChoNowhUXViaXQoUXVhbnR1bVJlZ2lzdGVyKDUsICdxJyksIDEplGg4SwFo\nOWg8jAVfaGFzaJSKCAgS0bPpKAsQdYaUYmgzKYGUTn2UKGg2jCFRdWJpdChRdWFudHVtUmVnaXN0\nZXIoNSwgJ3EnKSwgMimUaDhLAmg5aDxoQ4oIYXkhHffWUC11hpRiaDMpgZROfZQoaDaMIVF1Yml0\nKFF1YW50dW1SZWdpc3Rlcig1LCAncScpLCAzKZRoOEsDaDloPGhDiggzFoaADyZp6XWGlGJoMymB\nlE59lChoNowhUXViaXQoUXVhbnR1bVJlZ2lzdGVyKDUsICdxJyksIDQplGg4SwRoOWg8aEOKCIx9\n1mnZ7rhDdYaUYmV0lGJoQ4oINnVsUNHZ8lN1hpRihZSMBmNsYml0c5QpjBRfbGVnYWN5X2Zvcm1h\ndF9jYWNoZZROdYaUYmgNKYGUTn2UKGgQaBMpgZR9lChoFk5oF2gYaBlLAWgaSwBoG12UaB9oJUMI\nZnMtOFLB8D+UhpRSlGFoK05oLE5oLU5oLmgvdWJoMGhAhZRoVCloVU51hpRiaA0pgZROfZQoaBBo\nEymBlH2UKGgWTmgXaBhoGUsBaBpLAGgbXZRoH2glQwhlcy04UsEAQJSGlFKUYWgrTmgsTmgtTmgu\naC91YmgwaEWFlGhUKWhVTnWGlGJoDSmBlE59lChoEGgTKYGUfZQoaBZOaBdoGGgZSwFoGksAaBtd\nlGgfaCVDCGVzLThSwQBAlIaUUpRhaCtOaCxOaC1OaC5oL3ViaDBoSYWUaFQpaFVOdYaUYmgNKYGU\nTn2UKGgQaBMpgZR9lChoFk5oF2gYaBlLAWgaSwBoG12UaB9oJUMIZnMtOFLB8D+UhpRSlGFoK05o\nLE5oLU5oLmgvdWJoMGhNhZRoVCloVU51hpRiaA0pgZROfZQoaBCMFnFpc2tpdC5jaXJjdWl0LmJh\ncnJpZXKUjAdCYXJyaWVylJOUKYGUfZQoaCtOaBeMB2JhcnJpZXKUaBlLBWgaSwBoG12UaCxOaBZO\naC1OaC5oL3ViaDAoaDRoQGhFaEloTXSUaFQpaFVOdYaUYmgNKYGUTn2UKGgQjCdxaXNraXQuY2ly\nY3VpdC5saWJyYXJ5LnN0YW5kYXJkX2dhdGVzLniUjAZDWEdhdGWUk5QpgZR9lCiMCWJhc2VfZ2F0\nZZRojIwFWEdhdGWUk5QpgZR9lChoFk5oF4wBeJRoGUsBaBpLAGgbXZRoK05oLE5oLU5oLmgvdWJo\nFk5oF4wCY3iUaBlLAmgaSwBoG12UaCtOaCxOaC1OaC5oL4wQX251bV9jdHJsX3F1Yml0c5RLAYwL\nX2N0cmxfc3RhdGWUSwF1YmgwaEVoNIaUaFQpaFVOdYaUYmgNKYGUTn2UKGgQjChxaXNraXQuY2ly\nY3VpdC5saWJyYXJ5LnN0YW5kYXJkX2dhdGVzLnJ6lIwGUlpHYXRllJOUKYGUfZQoaBZOaBeMAnJ6\nlGgZSwFoGksAaBtdlIwicWlza2l0LmNpcmN1aXQucGFyYW1ldGVyZXhwcmVzc2lvbpSME1BhcmFt\nZXRlckV4cHJlc3Npb26Uk5QpgZROfZQojBJfcGFyYW1ldGVyX3N5bWJvbHOUfZSMGHFpc2tpdC5j\naXJjdWl0LnBhcmFtZXRlcpSMCVBhcmFtZXRlcpSTlIwDzrMxlIwEdXVpZJSMBFVVSUSUk5QpgZR9\nlIwDaW50lIoQIb433pDJ/IH2QtE7/NAbTXNihpSBlH2UaAdosXNijB9zeW1lbmdpbmUubGliLnN5\nbWVuZ2luZV93cmFwcGVylIwKbG9hZF9iYXNpY5STlEMZAQAACQABAACADQAAAAADAAAAAAAAAM6z\nMZSFlFKUc4wLX3BhcmFtZXRlcnOUj5QoaLmQjAxfc3ltYm9sX2V4cHKUaL1DSgEAAAkAAQAAgA8A\nAAACAACABgAAAAAAAAAAABDAAQAAAAAAAAADAACADQAAAAADAAAAAAAAAM6zMQQAAIAAAAAAAQAA\nAAAAAAAxlIWUUpSMCV9uYW1lX21hcJR9lGixaLlzdYaUYmFoK05oLE5oLU5oLmgvdWJoMGg0hZRo\nVCloVU51hpRiaA0pgZROfZQoaBBojimBlH2UKGiRaJMpgZR9lChoFk5oF2iWaBlLAWgaSwBoG12U\naCtOaCxOaC1OaC5oL3ViaBZOaBdomGgZSwJoGksAaBtdlGgrTmgsTmgtTmguaC9omksBaJtLAXVi\naDBoRWg0hpRoVCloVU51hpRiaA0pgZROfZQoaBBojimBlH2UKGiRaJMpgZR9lChoFk5oF2iWaBlL\nAWgaSwBoG12UaCtOaCxOaC1OaC5oL3ViaBZOaBdomGgZSwJoGksAaBtdlGgrTmgsTmgtTmguaC9o\nmksBaJtLAXViaDBoSWg0hpRoVCloVU51hpRiaA0pgZROfZQoaBBooimBlH2UKGgWTmgXaKVoGUsB\naBpLAGgbXZRoqSmBlE59lChorH2UaLlowHNowY+UKGi5kGjDaL1DSgEAAAkAAQAAgA8AAAACAACA\nBgAAAAAAAAAAABDAAQAAAAAAAAADAACADQAAAAADAAAAAAAAAM6zMQQAAIAAAAAAAQAAAAAAAAAx\nlIWUUpRox32UaLFouXN1hpRiYWgrTmgsTmgtTmguaC91YmgwaDSFlGhUKWhVTnWGlGJoDSmBlE59\n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\naCxOaC1OaC5oL3ViaDBoTYWUaFQpaFVOdYaUYmgNKYGUTn2UKGgQaKIpgZR9lChoFk5oF2ilaBlL\nAWgaSwBoG12UaKkpgZROfZQoaKx9lGqnAQAAaqsBAABzaMGPlChqpwEAAJBow2i9Q0wBAAAJAAEA\nAIAPAAAAAgAAgAAAAAACAAAAAAAAAC0yAQAAAAAAAAADAACADQAAAAADAAAAAAAAAM6yMQQAAIAA\nAAAAAQAAAAAAAAAxlIWUUpRox32UaqMBAABqpwEAAHN1hpRiYWgrTmgsTmgtTmguaC91YmgwaE2F\nlGhUKWhVTnWGlGJoDSmBlE59lChoEGgTKYGUfZQoaBZOaBdoGGgZSwFoGksAaBtdlGgfaCVDCGZz\nLThSwfC/lIaUUpRhaCtOaCxOaC1OaC5oL3ViaDBoTYWUaFQpaFVOdYaUYmgNKYGUTn2UKGgQaIMp\ngZR9lChoK05oF2iGaBlLBWgaSwBoG12UaCxOaBZOaC1OaC5oL3ViaDAoaDRoQGhFaEloTXSUaFQp\naFVOdYaUYmgNKYGUTn2UKGgQjBZxaXNraXQuY2lyY3VpdC5tZWFzdXJllIwHTWVhc3VyZZSTlCmB\nlH2UKGgXjAdtZWFzdXJllGgZSwFoGksBaBtdlGgrTmgsTmgWTmgtTmguaC91YmgwaDSFlGhUjCBx\naXNraXQuY2lyY3VpdC5jbGFzc2ljYWxyZWdpc3RlcpSMBUNsYml0lJOUKYGUTn2UKGg2jCNDbGJp\ndChDbGFzc2ljYWxSZWdpc3Rlcig1LCAnYycpLCA0KZRoOEsEaDlqXwIAAIwRQ2xhc3NpY2FsUmVn\naXN0ZXKUk5QpgZQojAFjlEsFigikbz60pZP2HIwZQ2xhc3NpY2FsUmVnaXN0ZXIoNSwgJ2MnKZRd\nlChqYQIAACmBlE59lChoNowjQ2xiaXQoQ2xhc3NpY2FsUmVnaXN0ZXIoNSwgJ2MnKSwgMCmUaDhL\nAGg5amcCAABoQ4oIUx8bZY3BnXN1hpRiamECAAApgZROfZQoaDaMI0NsYml0KENsYXNzaWNhbFJl\nZ2lzdGVyKDUsICdjJyksIDEplGg4SwFoOWpnAgAAaEOKCKyGa05Xiu3NdYaUYmphAgAAKYGUTn2U\nKGg2jCNDbGJpdChDbGFzc2ljYWxSZWdpc3Rlcig1LCAnYycpLCAyKZRoOEsCaDlqZwIAAGhDigh+\nI9Cxb9kFinWGlGJqYQIAACmBlE59lChoNowjQ2xiaXQoQ2xhc3NpY2FsUmVnaXN0ZXIoNSwgJ2Mn\nKSwgMymUaDhLA2g5amcCAABoQ4oI14ogG32HS6d1hpRiamICAABldJRiaEOKCDDycARHUJsBdYaU\nYoWUaFVOdYaUYmgNKYGUTn2UKGgQaloCAABoMGhAhZRoVGp3AgAAhZRoVU51hpRiaA0pgZROfZQo\naBBqWgIAAGgwaEWFlGhUanMCAACFlGhVTnWGlGJoDSmBlE59lChoEGpaAgAAaDBoSYWUaFRqbwIA\nAIWUaFVOdYaUYmgNKYGUTn2UKGgQaloCAABoMGhNhZRoVGprAgAAhZRoVU51hpRiZYwPX29wX3N0\nYXJ0X3RpbWVzlE6MFF9jb250cm9sX2Zsb3dfc2NvcGVzlF2UjAVxcmVnc5RdlGg8YYwFY3JlZ3OU\nXZRqZwIAAGGMB19xdWJpdHOUXZQoaDRoQGhFaEloTWWMB19jbGJpdHOUXZQoamsCAABqbwIAAGpz\nAgAAancCAABqYgIAAGWMDl9xdWJpdF9pbmRpY2VzlH2UKGg0aACMDEJpdExvY2F0aW9uc5STlEsA\nXZRoPEsAhpRhhpSBlGhAaqECAABLAV2UaDxLAYaUYYaUgZRoRWqhAgAASwJdlGg8SwKGlGGGlIGU\naElqoQIAAEsDXZRoPEsDhpRhhpSBlGhNaqECAABLBF2UaDxLBIaUYYaUgZR1jA5fY2xiaXRfaW5k\naWNlc5R9lChqawIAAGqhAgAASwBdlGpnAgAASwCGlGGGlIGUam8CAABqoQIAAEsBXZRqZwIAAEsB\nhpRhhpSBlGpzAgAAaqECAABLAl2UamcCAABLAoaUYYaUgZRqdwIAAGqhAgAASwNdlGpnAgAASwOG\nlGGGlIGUamICAABqoQIAAEsEXZRqZwIAAEsEhpRhhpSBlHWMCV9hbmNpbGxhc5RdlIwNX2NhbGli\ncmF0aW9uc5SMC2NvbGxlY3Rpb25zlIwLZGVmYXVsdGRpY3SUk5SMCGJ1aWx0aW5zlIwEZGljdJST\nlIWUUpSMEF9wYXJhbWV0ZXJfdGFibGWUjB1xaXNraXQuY2lyY3VpdC5wYXJhbWV0ZXJ0YWJsZZSM\nDlBhcmFtZXRlclRhYmxllJOUKYGUTn2UKIwGX3RhYmxllH2UKGi5atgCAACME1BhcmFtZXRlclJl\nZmVyZW5jZXOUk5QpgZRdlChoo0sAhpRo4ksAhpRqBgEAAEsAhpRqKgEAAEsAhpRqTgEAAEsAhpRq\ncgEAAEsAhpRlYmqnAQAAauACAAApgZRdlChqnQEAAEsAhpRqygEAAEsAhpRq7gEAAEsAhpRqEgIA\nAEsAhpRqNgIAAEsAhpRlYnWMBV9rZXlzlI+UKGi5aqcBAACQjAZfbmFtZXOUj5QoaLFqowEAAJB1\nhpRiaMFOjAdfbGF5b3V0lE6MDV9nbG9iYWxfcGhhc2WUSwCMCGR1cmF0aW9ulE6MBHVuaXSUaC+M\nCV9tZXRhZGF0YZROdWIu\n",
                    "method": "automatic",
                    "max_num_subcircuits": 2,
                    "max_cuts": 3,
                    "circuit_format": "qiskit",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        print(response.get_json())

    def test_automatic_gate_cut(self):
        response = self.client.post(
            "/gateCutCircuits",
            data=json.dumps(
                {
                    "circuit": 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[4];\ncreg meas[4];\nh q[0];\ncx q[0],q[1];\ncx q[1],q[2];\ncx q[2],q[3];\nmeasure q[0] -> meas[0];\nmeasure q[1] -> meas[1];\nmeasure q[2] -> meas[2];\nmeasure q[3] -> meas[3];\n',
                    "method": "automatic_gate_cutting",
                    "max_subcircuit_width": 2,
                    "max_num_subcircuits": 2,
                    "max_cuts": 2,
                    "circuit_format": "openqasm2",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        print(response.get_json())
