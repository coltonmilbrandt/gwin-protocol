from distutils.util import change_root
import brownie
from brownie import GwinProtocol, GwinToken, network, exceptions
from pyparsing import null_debug_action
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, INITIAL_VALUE, DECIMALS, get_account, get_contract, rounded, roundedDec, extra_rounded, rnd, short_round, deploy_mock_protocol_in_use
from scripts.deploy import deploy_gwin_protocol_and_gwin_token
from web3 import Web3
import pytest

def test_get_account():
    account = get_account()
    assert account

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
    gwin_protocol, gwin_ERC20, eth_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
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
    gwin_protocol, gwin_ERC20, eth_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    gwin_protocol.initializeProtocol({"from": account, "value": Web3.toWei(20, "ether")})
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call({"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call({"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(account.address, {"from": account}) == 10000000000000000000 # hEth for account

# Legacy math tests - Left here to archive situations that passed, since nothing has changed in the math since passing.
# NOTE: delete this if the math is adjusted
# def test_uneven():
#     # Arrange
#     if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
#         pytest.skip("Only for local testing!")
#     account = get_account()
#     non_owner = get_account(index=1)
#     gwin_protocol, gwin_ERC20, eth_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
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
#     gwin_protocol, gwin_ERC20, eth_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
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

def test_deploy_mock_protocol_in_use():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed = deploy_mock_protocol_in_use()
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call({"from": account})) == 8_8804772808 # cEth in protocol
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call({"from": account})) == 12_1507433794 # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(1300_00000000)
    assert rounded(valTwo) == 8_8804772808
    assert rounded(valOne) == 12_1507433794

    assert rounded(gwin_protocol.retrieveCEthBalance.call(account.address, {"from": account})) == 8_8804772808 # cEth for account 
    assert roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(account.address, {"from": account})) == 100_0000000000 # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(account.address, {"from": account})) == 11_1850633823 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(account.address, {"from": account}) == 92_0525027407 # hEth % for account 

    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner.address, {"from": account})) == 0 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert gwin_protocol.retrieveHEthBalance.call(non_owner.address, {"from": account}) == 0 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner_two.address, {"from": account})) == 0 # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner_two.address, {"from": account})) == 9656799970 # hEth for non_owner_two
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner_two.address, {"from": account}) == 7_9474972592 # hEth % for non_owner_two 

