from re import T
from brownie import GwinProtocol, GwinToken, network, exceptions
from pyparsing import null_debug_action
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, INITIAL_VALUE, DECIMALS, get_account, get_contract, rounded, roundedDec, extra_rounded, rnd
from scripts.deploy import deploy_gwin_protocol_and_gwin_token
from web3 import Web3
import pytest

def test_use_protocol():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act

    parent_id = 1
    pool_type = 0 # classic type pool
    pool_h_rate = 100_0000000000 # 2x leverage
    pool_c_rate = -100_0000000000 # stable

    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(20, "ether")})
    tx.wait(1)
    pool_2x_id = 0

    parent_id = 1
    pool_type = 0 # classic type pool
    pool_h_rate = 400_0000000000 # 5x leverage
    pool_c_rate = -100_0000000000 # stable

    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(20, "ether")})
    tx.wait(1)
    pool_5x_id = 1

    parent_id = 1
    pool_type = 0 # classic type pool
    pool_h_rate = 900_0000000000 # 10x leverage
    pool_c_rate = -100_0000000000 # stable

    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(20, "ether")})
    tx.wait(1)
    pool_10x_id = 2
    
    eth_usd, last_eth = gwin_protocol.retrieveProtocolEthPrice(pool_10x_id)
    assert eth_usd == 1000_00000000
    assert last_eth == 1000_00000000

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_10x_id, {"from": account}) == 2_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_10x_id, {"from": account}) == 18_000000000000000000 # hEth in protocol

    assert gwin_protocol.retrieveCEthBalance.call(pool_10x_id, account.address, {"from": account}) == 2_000000000000000000 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_10x_id, account.address, {"from": account}) == 100_0000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_10x_id, account.address, {"from": account}) == 18_000000000000000000 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_10x_id, account.address, {"from": account}) == 100_0000000000 # hEth % for account 

    eth_usd, last_eth = gwin_protocol.retrieveProtocolEthPrice(pool_10x_id)
    assert eth_usd == 1000_00000000
    assert last_eth == 1000_00000000

    valOne, valTwo = gwin_protocol.simulateInteract.call(pool_10x_id, 1000_00000000)
    assert valOne == 2_000000000000000000
    assert valTwo == 18_000000000000000000