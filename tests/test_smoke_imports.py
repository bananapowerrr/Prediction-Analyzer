import unittest
import config
import data.filters
import risk_engine
import main
import data.scanner
import data.polymarket_client
import core.models
import execution.paper

class TestSmokeImports(unittest.TestCase):
    def test_import_config(self):
        self.assertIsNotNone(config)

    def test_import_data_filters(self):
        self.assertIsNotNone(data.filters)

    def test_import_risk_engine(self):
        self.assertIsNotNone(risk_engine)

    def test_import_main(self):
        self.assertIsNotNone(main)

    def test_import_data_scanner(self):
        self.assertIsNotNone(data.scanner)

    def test_import_data_polymarket_client(self):
        self.assertIsNotNone(data.polymarket_client)

    def test_import_core_models(self):
        self.assertIsNotNone(core.models)

    def test_import_execution_paper(self):
        self.assertIsNotNone(execution.paper)

if __name__ == '__main__':
    unittest.main()
