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
    """Тесты на импорт модулей"""

    def test_import_config(self) -> None:
        self.assertIsNotNone(config)

    def test_import_data_filters(self) -> None:
        self.assertIsNotNone(data.filters)

    def test_import_risk_engine(self) -> None:
        self.assertIsNotNone(risk_engine)

    def test_import_main(self) -> None:
        self.assertIsNotNone(main)

    def test_import_data_scanner(self) -> None:
        self.assertIsNotNone(data.scanner)

    def test_import_data_polymarket_client(self) -> None:
        self.assertIsNotNone(data.polymarket_client)

    def test_import_core_models(self) -> None:
        self.assertIsNotNone(core.models)

    def test_import_execution_paper(self) -> None:
        self.assertIsNotNone(execution.paper)

if __name__ == '__main__':
    unittest.main()
