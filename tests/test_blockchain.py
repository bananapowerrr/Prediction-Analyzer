"""Tests for core.blockchain — web3 integration for Polygon / Base."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from core.blockchain import (
    BlockchainClient,
    BlockchainError,
    ConnectionError,
    TransactionError,
    SUPPORTED_CHAINS,
)


# --------------------------------------------------------------------------- construction


class TestBlockchainClientInit:
    def test_polygon_default(self):
        client = BlockchainClient(
            rpc_url="https://polygon-rpc.com",
            chain_id=137,
        )
        assert client.chain_name == "Polygon"
        assert client.chain_id == 137
        assert client.rpc_url == "https://polygon-rpc.com"

    def test_base_default(self):
        client = BlockchainClient(
            rpc_url="https://mainnet.base.org",
            chain_id=8453,
        )
        assert client.chain_name == "Base"
        assert client.chain_id == 8453

    def test_polygon_mumbai(self):
        client = BlockchainClient(
            rpc_url="https://rpc-mumbai.maticvigil.com",
            chain_id=80001,
        )
        assert client.chain_name == "Polygon Mumbai"

    def test_base_sepolia(self):
        client = BlockchainClient(
            rpc_url="https://sepolia.base.org",
            chain_id=84532,
        )
        assert client.chain_name == "Base Sepolia"

    def test_rejects_empty_rpc_url(self):
        with pytest.raises(ValueError, match="rpc_url is required"):
            BlockchainClient(rpc_url="", chain_id=137)

    def test_rejects_unsupported_chain(self):
        with pytest.raises(ValueError, match="Unsupported chain_id"):
            BlockchainClient(rpc_url="https://example.com", chain_id=1)

    def test_rejects_chain_zero(self):
        with pytest.raises(ValueError, match="Unsupported chain_id"):
            BlockchainClient(rpc_url="https://example.com", chain_id=0)

    def test_no_private_key_account_is_none(self):
        client = BlockchainClient(
            rpc_url="https://polygon-rpc.com",
            chain_id=137,
        )
        assert client._account is None


# --------------------------------------------------------------------------- connection


class TestConnection:
    def test_is_connected_returns_bool(self):
        client = BlockchainClient(
            rpc_url="https://polygon-rpc.com",
            chain_id=137,
        )
        assert isinstance(client.is_connected(), bool)

    @patch.object(BlockchainClient, "is_connected", return_value=True)
    def test_assert_connected_passes(self, _mock):
        client = BlockchainClient(
            rpc_url="https://polygon-rpc.com",
            chain_id=137,
        )
        client.assert_connected()

    @patch.object(BlockchainClient, "is_connected", return_value=False)
    def test_assert_connected_raises(self, _mock):
        client = BlockchainClient(
            rpc_url="https://polygon-rpc.com",
            chain_id=137,
        )
        with pytest.raises(ConnectionError, match="Cannot reach RPC"):
            client.assert_connected()


# --------------------------------------------------------------------------- ERC-20 helpers


class TestERC20ABI:
    def test_erc20_abi_has_required_methods(self):
        abi_names = {entry["name"] for entry in BlockchainClient.ERC20_ABI}
        assert "balanceOf" in abi_names
        assert "decimals" in abi_names
        assert "symbol" in abi_names
        assert "totalSupply" in abi_names
        assert "transfer" in abi_names


# --------------------------------------------------------------------------- w3 property


class TestW3Property:
    def test_w3_returns_web3_instance(self):
        from web3 import Web3

        client = BlockchainClient(
            rpc_url="https://polygon-rpc.com",
            chain_id=137,
        )
        assert isinstance(client.w3, Web3)


# --------------------------------------------------------------------------- supported chains


class TestSupportedChains:
    def test_polygon_mainnet(self):
        assert 137 in SUPPORTED_CHAINS
        assert SUPPORTED_CHAINS[137] == "Polygon"

    def test_polygon_mumbai(self):
        assert 80001 in SUPPORTED_CHAINS
        assert SUPPORTED_CHAINS[80001] == "Polygon Mumbai"

    def test_base_mainnet(self):
        assert 8453 in SUPPORTED_CHAINS
        assert SUPPORTED_CHAINS[8453] == "Base"

    def test_base_sepolia(self):
        assert 84532 in SUPPORTED_CHAINS
        assert SUPPORTED_CHAINS[84532] == "Base Sepolia"


# --------------------------------------------------------------------------- exceptions


class TestExceptions:
    def test_hierarchy(self):
        assert issubclass(BlockchainError, Exception)
        assert issubclass(ConnectionError, BlockchainError)
        assert issubclass(TransactionError, BlockchainError)