def test_estimate_balances():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed = deploy_mock_protocol_in_use()
    # Act
    eth_usd_price_feed.updateAnswer(1000_00000000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1000_00000000
    
    # Entire balance of non_owner_two
    rangeOfReturns = gwin_protocol.getRangeOfReturns(non_owner_two.address, False, False, True, {"from": account})
    assert rangeOfReturns[0] == 280932113371062956 # at $500/ETH
    assert rangeOfReturns[1] == 466384665201171342 # at $600/ETH
    assert rangeOfReturns[2] == 598850773651248760 # at $700/ETH
    assert rangeOfReturns[3] == 698200354988806824 # at $800/ETH
    assert rangeOfReturns[4] == 775472251583802262 # at $900/ETH
    assert rangeOfReturns[5] == 837289768860593363 # at $1000/ETH
    assert rangeOfReturns[6] == 887867737541604263 # at $1100/ETH
    assert rangeOfReturns[7] == 930016044775780014 # at $1200/ETH
    assert rangeOfReturns[8] == 965679997050240457 # at $1300/ETH
    assert rangeOfReturns[9] == 994805741012481654 # at $1400/ETH
    assert rangeOfReturns[10] == 1020048052446424025 # at $1500/ETH

    # Heated balance of non_owner_two
    rangeOfReturns = gwin_protocol.getRangeOfReturns(non_owner_two.address, False, True, False, {"from": account})
    assert rangeOfReturns[0] == 280932113371062956 # at $500/ETH
    assert rangeOfReturns[1] == 466384665201171342 # at $600/ETH
    assert rangeOfReturns[2] == 598850773651248760 # at $700/ETH
    assert rangeOfReturns[3] == 698200354988806824 # at $800/ETH
    assert rangeOfReturns[4] == 775472251583802262 # at $900/ETH
    assert rangeOfReturns[5] == 837289768860593363 # at $1000/ETH
    assert rangeOfReturns[6] == 887867737541604263 # at $1100/ETH
    assert rangeOfReturns[7] == 930016044775780014 # at $1200/ETH
    assert rangeOfReturns[8] == 965679997050240457 # at $1300/ETH
    assert rangeOfReturns[9] == 994805741012481654 # at $1400/ETH
    assert rangeOfReturns[10] == 1020048052446424025 # at $1500/ETH

    # Cooled balance of non_owner_two
    rangeOfReturns = gwin_protocol.getRangeOfReturns(non_owner_two.address, True, False, False, {"from": account})
    assert rangeOfReturns[0] == 0 # at $500/ETH
    assert rangeOfReturns[1] == 0 # at $600/ETH
    assert rangeOfReturns[2] == 0 # at $700/ETH
    assert rangeOfReturns[3] == 0 # at $800/ETH
    assert rangeOfReturns[4] == 0 # at $900/ETH
    assert rangeOfReturns[5] == 0 # at $1000/ETH
    assert rangeOfReturns[6] == 0 # at $1100/ETH
    assert rangeOfReturns[7] == 0 # at $1200/ETH
    assert rangeOfReturns[8] == 0 # at $1300/ETH
    assert rangeOfReturns[9] == 0 # at $1400/ETH
    assert rangeOfReturns[10] == 0 # at $1500/ETH

    # Cooled balance of account
    rangeOfReturns = gwin_protocol.getRangeOfReturns(account.address, True, False, False, {"from": account})
    assert rangeOfReturns[0] == 17496370578385007258 # at $500/ETH
    assert rangeOfReturns[1] == 15162899476969674201 # at $600/ETH
    assert rangeOfReturns[4] == 11273780974610785771 # at $900/ETH
    assert rangeOfReturns[6] == 9859556064653008159 # at $1100/ETH
    assert rangeOfReturns[10] == 8196387011636940558 # at $1500/ETH

    # Heated balance of account
    rangeOfReturns = gwin_protocol.getRangeOfReturns(account.address, False, True, False, {"from": account})
    assert rangeOfReturns[0] == 3253917968465402192 # at $500/ETH
    assert rangeOfReturns[1] == 5401936518059627002 # at $600/ETH
    assert rangeOfReturns[4] == 8981967434039773630 # at $900/ETH
    assert rangeOfReturns[6] == 10283796858038133161 # at $1100/ETH
    assert rangeOfReturns[10] == 11814785596154074473 # at $1500/ETH

    # Entire balance of account
    rangeOfReturns = gwin_protocol.getRangeOfReturns(account.address, False, False, True, {"from": account})
    assert rangeOfReturns[0] == 20750288546850409450 # at $500/ETH
    assert rangeOfReturns[1] == 20564835995029301203 # at $600/ETH
    assert rangeOfReturns[4] == 20255748408650559401 # at $900/ETH
    assert rangeOfReturns[6] == 20143352922691141320 # at $1100/ETH
    assert rangeOfReturns[10] == 20011172607791015031 # at $1500/ETH

def test_withdrawal_greater_than_user_balance():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed = deploy_mock_protocol_in_use()
    # Act
    eth_usd_price_feed.updateAnswer(1000_00000000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1000_00000000
    with pytest.raises(ValueError):
        #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
        tx = gwin_protocol.withdrawFromTranche(True, False, 10, 0, False, {"from": non_owner_two, "gasLimit": 200000000})
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
    gwin_protocol, gwin_ERC20, eth_usd_price_feed = deploy_mock_protocol_in_use()
    # Act
    eth_usd_price_feed.updateAnswer(1000_00000000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1000_00000000
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
    gwin_protocol, gwin_ERC20, eth_usd_price_feed = deploy_mock_protocol_in_use()
    # Act
    eth_usd_price_feed.updateAnswer(1000_00000000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1000_00000000
    with pytest.raises(ValueError):
        # Attempts to adjust ledger records without sending ETH via "value"
        #              DEPOSIT           isCooled, isHeated, cAmount, hAmount {from, msg.value}
        tx = gwin_protocol.depositToTranche(True, False, Web3.toWei(1, "ether"), 0, {"from": non_owner_two, "value": 0})
        tx.wait(1)

def test_zero_withdrawal():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed = deploy_mock_protocol_in_use()
    # Act
    eth_usd_price_feed.updateAnswer(1000_00000000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1000_00000000
    with pytest.raises(ValueError):
        #              WITHDRAWAL        isCooled, isHeated, cAmount, hAmount, isAll, {from, msg.value}
        tx = gwin_protocol.withdrawFromTranche(True, False, 0, 0, False, {"from": non_owner})
        tx.wait(1)

def test_cannot_initialize_after_initialized():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    tx = gwin_protocol.initializeProtocol({"from": account, "value": Web3.toWei(20, "ether")})
    tx.wait(1)
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call({"from": account}) == 10_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call({"from": account}) == 10_000000000000000000 # hEth in protocol

    assert gwin_protocol.retrieveCEthBalance.call(account.address, {"from": account}) == 10_000000000000000000 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(account.address, {"from": account}) == 100_0000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthBalance.call(account.address, {"from": account}) == 10_000000000000000000 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(account.address, {"from": account}) == 100_0000000000 # hEth % for account 

    valOne, valTwo = gwin_protocol.simulateInteract.call(1000_00000000)
    assert valOne == 10_000000000000000000
    assert valTwo == 10_000000000000000000
    
    with pytest.raises(ValueError):
        tx = gwin_protocol.initializeProtocol({"from": account, "value": Web3.toWei(20, "ether")})
        tx.wait(1)

def test_cannot_deposit_before_initialized():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    eth_usd_price_feed.updateAnswer(1200_00000000, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1200_00000000
    # Act
    ################### tx1 ###################
    # Assert
    with pytest.raises(ValueError):
        #                                     isCooled, isHeated, cAmount, hAmount {from, msg.value}
        tx = gwin_protocol.depositToTranche(True, False, Web3.toWei(1, "ether"), 0, {"from": non_owner, "value": Web3.toWei(1, "ether")})
        tx.wait(1)

def test_cannot_readjust_without_tx():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    eth_usd_price_feed.updateAnswer(1200_00000000, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1200_00000000
    # Act
    ################### tx1 ###################
    # Assert
    possible_inputs = [
        [True, True, True],
        [True, True, False],
        [True, False, True],
        [True, False, False],
        [False, False, False],
        [False, False, True],
        [False, True, False],
        [False, True, True]
    ]

    for x in possible_inputs:
        with pytest.raises(AttributeError):
            tx = gwin_protocol.reAdjust.call(possible_inputs[x])
            tx.wait(1)


def test_unbalanced_hot_cold_ratio():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed = deploy_mock_protocol_in_use()
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1300_00000000
    # Act
    eth_usd_price_feed.updateAnswer(1000_00000000, {"from": account}) # Started at 1300

    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(True, False, Web3.toWei(8, "ether"), 0, False, {"from": account})
    tx.wait(1)
    
    # Assert
    valOne, valTwo = gwin_protocol.simulateInteract.call(1000_00000000)
    assert rounded(valTwo) == 2_4959572741
    assert rounded(valOne) == 10_5352633861

    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call({"from": account})) == 2_4959572741 # cEth in protocol
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call({"from": account})) == 10_5352633861 # hEth in protocol

    assert rounded(gwin_protocol.retrieveCEthBalance.call(account.address, {"from": account})) == 2_4959572741 # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(account.address, {"from": account}))) == rnd(100_0000000000) # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(account.address, {"from": account})) == 9_6979736172 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(account.address, {"from": account}) == 92_0525027407 # hEth % for account 

    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner.address, {"from": account})) == 0 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert gwin_protocol.retrieveHEthBalance.call(non_owner.address, {"from": account}) == 0 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner_two.address, {"from": account})) == 0 # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner_two.address, {"from": account})) == 8372897688 # hEth for non_owner_two
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner_two.address, {"from": account}) == 7_9474972592 # hEth % for non_owner_two

    # Act
    eth_usd_price_feed.updateAnswer(1100_00000000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1100_00000000
    #              DEPOSIT          isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.depositToTranche(True, False, Web3.toWei(1, "ether"), 0, {"from": non_owner, "value": Web3.toWei(1, "ether")})
    tx.wait(1)
    # Assert
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call({"from": account})) == 3_3125127466 # cEth in protocol
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call({"from": account}))) == rnd(10_7187079136) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(1100_00000000)
    assert rounded(valTwo) == 3_3125127466
    assert rnd(rounded(valOne)) == rnd(10_7187079136)

    assert rounded(gwin_protocol.retrieveCEthBalance.call(account.address, {"from": account})) == 2_3125127466 # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(account.address, {"from": account}))) == rnd(69_8114369218) # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(account.address, {"from": account})) == 9_8668388959 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(account.address, {"from": account}) == 92_0525027407 # hEth % for account 

    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner.address, {"from": account})) == 1_0000000000 # cEth for non_owner
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(non_owner.address, {"from": account}))) == rnd(30_1885630781) # cEth % non_owner
    assert gwin_protocol.retrieveHEthBalance.call(non_owner.address, {"from": account}) == 0 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner_two.address, {"from": account})) == 0 # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner_two.address, {"from": account})) == 8518690176 # hEth for non_owner_two
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner_two.address, {"from": account}) == 7_9474972592 # hEth % for non_owner_two

    # Act
    eth_usd_price_feed.updateAnswer(800_00000000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 800_00000000
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(True, False, 0, 0, True, {"from": non_owner})
    tx.wait(1)
    # Assert
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call({"from": account})) == 3_4866854831 # cEth in protocol
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call({"from": account}))) == rnd(9_0367876033) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(800_00000000)
    assert rounded(valTwo) == 3_4866854831
    assert rnd(rounded(valOne)) == rnd(9_0367876033)

    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(account.address, {"from": account}))) == rnd(3_4866854831) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(account.address, {"from": account}))) == rnd(100_0000000000) # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(account.address, {"from": account})) == 8_3185891562 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(account.address, {"from": account}) == 92_0525027407 # hEth % for account 

    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner.address, {"from": account})) == 0 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert gwin_protocol.retrieveHEthBalance.call(non_owner.address, {"from": account}) == 0 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner_two.address, {"from": account})) == 0 # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner_two.address, {"from": account})) == 7181984470 # hEth for non_owner_two
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner_two.address, {"from": account}) == 7_9474972592 # hEth % for non_owner_two


