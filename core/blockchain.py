"""Web3 integration for Polygon and Base smart-contract interaction.

Provides :class:`BlockchainClient` — a thin wrapper around *web3.py* that
supports both the Polygon (PoS) and Base (OP Stack) networks.

Usage::

    from core.blockchain import BlockchainClient

    client = BlockchainClient(
        rpc_url="https://polygon-rpc.com",
        chain_id=137,
        private_key=os.getenv("RPC_PRIVATE_KEY"),
    )

    balance = client.get_balance("0xAbC...123")
    client.send_transaction(to="0xAbC...123", value=Web3.to_wei(0.1, "ether"))
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from web3 import Web3
from web3.types import TxReceipt

logger = logging.getLogger(__name__)

SUPPORTED_CHAINS: Dict[int, str] = {
    137: "Polygon",
    80001: "Polygon Mumbai",
    8453: "Base",
    84532: "Base Sepolia",
}


class BlockchainError(Exception):
    """Raised on any blockchain interaction failure."""


class ConnectionError(BlockchainError):
    """Raised when the provider cannot connect to the RPC endpoint."""


class TransactionError(BlockchainError):
    """Raised when a transaction fails after submission."""


class BlockchainClient:
    """Unified web3 client for Polygon / Base networks.

    Args:
        rpc_url: JSON-RPC endpoint URL.
        chain_id: EIP-155 chain identifier (137 = Polygon, 8453 = Base).
        private_key: Optional wallet private key for signing transactions.
    """

    def __init__(
        self,
        rpc_url: str,
        chain_id: int,
        private_key: Optional[str] = None,
    ) -> None:
        if not rpc_url:
            raise ValueError("rpc_url is required")
        if chain_id not in SUPPORTED_CHAINS:
            raise ValueError(
                f"Unsupported chain_id {chain_id}; "
                f"supported: {list(SUPPORTED_CHAINS.keys())}"
            )

        self.rpc_url = rpc_url
        self.chain_id = chain_id
        self.chain_name = SUPPORTED_CHAINS[chain_id]
        self._w3 = Web3(Web3.HTTPProvider(rpc_url))

        if private_key:
            account = self._w3.eth.account.from_key(private_key)
            self._w3.eth.default_account = account.address
            self._account = account
        else:
            self._account = None

        logger.info(
            "BlockchainClient initialised for %s (chain_id=%d, rpc=%s)",
            self.chain_name,
            chain_id,
            rpc_url,
        )

    # ------------------------------------------------------------------ helpers

    @property
    def w3(self) -> Web3:
        return self._w3

    def is_connected(self) -> bool:
        """Return ``True`` if the RPC provider is reachable."""
        return self._w3.is_connected()

    def assert_connected(self) -> None:
        """Raise :class:`ConnectionError` when the provider is offline."""
        if not self.is_connected():
            raise ConnectionError(
                f"Cannot reach RPC endpoint {self.rpc_url} "
                f"for {self.chain_name}"
            )

    # ------------------------------------------------------------ account info

    def get_balance(self, address: str, block_identifier: str = "latest") -> int:
        """Return the balance of *address* in **wei**."""
        self.assert_connected()
        checksum = Web3.to_checksum_address(address)
        return self._w3.eth.get_balance(checksum, block_identifier)

    def get_transaction_count(self, address: str) -> int:
        """Return the nonce for *address*."""
        self.assert_connected()
        checksum = Web3.to_checksum_address(address)
        return self._w3.eth.get_transaction_count(checksum)

    def get_gas_price(self) -> int:
        """Return the current gas price in **wei**."""
        self.assert_connected()
        return self._w3.eth.gas_price

    def get_block(self, block_identifier: Any = "latest") -> Any:
        """Fetch a block by number or tag."""
        self.assert_connected()
        return self._w3.eth.get_block(block_identifier)

    # ------------------------------------------------------------ transactions

    def send_transaction(
        self,
        to: str,
        value: int,
        data: bytes = b"",
        gas: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
    ) -> TxReceipt:
        """Build, sign and send a simple value-transfer transaction.

        Returns the transaction receipt on success.
        """
        if self._account is None:
            raise BlockchainError(
                "No private key configured; cannot sign transactions"
            )
        self.assert_connected()

        to_checksum = Web3.to_checksum_address(to)
        nonce = self._w3.eth.get_transaction_count(self._account.address)

        tx_params: Dict[str, Any] = {
            "from": self._account.address,
            "to": to_checksum,
            "value": value,
            "nonce": nonce,
            "chainId": self.chain_id,
            "data": data,
        }

        if gas is not None:
            tx_params["gas"] = gas
        else:
            tx_params["gas"] = self._w3.eth.estimate_gas(tx_params)

        if max_fee_per_gas is not None:
            tx_params["maxFeePerGas"] = max_fee_per_gas
        if max_priority_fee_per_gas is not None:
            tx_params["maxPriorityFeePerGas"] = max_priority_fee_per_gas

        signed = self._account.sign_transaction(tx_params)
        tx_hash = self._w3.eth.send_raw_transaction(signed.raw_transaction)
        logger.info("Transaction sent: %s", tx_hash.hex())

        receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash)
        logger.info(
            "Transaction %s confirmed in block %d (status=%s)",
            tx_hash.hex(),
            receipt["blockNumber"],
            receipt["status"],
        )
        return receipt

    # ------------------------------------------------------------ contracts

    def get_contract(self, address: str, abi: list) -> Any:
        """Return a :class:`web3.eth.Contract` instance for the given ABI."""
        checksum = Web3.to_checksum_address(address)
        return self._w3.eth.contract(address=checksum, abi=abi)

    def call_function(
        self,
        contract_address: str,
        abi: list,
        function_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Invoke a read-only (view/pure) smart-contract function.

        Example::

            total = client.call_function(
                "0xAbC...123",
                erc20_abi,
                "totalSupply",
            )
        """
        contract = self.get_contract(contract_address, abi)
        fn = contract.functions[function_name](*args, **kwargs)
        return fn.call()

    def transact_function(
        self,
        contract_address: str,
        abi: list,
        function_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> TxReceipt:
        """Send a state-changing smart-contract transaction.

        Returns the transaction receipt.
        """
        if self._account is None:
            raise BlockchainError(
                "No private key configured; cannot sign transactions"
            )
        self.assert_connected()

        contract = self.get_contract(contract_address, abi)
        fn = contract.functions[function_name](*args, **kwargs)

        tx = fn.build_transaction({
            "from": self._account.address,
            "chainId": self.chain_id,
            "nonce": self._w3.eth.get_transaction_count(self._account.address),
        })

        signed = self._account.sign_transaction(tx)
        tx_hash = self._w3.eth.send_raw_transaction(signed.raw_transaction)
        logger.info(
            "Contract tx %s sent to %s.%s",
            tx_hash.hex(),
            contract_address[:10],
            function_name,
        )

        receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt["status"] != 1:
            raise TransactionError(
                f"Transaction {tx_hash.hex()} reverted (status=0)"
            )
        return receipt

    # ------------------------------------------------------------ ERC-20 helpers

    ERC20_ABI = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function",
        },
        {
            "constant": False,
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"},
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function",
        },
    ]

    def erc20_balance(self, token_address: str, holder: str) -> int:
        """Return the ERC-20 balance of *holder* (in token's smallest unit)."""
        return int(
            self.call_function(
                token_address, self.ERC20_ABI, "balanceOf", Web3.to_checksum_address(holder)
            )
        )

    def erc20_decimals(self, token_address: str) -> int:
        """Return the decimal precision of an ERC-20 token."""
        return int(self.call_function(token_address, self.ERC20_ABI, "decimals"))

    def erc20_symbol(self, token_address: str) -> str:
        """Return the symbol of an ERC-20 token."""
        return str(self.call_function(token_address, self.ERC20_ABI, "symbol"))

    def erc20_transfer(
        self, token_address: str, to: str, amount: int
    ) -> TxReceipt:
        """Transfer *amount* of an ERC-20 token to *to* (unsigned int amount)."""
        return self.transact_function(
            token_address, self.ERC20_ABI, "transfer",
            Web3.to_checksum_address(to), amount,
        )
