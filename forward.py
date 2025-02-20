import copy
from decimal import Decimal

from algo import naive_algorithm
from pools import generate_assets_and_pools
from reward import get_rewards
from simulator import Simulator
from src.forest_allocation import RandomForestAllocation
from src.sgd_allocation import SGDAllocation

model = RandomForestAllocation()
sgd = SGDAllocation()



def query_and_score(
        allocations,
        assets_and_pools):
    simulator = Simulator()
    simulator.initialize()

    if assets_and_pools is not None:
        simulator.init_data(init_assets_and_pools=copy.deepcopy(assets_and_pools))
    else:
        simulator.init_data()
        assets_and_pools = simulator.assets_and_pools

    # Adjust the scores based on allocations from engine
    apys, max_apy = get_rewards(
        simulator,
        allocations,
        assets_and_pools=assets_and_pools
    )

    # print(f"apys: {apys}")
    # print(f"max_apy:\n{max_apy}")
    return apys, max_apy


def convert_pool(asset_and_pools, e=1e18):
    new_pools = {'0': {}, '1': {}, '2': {}, '3': {}, '4': {}, '5': {}, '6': {}, '7': {}, '8': {}, '9': {}}
    new_asset_and_pools = {'total_assets': asset_and_pools['total_assets'] / e, 'pools': new_pools}
    for x, pools in asset_and_pools['pools'].items():
        new_asset_and_pools['pools'][x]['base_slope'] = pools.base_slope / e
        new_asset_and_pools['pools'][x]['kink_slope'] = pools.kink_slope / e
        new_asset_and_pools['pools'][x]['optimal_util_rate'] = pools.optimal_util_rate / e
        new_asset_and_pools['pools'][x]['borrow_amount'] = pools.borrow_amount / e
        new_asset_and_pools['pools'][x]['reserve_size'] = pools.reserve_size / e
        new_asset_and_pools['pools'][x]['base_rate'] = pools.base_rate / e
    # print(f"============>>> updated new_asset_and_pools:: {new_asset_and_pools}")
    return new_asset_and_pools


def convert_allocation(allocation, e=1e18):
    final_allocation = {str(k): float(Decimal(str(float(v) * e))) for k, v in allocation.items()}
    return final_allocation


def calc_simple_allocations(assets_and_pools):
    pools = assets_and_pools['pools']
    total_asset = assets_and_pools['total_assets']
    simple_allocations = {k: total_asset / len(pools) for k, v in pools.items()}
    return simple_allocations




def compare():
    assets_and_pools = generate_assets_and_pools()

    naive_allocations = naive_algorithm(assets_and_pools)

    model_allocation = model.predict_allocation(convert_pool(assets_and_pools), model='old')

    # TODO:
    # Call your allocation solution here and add to allocation_list to compare the result with naive_allocations
    # and model_allocation
    allocation_list = [naive_allocations, convert_allocation(model_allocation)]
    apys, max_apy = query_and_score(
        allocation_list,
        assets_and_pools)

    return apys


if __name__ == '__main__':
    ...
