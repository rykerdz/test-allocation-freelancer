import copy
import time
from decimal import Decimal
from typing import Dict

import bittensor as bt

from pools import (
    POOL_TYPES,
    AaveV3DefaultInterestRatePool,
    BasePool,
    VariableInterestSturdySiloStrategy,
)
from protocol import REQUEST_TYPES, AllocateAssets


def naive_algorithm(assets_and_pools, request_type='SYNTHETIC', user_address='-0CYIJWXa6TFgkrU6gNQpaos1g3u5w3w',
                    w3=None) -> Dict:
    bt.logging.debug(f"received request type: {request_type}")
    pools = assets_and_pools["pools"]
    match request_type:
        case REQUEST_TYPES.ORGANIC:
            for uid in pools:
                match pools[uid].pool_type:
                    case POOL_TYPES.AAVE:
                        pools[uid] = AaveV3DefaultInterestRatePool(**pools[uid].dict())
                    case POOL_TYPES.STURDY_SILO:
                        pools[uid] = VariableInterestSturdySiloStrategy(
                            **pools[uid].dict()
                        )
                    case _:
                        pass

        case _:  # we assume it is a synthetic request
            for uid in pools:
                pools[uid] = BasePool(**pools[uid].dict())

    balance = assets_and_pools["total_assets"]
    pools = assets_and_pools["pools"]

    supply_rate_sum = 0
    supply_rates = {}

    # sync pool parameters by calling smart contracts on chain
    for _uid, pool in pools.items():
        match pool.pool_type:
            case POOL_TYPES.AAVE:
                pool.sync(w3)
            case POOL_TYPES.STURDY_SILO:
                pool.sync(user_address, w3)
            case _:
                pass

    # obtain supply rates of pools - aave pool and sturdy silo
    # rates are determined by making on chain calls to smart contracts
    for _uid, pool in pools.items():
        match pool.pool_type:
            case POOL_TYPES.AAVE:
                apy = pool.supply_rate(user_address, 0)
                supply_rates[pool.pool_id] = apy
                supply_rate_sum += apy
            case POOL_TYPES.STURDY_SILO:
                apy = pool.supply_rate(0)
                supply_rates[pool.pool_id] = apy
                supply_rate_sum += apy
            case POOL_TYPES.SYNTHETIC:
                apy = pool.supply_rate
                supply_rates[pool.pool_id] = apy
                supply_rate_sum += apy
            case _:
                pass

    current_allocations = {
        pool_uid: float(round_down(Decimal(str(supply_rates[pool_uid] / supply_rate_sum))) * Decimal(str(balance)))
        for pool_uid, _ in pools.items()
    }

    return current_allocations


def round_down(value, index=100000000):
    return ((Decimal(str(index)) * value) // Decimal('1')) / Decimal(str(index))


def simple_allocation_algorithm(synapse: AllocateAssets) -> Dict:
    bt.logging.info("start simple_allocation_algorithm")
    pools = synapse.assets_and_pools["pools"]
    current_allocations = {k: v["borrow_amount"] for k, v in pools.items()}
    return current_allocations




