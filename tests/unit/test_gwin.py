from brownie import GwinProtocol, GwinToken, network, exceptions
from pyparsing import null_debug_action
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, INITIAL_PRICE_FEED_VALUE, DECIMALS, get_account, get_contract, rounded
from scripts.deploy import deploy_gwin_protocol_and_gwin_token
from web3 import Web3
import pytest

def test_get_account():
    account = get_account()
    assert account

def test_interaction():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20 = deploy_gwin_protocol_and_gwin_token()
    # Act
    # Assert
    value = gwin_protocol.test.call(1000,1100,10,10,{"from": account})
    assert rounded(value[0]) == 1045
    assert rounded(value[1]) == 954
    assert rounded(value[2]) == 2000
    value = gwin_protocol.test.call(1000,900,10,10,{"from": account})
    assert rounded(value[0]) == 944
    assert rounded(value[1]) == 1055
    assert rounded(value[2]) == 2000
    value = gwin_protocol.test.call(1000,750,10,10,{"from": account})
    assert rounded(value[0]) == 833
    assert rounded(value[1]) == 1166
    assert rounded(value[2]) == 2000
    value = gwin_protocol.test.call(1000,1511,10,10,{"from": account})
    assert rounded(value[0]) == 1169
    assert rounded(value[1]) == 830
    assert rounded(value[2]) == 2000
    value = gwin_protocol.test.call(1000,2888,10,10,{"from": account})
    assert rounded(value[0]) == 1326
    assert rounded(value[1]) == 673
    assert rounded(value[2]) == 2000

def test_uneven():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20 = deploy_gwin_protocol_and_gwin_token()
    # Act
    # Assert
    value = gwin_protocol.test.call(1000,1200,18,20,{"from": account})
    assert rounded(value[0]) == 1958
    assert rounded(value[1]) == 1841
    assert rounded(value[2]) == 3800
    value = gwin_protocol.test.call(500,300,25,12,{"from": account})
    assert rounded(value[0]) == 1807
    assert rounded(value[1]) == 1892
    assert rounded(value[2]) == 3700
    value = gwin_protocol.test.call(10500,7124,100,12,{"from": account})
    assert rounded(value[0]) == 7853
    assert rounded(value[1]) == 3346
    assert rounded(value[2]) == 11200

def test_can_deploy_ERC20():
    account = get_account()
    gwin_ERC20 = GwinToken.deploy({"from": account})
    assert gwin_ERC20

def test_stake_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20 = deploy_gwin_protocol_and_gwin_token()
    # Act
    gwin_protocol.addAllowedTokens(gwin_ERC20.address, {"from": account})
    gwin_ERC20.approve(gwin_protocol.address, Web3.toWei(1, "ether"), {"from": account})
    gwin_protocol.stakeTokens(Web3.toWei(1, "ether"), gwin_ERC20.address, {"from": account})
    # Assert
    assert gwin_protocol.stakingBalance(gwin_ERC20.address, account.address) == Web3.toWei(1, "ether")
    assert gwin_protocol.stakers(0) == account.address

def test_initialize_protocol():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20 = deploy_gwin_protocol_and_gwin_token()
    # Act
    gwin_protocol.initializeProtocol({"from": account, "value": Web3.toWei(1, "ether")})
    # Assert
    assert gwin_protocol.retrieveBalance({"from": account}) == 500000000000000000