def test_liquidation():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed = deploy_mock_protocol_in_use()
    
    valOne, valTwo = gwin_protocol.simulateInteract.call(300_00000000)
    # test_value = gwin_protocol.simulateInteract.call(300_00000000)
    # assert test_value == 0
    assert rounded(valTwo) == 210312206602
    assert rounded(valOne) == 0

def test_deposit_after_liquidation():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed = deploy_mock_protocol_in_use()
    
    valOne, valTwo = gwin_protocol.simulateInteract.call(300_00000000)
    # test_value = gwin_protocol.simulateInteract.call(300_00000000)
    # assert test_value == 0
    assert rounded(valTwo) == 210312206602
    assert rounded(valOne) == 0

    # Act
    eth_usd_price_feed.updateAnswer(300_00000000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 300_00000000
    # tx = gwin_protocol.withdrawFromTranche(True, False, 0, 0, True, {"from": account})
    tx = gwin_protocol.depositToTranche(False, True, 0, Web3.toWei(1, "ether"), {"from": non_owner, "value": Web3.toWei(1, "ether")})
    tx.wait(1)
    # Assert
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call({"from": account})) == 21_0312206602 # cEth in protocol
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call({"from": account})) == 1_0000000000 # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(300_00000000)
    assert rounded(valTwo) == 21_0312206602 # cEth according to simulate interact call
    assert rounded(valOne) == 1_0000000000 # hEth according to simulate interact call

    assert rounded(gwin_protocol.retrieveCEthBalance.call(account.address, {"from": account})) == 21_0312206602 # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(account.address, {"from": account}))) == rnd(100_0000000000) # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(account.address, {"from": account})) == 0 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(account.address, {"from": account}) == 0 # hEth % for account 

    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner.address, {"from": account})) == 0 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner.address, {"from": account})) == 1_0000000000 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner.address, {"from": account}) == 100_0000000000 # hEth % for non_owner

    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner_two.address, {"from": account})) == 0 # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner_two.address, {"from": account})) == 0 # hEth for non_owner_two
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner_two.address, {"from": account}) == 0 # hEth % for non_owner_two

