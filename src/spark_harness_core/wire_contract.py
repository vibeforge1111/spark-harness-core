from __future__ import annotations

from dataclasses import dataclass


HARNESS_CORE_WIRE_CONTRACT_VERSION = 1
HARNESS_CORE_MIN_WIRE_CONTRACT_VERSION = 1


@dataclass(frozen=True)
class WireContractNegotiation:
    allowed: bool
    agreed_version: int | None
    reason_codes: tuple[str, ...]


def negotiate_wire_contract(
    *,
    producer_version: int,
    producer_min_version: int | None = None,
    consumer_version: int = HARNESS_CORE_WIRE_CONTRACT_VERSION,
    consumer_min_version: int | None = None,
) -> WireContractNegotiation:
    producer_min = producer_min_version if producer_min_version is not None else max(1, producer_version - 1)
    consumer_min = consumer_min_version if consumer_min_version is not None else max(1, consumer_version - 1)
    if producer_version < producer_min or consumer_version < consumer_min:
        return WireContractNegotiation(
            allowed=False,
            agreed_version=None,
            reason_codes=("wire_contract_invalid_range",),
        )

    agreed = min(producer_version, consumer_version)
    if agreed < max(producer_min, consumer_min):
        return WireContractNegotiation(
            allowed=False,
            agreed_version=None,
            reason_codes=("wire_contract_no_overlap",),
        )
    return WireContractNegotiation(allowed=True, agreed_version=agreed, reason_codes=())
