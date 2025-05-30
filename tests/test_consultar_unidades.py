"""
Unit test consultar_unidades
"""

import unittest

import requests

from tests import config


class TestConsultarUnidades(unittest.TestCase):
    """Test consultar_unidades"""

    def test_get_consultar_unidades(self):
        """Test GET consultar_unidades"""
        response = requests.get(
            url=f"{config['api_base_url']}/consultar_unidades",
            headers={"X-Api-Key": config["api_key"]},
            timeout=config["timeout"],
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue("success" in payload)
        self.assertTrue(payload["success"])
        self.assertTrue("message" in payload)
        self.assertTrue("data" in payload)
        self.assertTrue(isinstance(payload["data"], list))
        for item in payload["data"]:
            self.assertTrue("id" in item)
            self.assertTrue("clave" in item)
            self.assertTrue("nombre" in item)


if __name__ == "__main__":
    unittest.main()
