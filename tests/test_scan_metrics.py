import unittest
from unittest.mock import Mock
from datetime import datetime

from agents.pipeline import CloudAnalysis, JudgeVerdict, PipelineResult
from agents.tribunal import fetch_markets, run_agent, gather_agents, run_pipeline_on_markets
from ai_explanation import AIExplanation, format_explanation
from backtester import Backtester, filter_markets, summarize_trades
from config import RpcSettings, LiquidityGateSettings, SpreadSettings, ConnectionSettings, CloudTierSettings, Settings
from core.blockchain import BlockchainError, ConnectionError, TransactionError, BlockchainClient
from core.config import Config
from core.models import Order, Market, QuantitativeSignal, MarketSchema, OrderSchema, QuantitativeSignalSchema, validate_market_data
from core.utils import clamp
from data.filters import passes_liquidity_gate, passes_spread_gate, passes_volume_gate, passes_all_gates, filter_markets
from data.polymarket_client import PolymarketClient, PolymarketAdapter
from data.ranking import rank_markets
from data.rpc_failover import RPCNode, RPCPoolError, RPCPool
from data.scanner import ScanConfig, MarketScanner, run_scan
from execution.order_executor import OrderExecutorError, OrderValidationError, LiquidityGateError, OrderExecutor, validate_order, submit_order, cancel_order
from execution.paper import PaperBroker
from execution.state_machine import OrderStateMachine, OrderState, transition, _confirming_timeout, _close_or_fail_timeout, get_state
from execution.supervisor import TransactionSupervisor, submit_order
from main import main
from market_connector import Market, PolymarketClient
from persistence import PersistenceManager, save_markets_json, load_markets_json
from quantitative_signals import QuantitativeSignal, build_signal
from risk_engine import OutcomeAssessment, passes_liquidity_gate, passes_spread_gate, calculate_expected_value, calculate_fractional_kelly, determine_position_size, _z_score, _erf_inv, estimate_outcome_probability, calculate_confidence_interval, assess_outcome
from state_manager import StateManager, remember_markets, seen_recently, clear, close
from telemetry import TelemetryError, Telemetry, _as_dict, _json_default, get, reset_all
from unified_decision import UnifiedDecision

class ScanMetrics:
    def __init__(self):
        self.scan_count = 0
        self.last_scan_time = None

    def record_scan(self):
        self.scan_count += 1
        self.last_scan_time = datetime.now()

    def last_scan_stats(self):
        return {
            "scan_count": self.scan_count,
            "last_scan_time": self.last_scan_time
        }

class TestScanMetrics(unittest.TestCase):
    def test_record_scan(self):
        metrics = ScanMetrics()
        metrics.record_scan()
        self.assertEqual(metrics.scan_count, 1)
        self.assertIsNotNone(metrics.last_scan_time)

    def test_last_scan_stats(self):
        metrics = ScanMetrics()
        metrics.record_scan()
        stats = metrics.last_scan_stats()
        self.assertEqual(stats["scan_count"], 1)
        self.assertIsNotNone(stats["last_scan_time"])

if __name__ == '__main__':
    unittest.main()
