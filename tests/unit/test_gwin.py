from brownie import GwinProtocol, GwinToken, network, exceptions
from pyparsing import null_debug_action
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, INITIAL_PRICE_FEED_VALUE, DECIMALS, get_account, get_contract, rounded
from scripts.deploy import deploy_gwin_protocol_and_gwin_token
from web3 import Web3
import pytest

# def test_get_account():
#     account = get_account()
#     assert account

# def test_interaction():
#     # Arrange
#     if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
#         pytest.skip("Only for local testing!")
#     account = get_account()
#     non_owner = get_account(index=1)
#     gwin_protocol, gwin_ERC20 = deploy_gwin_protocol_and_gwin_token()
#     # Act
#     # Assert
#     value = gwin_protocol.test.call(1000,1100,10,10,{"from": account})
#     assert rounded(value[0]) == 1045 # heated
#     assert rounded(value[1]) == 954 # cooled
#     assert rounded(value[2]) == 2000 # total
#     value = gwin_protocol.test.call(1000,900,10,10,{"from": account})
#     assert rounded(value[0]) == 944
#     assert rounded(value[1]) == 1055
#     assert rounded(value[2]) == 2000
#     value = gwin_protocol.test.call(1000,750,10,10,{"from": account})
#     assert rounded(value[0]) == 833
#     assert rounded(value[1]) == 1166
#     assert rounded(value[2]) == 2000
#     value = gwin_protocol.test.call(1000,1511,10,10,{"from": account})
#     assert rounded(value[0]) == 1169
#     assert rounded(value[1]) == 830
#     assert rounded(value[2]) == 2000
#     value = gwin_protocol.test.call(1000,2888,10,10,{"from": account})
#     assert rounded(value[0]) == 1326
#     assert rounded(value[1]) == 673
#     assert rounded(value[2]) == 2000

# def test_uneven():
#     # Arrange
#     if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
#         pytest.skip("Only for local testing!")
#     account = get_account()
#     non_owner = get_account(index=1)
#     gwin_protocol, gwin_ERC20 = deploy_gwin_protocol_and_gwin_token()
#     # Act
#     # Assert
#     value = gwin_protocol.test.call(1000,1200,18,20,{"from": account})
#     assert rounded(value[0]) == 1958
#     assert rounded(value[1]) == 1841
#     assert rounded(value[2]) == 3800
#     value = gwin_protocol.test.call(500,300,25,12,{"from": account})
#     assert rounded(value[0]) == 1807
#     assert rounded(value[1]) == 1892
#     assert rounded(value[2]) == 3700
#     value = gwin_protocol.test.call(10500,7124,100,12,{"from": account})
#     assert rounded(value[0]) == 7853
#     assert rounded(value[1]) == 3346
#     assert rounded(value[2]) == 11200

# def test_can_deploy_ERC20():
#     account = get_account()
#     gwin_ERC20 = GwinToken.deploy({"from": account})
#     assert gwin_ERC20

# def test_stake_tokens():
#     # Arrange
#     if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
#         pytest.skip("Only for local testing!")
#     account = get_account()
#     non_owner = get_account(index=1)
#     gwin_protocol, gwin_ERC20 = deploy_gwin_protocol_and_gwin_token()
#     # Act
#     gwin_protocol.addAllowedTokens(gwin_ERC20.address, {"from": account})
#     gwin_ERC20.approve(gwin_protocol.address, Web3.toWei(1, "ether"), {"from": account})
#     gwin_protocol.stakeTokens(Web3.toWei(1, "ether"), gwin_ERC20.address, {"from": account})
#     # Assert
#     assert gwin_protocol.stakingBalance(gwin_ERC20.address, account.address) == Web3.toWei(1, "ether")
#     assert gwin_protocol.stakers(0) == account.address

# def test_initialize_protocol():
#     # Arrange
#     if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
#         pytest.skip("Only for local testing!")
#     account = get_account()
#     non_owner = get_account(index=1)
#     gwin_protocol, gwin_ERC20 = deploy_gwin_protocol_and_gwin_token()
#     # Act
#     gwin_protocol.initializeProtocol({"from": account, "value": Web3.toWei(20, "ether")})
#     # Assert
#     assert gwin_protocol.retrieveProtocolCEthBalance.call({"from": account}) == 10000000000000000000 # cEth in protocol
#     assert gwin_protocol.retrieveProtocolHEthBalance.call({"from": account}) == 10000000000000000000 # hEth in protocol
#     assert gwin_protocol.retrieveCEthPercentBalance.call({"from": account}) == 10000 # cEth % for account
#     assert gwin_protocol.retrieveHEthPercentBalance.call({"from": account}) == 10000 # hEth % for account
#     assert gwin_protocol.retrieveCEthBalance.call({"from": account}) == 10000000000000000000 # cEth for account
#     assert gwin_protocol.retrieveHEthBalance.call({"from": account}) == 10000000000000000000 # hEth for account

def test_use_protocol():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20 = deploy_gwin_protocol_and_gwin_token()
    # Act
    txTwo = gwin_protocol.initializeProtocol({"from": account, "value": Web3.toWei(20, "ether")})
    txTwo.wait(1)
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call({"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call({"from": account}) == 10000000000000000000 # hEth in protocol

    assert gwin_protocol.retrieveCEthBalance.call(0, {"from": account}) == 10000000000000000000 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, {"from": account}) == 10000 # cEth % for account
    assert gwin_protocol.retrieveHEthBalance.call(0, {"from": account}) == 10000000000000000000 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, {"from": account}) == 10000 # hEth % for account 

    # with pytest.raises(exceptions.VirtualMachineError):
    #     gwin_protocol.retrieveHEthPercentBalance.call(1, {"from": account}) == 0 # hEth % for non_owner

    # Act
    gwin_protocol.changeCurrentEthUsd(1200, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 120000000000;
    # Act
    txThree = gwin_protocol.depositToTranche(True, {"from": non_owner, "value": Web3.toWei(1, "ether")})
    txThree.wait(1)
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call({"from": account})) == 1016 # cEth in protocol
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call({"from": account})) == 1083 # hEth in protocol

    assert gwin_protocol.retrieveCEthBalance.call(0, {"from": account}) == 9166666666666666666 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, {"from": account}) == 9016 # cEth % for account
    assert gwin_protocol.retrieveHEthBalance.call(0, {"from": account}) == 10833333333333333333 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, {"from": account}) == 10000 # hEth % for account 

    assert gwin_protocol.retrieveCEthBalance.call(1, {"from": account}) == 1000000000000000000 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(1, {"from": account}) == 983 # cEth % non_owner
    assert gwin_protocol.retrieveHEthBalance.call(1, {"from": account}) == 0 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(1, {"from": account}) == 0 # hEth % for non_owner

    # Protocol rebalanced but did not update balances and percentages
    

    # x = gwin_protocol.retrieveBalance.call({"from": account})
    # print(x)
    # print(gwin_protocol.balance())
    # y = gwin_protocol.retrieveProtocolCEthBalance.call({"from": account})
    # print(y)
    # z = gwin_protocol.retrieveProtocolHEthBalance.call({"from": account})
    # print(z)
    
    # print(gwin_protocol.retrieveProtocolCEthBalance.call({"from": account}))
    # print(gwin_protocol.retrieveProtocolHEthBalance.call({"from": account}))
    # print(gwin_protocol.balance())
    # print(gwin_protocol.retrieveBalance.call({"from": account}))
    # # Assert