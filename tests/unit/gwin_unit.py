from distutils.util import change_root
import brownie
from brownie import GwinProtocol, GwinToken, network, exceptions
from pyparsing import null_debug_action
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, INITIAL_PRICE_FEED_VALUE, DECIMALS, get_account, get_contract, rounded, roundedDec, extra_rounded, rnd, short_round, deploy_mock_protocol_in_use
from scripts.deploy import deploy_gwin_protocol_and_gwin_token
from web3 import Web3
import pytest

# def test_get_account():
#     account = get_account()
#     assert account

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
#     assert gwin_protocol.retrieveCEthPercentBalance.call(account.address, {"from": account}) == 1000000000000 # cEth % for account
#     assert gwin_protocol.retrieveHEthPercentBalance.call(account.address, {"from": account}) == 1000000000000 # hEth % for account
#     assert gwin_protocol.retrieveCEthBalance.call(account.address, {"from": account}) == 10000000000000000000 # cEth for account
#     assert gwin_protocol.retrieveHEthBalance.call(account.address, {"from": account}) == 10000000000000000000 # hEth for account

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
#     assert short_round(value[0]) == 1958
#     assert short_round(value[1]) == 1841
#     assert short_round(value[2]) == 3800
#     value = gwin_protocol.test.call(500,300,25,12,{"from": account})
#     assert short_round(value[0]) == 1807
#     assert short_round(value[1]) == 1892
#     assert short_round(value[2]) == 3700
#     value = gwin_protocol.test.call(10500,7124,100,12,{"from": account})
#     assert short_round(value[0]) == 7853
#     assert short_round(value[1]) == 3346
#     assert short_round(value[2]) == 11200

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
#     assert short_round(value[0]) == 1045 # heated
#     assert short_round(value[1]) == 954 # cooled
#     assert short_round(value[2]) == 2000 # total
#     value = gwin_protocol.test.call(1000,900,10,10,{"from": account})
#     assert short_round(value[0]) == 944
#     assert short_round(value[1]) == 1055
#     assert short_round(value[2]) == 2000
#     value = gwin_protocol.test.call(1000,750,10,10,{"from": account})
#     assert short_round(value[0]) == 833
#     assert short_round(value[1]) == 1166
#     assert short_round(value[2]) == 2000
#     value = gwin_protocol.test.call(1000,1511,10,10,{"from": account})
#     assert short_round(value[0]) == 1169
#     assert short_round(value[1]) == 830
#     assert short_round(value[2]) == 2000
#     value = gwin_protocol.test.call(1000,2888,10,10,{"from": account})
#     assert short_round(value[0]) == 1326
#     assert short_round(value[1]) == 673
#     assert short_round(value[2]) == 2000

# def test_deploy_mock_protocol_in_use():
#     # Arrange
#     if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
#         pytest.skip("Only for local testing!")
#     account = get_account() # Protocol 
#     non_owner = get_account(index=1) # Alice
#     non_owner_two = get_account(index=2) # Bob
#     non_owner_three = get_account(index=3) # Chris
#     non_owner_four = get_account(index=4) # Dan
#     gwin_protocol, gwin_ERC20 = deploy_mock_protocol_in_use()
#     assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call({"from": account})) == 8_8804772808 # cEth in protocol
#     assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call({"from": account})) == 12_1507433794 # hEth in protocol

#     valOne, valTwo = gwin_protocol.simulateInteract.call(1300_00000000)
#     assert rounded(valTwo) == 8_8804772808
#     assert rounded(valOne) == 12_1507433794

#     assert rounded(gwin_protocol.retrieveCEthBalance.call(account.address, {"from": account})) == 8_8804772808 # cEth for account 
#     assert roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(account.address, {"from": account})) == 100_0000000000 # cEth % for account
#     assert rounded(gwin_protocol.retrieveHEthBalance.call(account.address, {"from": account})) == 11_1850633823 # hEth for account
#     assert gwin_protocol.retrieveHEthPercentBalance.call(account.address, {"from": account}) == 92_0525027407 # hEth % for account 

#     assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner.address, {"from": account})) == 0 # cEth for non_owner
#     assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # cEth % non_owner
#     assert gwin_protocol.retrieveHEthBalance.call(non_owner.address, {"from": account}) == 0 # hEth for non_owner
#     assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # hEth % for non_owner

#     assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner_two.address, {"from": account})) == 0 # cEth for account 
#     assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner_two.address, {"from": account}) == 0 # cEth % for account
#     assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner_two.address, {"from": account})) == 9656799970 # hEth for account
#     assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner_two.address, {"from": account}) == 7_9474972592 # hEth % for account 

def test_withdrawal_greater_than_user_balance():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20 = deploy_mock_protocol_in_use()
    # Act
    gwin_protocol.changeCurrentEthUsd(1000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1000_00000000;
    with pytest.raises(ValueError):
        #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
        tx = gwin_protocol.withdrawFromTranche(True, False, 100, 0, False, {"from": non_owner_two, "gasLimit": 200000000})
        tx.wait(1)

def test_zero_deposit():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20 = deploy_mock_protocol_in_use()
    # Act
    gwin_protocol.changeCurrentEthUsd(1000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1000_00000000;
    with pytest.raises(ValueError):
        #              DEPOSIT            isCooled, isHeated, cAmount, hAmount {from, msg.value}
        tx = gwin_protocol.depositToTranche(True, False, 0, 0, {"from": non_owner_two, "value": 0})
        tx.wait(1)

def test_ledger_exploit_deposit():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20 = deploy_mock_protocol_in_use()
    # Act
    gwin_protocol.changeCurrentEthUsd(1000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1000_00000000;
    with pytest.raises(ValueError):
        # Attempts to adjust ledger records without sending ETH via "value"
        #              DEPOSIT           isCooled, isHeated, cAmount, hAmount {from, msg.value}
        tx = gwin_protocol.depositToTranche(True, False, Web3.toWei(1, "ether"), 0, {"from": non_owner_two, "value": 0})
        tx.wait(1)

# Test liquidation type price change
# Test deposit after a liquidation
# Test a withdrawal greater than the balance
# ...