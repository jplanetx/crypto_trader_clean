import asyncio
import time
import logging
import unittest
from decimal import Decimal
from src.core.order_executor import OrderExecutor
from src.utils.exceptions import OrderExecutionError, ValidationError, PositionError, ExchangeError

class DummyRiskManager:
    async def check_order_risk(self, trading_pair, side, size, price):
        return True

class FastDummyExchange:
    async def buy(self, trading_pair, size, price):
        return {"order_id": "fast_dummy_buy"}
    async def sell(self, trading_pair, size, price):
        return {"order_id": "fast_dummy_sell"}

class SlowDummyExchange:
    async def buy(self, trading_pair, size, price):
        await asyncio.sleep(0.15)  # sleep 150 ms to simulate delay
        return {"order_id": "slow_dummy_buy"}
    async def sell(self, trading_pair, size, price):
        await asyncio.sleep(0.15)
        return {"order_id": "slow_dummy_sell"}

class LogCaptureHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []
    def emit(self, record):
        self.records.append(record)

class TestOrderExecutorPerformance(unittest.IsolatedAsyncioTestCase):
    async def test_fast_order_execution_no_warning(self):
        logger = logging.getLogger("src.core.order_executor")
        capture_handler = LogCaptureHandler()
        logger.addHandler(capture_handler)
        executor = OrderExecutor(FastDummyExchange(), risk_manager=DummyRiskManager())
        await executor.execute_order("BTC-USD", "buy", 1.0, 50000)
        warnings = [r for r in capture_handler.records if r.levelno == logging.WARNING]
        self.assertEqual(len(warnings), 0, "There should be no warning for fast execution")
        logger.removeHandler(capture_handler)

    async def test_slow_order_execution_logs_warning(self):
        logger = logging.getLogger("src.core.order_executor")
        capture_handler = LogCaptureHandler()
        logger.addHandler(capture_handler)
        executor = OrderExecutor(SlowDummyExchange(), risk_manager=DummyRiskManager())
        await executor.execute_order("ETH-USD", "sell", 1.0, 3000)
        warnings = [r for r in capture_handler.records if r.levelno == logging.WARNING]
        self.assertGreater(len(warnings), 0, "Warning should be logged for slow execution")
        logger.removeHandler(capture_handler)

if __name__ == "__main__":
    unittest.main()