def test_withdrawal_after_liquidation():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed = deploy_mock_protocol_in_use()
    
    valOne, valTwo = gwin_protocol.simulateInteract.call(300_00000000)
    # test_value = gwin_protocol.simulateInteract.call(300_00000000)
    # assert test_value == 0
    assert rounded(valTwo) == 210312206602
    assert rounded(valOne) == 0

    # Act
    eth_usd_price_feed.updateAnswer(300_00000000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 300_00000000
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(True, False, Web3.toWei(10, "ether"), 0, False, {"from": account})
    tx.wait(1)
    # Assert
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call({"from": account})) == 11_0312206602 # cEth in protocol
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call({"from": account})) == 0 # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(300_00000000)
    assert rounded(valTwo) == 11_0312206602 # cEth according to simulate interact call
    assert rounded(valOne) == 0 # hEth according to simulate interact call

    assert rounded(gwin_protocol.retrieveCEthBalance.call(account.address, {"from": account})) == 11_0312206602 # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(account.address, {"from": account}))) == rnd(100_0000000000) # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(account.address, {"from": account})) == 0 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(account.address, {"from": account}) == 0 # hEth % for account 

    assert gwin_protocol.retrieveAddressAtIndex.call(0, {"from": account}) == account.address

    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner.address, {"from": account})) == 0 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # hEth % for non_owner
    assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner.address, {"from": account})) == 0 # hEth for non_owner
    
    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner_two.address, {"from": account})) == 0 # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner_two.address, {"from": account})) == 0 # hEth for non_owner_two
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner_two.address, {"from": account}) == 0 # hEth % for non_owner_two