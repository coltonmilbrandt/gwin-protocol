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
    assert rounded(value[0]) == 10454
    assert rounded(value[1]) == 9545
    assert rounded(value[2]) == 20000
    value = gwin_protocol.test.call(1000,900,10,10,{"from": account})
    assert rounded(value[0]) == 9444
    assert rounded(value[1]) == 10555
    assert rounded(value[2]) == 20000
    value = gwin_protocol.test.call(1000,750,10,10,{"from": account})
    assert rounded(value[0]) == 8333
    assert rounded(value[1]) == 11666
    assert rounded(value[2]) == 20000
    value = gwin_protocol.test.call(1000,1511,10,10,{"from": account})
    assert rounded(value[0]) == 11690
    assert rounded(value[1]) == 8309
    assert rounded(value[2]) == 20000
    value = gwin_protocol.test.call(1000,2888,10,10,{"from": account})
    assert rounded(value[0]) == 13268
    assert rounded(value[1]) == 6731
    assert rounded(value[2]) == 20000
    # value = gwin_protocol.test.call(1000,1200,18,20,{"from": account})
    # assert rounded(value[0]) == 19587
    # assert rounded(value[1]) == 18412
    # assert rounded(value[2]) == 40000

def test_uneven():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20 = deploy_gwin_protocol_and_gwin_token()
    # Act
    # Assert
    value = gwin_protocol.test.call(1000,1200,20,20,{"from": account})
    assert rounded(value[0]) == 19587
    assert rounded(value[1]) == 18412
    assert rounded(value[2]) == 40000

def test_can_deploy_ERC20():
    account = get_account()
    gwin_ERC20 = GwinToken.deploy({"from": account})
    assert gwin_ERC20