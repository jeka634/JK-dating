from dataclasses import dataclass
from typing import Optional

import httpx

from app.config.settings import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TonWalletInfo:
    address: str
    balance_nano: int
    balance_jk: float
    is_connected: bool


class TonConnectService:
    """TON Connect module for wallet integration and $JK token balance."""

    JK_DECIMALS = 9

    def __init__(self) -> None:
        self.network = settings.ton_network
        self.api_key = settings.ton_api_key
        self.jk_contract = settings.jk_token_contract
        if self.network == "mainnet":
            self.base_url = "https://toncenter.com/api/v2"
        else:
            self.base_url = "https://testnet.toncenter.com/api/v2"

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def validate_address(self, address: str) -> bool:
        if not address or len(address) < 48:
            return False
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/detectAddress",
                    params={"address": address},
                    headers=self._headers(),
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("ok", False)
        except Exception as exc:
            logger.error("ton_validate_address_error", error=str(exc))
        return address.startswith("EQ") or address.startswith("UQ")

    async def get_wallet_balance(self, address: str) -> int:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/getAddressBalance",
                    params={"address": address},
                    headers=self._headers(),
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        return int(data.get("result", 0))
        except Exception as exc:
            logger.error("ton_balance_error", error=str(exc))
        return 0

    async def get_jk_token_balance(self, wallet_address: str) -> float:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.base_url}/runGetMethod",
                    json={
                        "address": self.jk_contract,
                        "method": "get_wallet_address",
                        "stack": [
                            ["tvm.Slice", wallet_address],
                        ],
                    },
                    headers=self._headers(),
                )
                if response.status_code != 200:
                    return await self._get_jetton_balance_fallback(wallet_address)

                data = response.json()
                if not data.get("ok"):
                    return await self._get_jetton_balance_fallback(wallet_address)

                stack = data.get("result", {}).get("stack", [])
                if not stack:
                    return 0.0

                jetton_wallet = stack[0][1].get("object", {}).get("data", {}).get(
                    "bytes", ""
                )
                if not jetton_wallet:
                    return await self._get_jetton_balance_fallback(wallet_address)

                balance_response = await client.post(
                    f"{self.base_url}/runGetMethod",
                    json={
                        "address": jetton_wallet,
                        "method": "get_wallet_data",
                        "stack": [],
                    },
                    headers=self._headers(),
                )
                if balance_response.status_code == 200:
                    balance_data = balance_response.json()
                    if balance_data.get("ok"):
                        balance_stack = balance_data.get("result", {}).get("stack", [])
                        if balance_stack:
                            raw_balance = int(balance_stack[0][1], 16) if isinstance(
                                balance_stack[0][1], str
                            ) else int(balance_stack[0][1])
                            return raw_balance / (10 ** self.JK_DECIMALS)
        except Exception as exc:
            logger.error("ton_jk_balance_error", error=str(exc))

        return await self._get_jetton_balance_fallback(wallet_address)

    async def _get_jetton_balance_fallback(self, wallet_address: str) -> float:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/getTransactions",
                    params={
                        "address": wallet_address,
                        "limit": 1,
                    },
                    headers=self._headers(),
                )
                if response.status_code == 200:
                    return 0.0
        except Exception as exc:
            logger.error("ton_jetton_fallback_error", error=str(exc))
        return 0.0

    async def get_wallet_info(
        self, address: Optional[str]
    ) -> TonWalletInfo:
        if not address:
            return TonWalletInfo(
                address="",
                balance_nano=0,
                balance_jk=0.0,
                is_connected=False,
            )

        balance_nano = await self.get_wallet_balance(address)
        balance_jk = await self.get_jk_token_balance(address)

        return TonWalletInfo(
            address=address,
            balance_nano=balance_nano,
            balance_jk=balance_jk,
            is_connected=True,
        )

    def generate_connect_url(self, bot_username: str, user_id: int) -> str:
        return (
            f"https://app.tonkeeper.com/ton-connect"
            f"?v=2&app={bot_username}&id={user_id}"
        )

    async def verify_payment(
        self, tx_hash: str, expected_amount: float, recipient: str
    ) -> bool:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/getTransactions",
                    params={"address": recipient, "limit": 10},
                    headers=self._headers(),
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        for tx in data.get("result", []):
                            if tx.get("transaction_id", {}).get("hash") == tx_hash:
                                return True
        except Exception as exc:
            logger.error("ton_verify_payment_error", error=str(exc))
        return False
