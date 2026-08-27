"""RPC rotation and failover pool for blockchain node data ingestion.

Provides :class:`RPCPool` — a round-robin health-aware connection pool that
maintains multiple JSON-RPC endpoints and transparently fails over when the
current node becomes unreachable or rate-limited.

Each endpoint is wrapped in :class:`RPCNode` which tracks latency, success
rate, cooldown state and priority.  The pool periodically probes nodes and
deprioritises unhealthy ones.

Usage::

    from data.rpc_failover import RPCPool

    pool = RPCPool(
        endpoints=[
            "https://polygon-rpc.com",
            "https://rpc.ankr.com/polygon",
            "https://polygon.llamarpc.com",
        ],
        chain_id=137,
        cooldown_seconds=60,
    )

    # Execute a call with automatic failover
    balance = await pool.call("eth_getBalance", ["0xAbC...123", "latest"])
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional

import aiohttp
from web3 import Web3
from web3.providers import AsyncHTTPProvider

logger = logging.getLogger(__name__)


class NodeState(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    COOLDOWN = "cooldown"


@dataclass
class RPCNode:
    """Single RPC endpoint with health metadata."""

    url: str
    priority: int = 0
    max_failures: int = 3
    cooldown_seconds: float = 60.0
    timeout_seconds: float = 10.0

    _failures: int = field(default=0, repr=False)
    _last_failure: float = field(default=0.0, repr=False)
    _last_latency: float = field(default=0.0, repr=False)
    _successes: int = field(default=0, repr=False)
    _total_calls: int = field(default=0, repr=False)
    _state: NodeState = field(default=NodeState.HEALTHY, repr=False)

    @property
    def state(self) -> NodeState:
        if self._failures < self.max_failures:
            return NodeState.HEALTHY
        elapsed = time.monotonic() - self._last_failure
        if elapsed >= self.cooldown_seconds:
            self._failures = 0
            self._state = NodeState.HEALTHY
            return NodeState.HEALTHY
        self._state = NodeState.COOLDOWN
        return NodeState.COOLDOWN

    @property
    def is_available(self) -> bool:
        return self.state != NodeState.COOLDOWN

    @property
    def success_rate(self) -> float:
        if self._total_calls == 0:
            return 1.0
        return self._successes / self._total_calls

    @property
    def score(self) -> float:
        """Lower is better. Combines priority, latency and success rate."""
        latency_weight = self._last_latency if self._last_latency > 0 else 0.5
        rate_penalty = (1.0 - self.success_rate) * 100
        cooldown_penalty = 1000 if self.state == NodeState.COOLDOWN else 0
        return self.priority * 10 + latency_weight + rate_penalty + cooldown_penalty

    def record_success(self, latency: float) -> None:
        self._failures = 0
        self._successes += 1
        self._total_calls += 1
        self._last_latency = latency
        self._state = NodeState.HEALTHY

    def record_failure(self) -> None:
        self._failures += 1
        self._total_calls += 1
        self._last_failure = time.monotonic()
        if self._failures >= self.max_failures:
            self._state = NodeState.UNHEALTHY
            logger.warning(
                "RPC node %s marked unhealthy after %d consecutive failures",
                self.url,
                self._failures,
            )

    def reset(self) -> None:
        self._failures = 0
        self._successes = 0
        self._total_calls = 0
        self._last_latency = 0.0
        self._state = NodeState.HEALTHY


class RPCPoolError(Exception):
    """Raised when all RPC nodes are exhausted."""


class RPCPool:
    """Health-aware round-robin pool of JSON-RPC endpoints.

    Args:
        endpoints: List of RPC endpoint URLs.
        chain_id: EIP-155 chain identifier.
        cooldown_seconds: Seconds to cool down an unhealthy node.
        max_retries: Maximum failover attempts per call.
        timeout_seconds: Default HTTP timeout.
        request_timeout: Per-request timeout for aiohttp.
    """

    def __init__(
        self,
        endpoints: List[str],
        chain_id: int,
        cooldown_seconds: float = 60.0,
        max_retries: int = 3,
        timeout_seconds: float = 10.0,
        request_timeout: float = 30.0,
    ) -> None:
        if not endpoints:
            raise ValueError("At least one RPC endpoint is required")

        self.chain_id = chain_id
        self.max_retries = max_retries
        self.request_timeout = request_timeout

        self._nodes: List[RPCNode] = [
            RPCNode(
                url=url,
                cooldown_seconds=cooldown_seconds,
                timeout_seconds=timeout_seconds,
            )
            for url in endpoints
        ]
        self._index = 0
        self._session: Optional[aiohttp.ClientSession] = None
        self._w3_cache: Dict[str, Web3] = {}

        logger.info(
            "RPCPool initialised with %d endpoints (chain_id=%d)",
            len(self._nodes),
            chain_id,
        )

    @property
    def endpoints(self) -> List[str]:
        return [n.url for n in self._nodes]

    @property
    def healthy_count(self) -> int:
        return sum(1 for n in self._nodes if n.is_available)

    def _sorted_nodes(self) -> List[RPCNode]:
        available = [n for n in self._nodes if n.is_available]
        if not available:
            return []
        return sorted(available, key=lambda n: n.score)

    def _pick_node(self) -> RPCNode:
        ranked = self._sorted_nodes()
        if not ranked:
            raise RPCPoolError(
                f"All {len(self._nodes)} RPC nodes are in cooldown. "
                "Wait for cooldown to expire or add more endpoints."
            )
        return ranked[0]

    def _next_node(self) -> RPCNode:
        ranked = self._sorted_nodes()
        if not ranked:
            raise RPCPoolError(
                f"All {len(self._nodes)} RPC nodes are in cooldown."
            )
        self._index = (self._index + 1) % len(ranked)
        return ranked[self._index % len(ranked)]

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.request_timeout)
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
        self._w3_cache.clear()

    def _get_w3(self, url: str) -> Web3:
        if url not in self._w3_cache:
            provider = AsyncHTTPProvider(url)
            self._w3_cache[url] = Web3(provider)
        return self._w3_cache[url]

    async def call(
        self,
        method: str,
        params: Optional[List[Any]] = None,
    ) -> Any:
        """Execute a raw JSON-RPC call with automatic failover.

        Tries each available node in score order, recording latency and
        failures. Raises :class:`RPCPoolError` if all nodes are exhausted.
        """
        last_error: Optional[Exception] = None
        tried: set[str] = set()

        for attempt in range(min(self.max_retries + 1, self.healthy_count + 1)):
            try:
                node = self._pick_node()
            except RPCPoolError:
                break

            while node.url in tried:
                node = self._next_node()
                if not node.is_available:
                    break
            if node.url in tried:
                continue
            tried.add(node.url)

            start = time.monotonic()
            try:
                session = await self._ensure_session()
                payload = {
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": params or [],
                    "id": 1,
                }
                async with session.post(
                    node.url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=node.timeout_seconds),
                ) as resp:
                    elapsed = time.monotonic() - start
                    body = await resp.json()

                    if resp.status == 429:
                        raise Exception(f"Rate limited (429) on {node.url}")
                    if resp.status >= 500:
                        raise Exception(
                            f"Server error {resp.status} from {node.url}"
                        )
                    if "error" in body:
                        raise Exception(
                            f"RPC error: {body['error']} from {node.url}"
                        )

                    node.record_success(elapsed)
                    logger.debug(
                        "RPC %s succeeded via %s in %.3fs",
                        method,
                        node.url,
                        elapsed,
                    )
                    return body.get("result")

            except Exception as exc:
                elapsed = time.monotonic() - start
                node.record_failure()
                last_error = exc
                logger.warning(
                    "RPC %s failed on %s (%.3fs): %s",
                    method,
                    node.url,
                    elapsed,
                    exc,
                )
                continue

        raise RPCPoolError(
            f"All nodes failed for method '{method}': {last_error}"
        ) from last_error

    async def get_block_number(self) -> int:
        result = await self.call("eth_blockNumber")
        return int(result, 16)

    async def get_balance(self, address: str, block: str = "latest") -> int:
        checksum = Web3.to_checksum_address(address)
        result = await self.call("eth_getBalance", [checksum, block])
        return int(result, 16)

    async def get_block(self, block_identifier: Any = "latest") -> Dict[str, Any]:
        if isinstance(block_identifier, int):
            block_identifier = hex(block_identifier)
        return await self.call("eth_getBlockByNumber", [block_identifier, False])

    async def get_transaction_receipt(
        self, tx_hash: str
    ) -> Optional[Dict[str, Any]]:
        return await self.call("eth_getTransactionReceipt", [tx_hash])

    async def call_contract(
        self,
        to: str,
        data: str,
        block: str = "latest",
    ) -> str:
        checksum = Web3.to_checksum_address(to)
        return await self.call(
            "eth_call",
            [{"to": checksum, "data": data}, block],
        )

    async def health_check(self) -> Dict[str, Any]:
        """Probe each node and return a health summary."""
        results = {}
        for node in self._nodes:
            start = time.monotonic()
            try:
                session = await self._ensure_session()
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_blockNumber",
                    "params": [],
                    "id": 1,
                }
                async with session.post(
                    node.url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=node.timeout_seconds),
                ) as resp:
                    elapsed = time.monotonic() - start
                    await resp.json()
                    ok = resp.status == 200
                    if ok:
                        node.record_success(elapsed)
                    else:
                        node.record_failure()
                    results[node.url] = {
                        "healthy": ok,
                        "latency_ms": round(elapsed * 1000, 1),
                        "status": node.state.value,
                        "success_rate": round(node.success_rate, 3),
                    }
            except Exception as exc:
                elapsed = time.monotonic() - start
                node.record_failure()
                results[node.url] = {
                    "healthy": False,
                    "latency_ms": round(elapsed * 1000, 1),
                    "status": node.state.value,
                    "error": str(exc),
                    "success_rate": round(node.success_rate, 3),
                }
        return results

    def __repr__(self) -> str:
        return (
            f"RPCPool(endpoints={len(self._nodes)}, "
            f"healthy={self.healthy_count}, chain_id={self.chain_id})"
        )
