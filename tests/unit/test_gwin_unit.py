from distutils.util import change_root
import brownie
from brownie import GwinProtocol, GwinToken, network, exceptions
from pyparsing import null_debug_action
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, INITIAL_VALUE, DECIMALS, get_account, get_contract, rounded, roundedDec, extra_rounded, rnd, short_round, deploy_mock_protocol_in_use, empty_account
from scripts.deploy import deploy_gwin_protocol_and_gwin_token
from web3 import Web3
import pytest

# NOTE: If you start a new instance of Ganache etc., be sure to delete the previous deployments in the build folder

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
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
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
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    eth_usd_price_feed.updateAnswer(1000_00000000, {"from": account}) 
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1000_00000000 

def test_initialize_protocol_with_positive_rates():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    # Assert
    with pytest.raises(ValueError):
        #              attempt to initialize with two positive rates
        gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", 50_0000000000, 50_0000000000, {"from": account, "value": Web3.toWei(20, "ether"), "gasLimit": 20000000000})

def test_initialize_protocol_with_negative_rates():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    # Assert
    with pytest.raises(ValueError):
        #              attempt to initialize with two positive rates
        gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, -50_0000000000, {"from": account, "value": Web3.toWei(20, "ether"), "gasLimit": 20000000000})

def test_non_owner_can_initialize():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": non_owner, "value": Web3.toWei(20, "ether")})
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(0, non_owner.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(0, non_owner.address, {"from": account}) == 10000000000000000000 # hEth for account
    eth_usd_price_feed.updateAnswer(1000_00000000, {"from": account}) 
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1000_00000000

# def test_only_owner_can_initialize():
    # CHANGED - anyone can initialize a pool now
    # # Arrange
    # if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
    #     pytest.skip("Only for local testing!")
    # account = get_account()
    # non_owner = get_account(index=1)
    # gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # # Act/Assert
    # with pytest.raises(ValueError):
    #     parent_id = 0
    #     gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": non_owner, "value": Web3.toWei(20, "ether")})

def test_deploy_mock_protocol_in_use():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_mock_protocol_in_use()
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account})) == 8_8804772808 # cEth in protocol
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account})) == 12_1507433794 # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 1300_00000000, {"from": account})
    assert rounded(valTwo) == 8_8804772808
    assert rounded(valOne) == 12_1507433794

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account})) == 8_8804772808 # cEth for account 
    assert roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account})) == 100_0000000000 # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account})) == 11_1850633823 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 92_0525027407 # hEth % for account 

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner.address, {"from": account})) == 0 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert gwin_protocol.retrieveHEthBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_two.address, {"from": account})) == 0 # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_two.address, {"from": account})) == 9656799970 # hEth for non_owner_two
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 7_9474972592 # hEth % for non_owner_two 

def test_estimate_balances():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_mock_protocol_in_use()
    # Act
    eth_usd_price_feed.updateAnswer(1000_00000000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1000_00000000
    
    # Entire balance of non_owner_two               id      address        isCooled   isAll
    rangeOfReturns = gwin_protocol.getRangeOfReturns(0, non_owner_two.address, False, True, {"from": account})
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

    # Heated balance of non_owner_two               id      address        isCooled   isAll
    rangeOfReturns = gwin_protocol.getRangeOfReturns(0, non_owner_two.address, False, False, {"from": account})
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

    # Cooled balance of non_owner_two               id      address        isCooled   isAll
    rangeOfReturns = gwin_protocol.getRangeOfReturns(0, non_owner_two.address, True, False, {"from": account})
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

    # Cooled balance of account               id      address        isCooled   isAll
    rangeOfReturns = gwin_protocol.getRangeOfReturns(0, account.address, True, False, {"from": account})
    assert rangeOfReturns[0] == 17496370578385007258 # at $500/ETH
    assert rangeOfReturns[1] == 15162899476969674201 # at $600/ETH
    assert rangeOfReturns[4] == 11273780974610785771 # at $900/ETH
    assert rangeOfReturns[6] == 9859556064653008159 # at $1100/ETH
    assert rangeOfReturns[10] == 8196387011636940558 # at $1500/ETH

    # Heated balance of account               id      address        isCooled   isAll
    rangeOfReturns = gwin_protocol.getRangeOfReturns(0, account.address, False, False, {"from": account})
    assert rangeOfReturns[0] == 3253917968465402192 # at $500/ETH
    assert rangeOfReturns[1] == 5401936518059627002 # at $600/ETH
    assert rangeOfReturns[4] == 8981967434039773630 # at $900/ETH
    assert rangeOfReturns[6] == 10283796858038133161 # at $1100/ETH
    assert rangeOfReturns[10] == 11814785596154074473 # at $1500/ETH

    # Entire balance of account               id      address        isCooled   isAll
    rangeOfReturns = gwin_protocol.getRangeOfReturns(0, account.address, False, True, {"from": account})
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
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_mock_protocol_in_use()
    # Act
    eth_usd_price_feed.updateAnswer(1000_00000000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1000_00000000
    with pytest.raises(ValueError):
        #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
        tx = gwin_protocol.withdrawFromTranche(0, True, False, 10, 0, False, {"from": non_owner_two, "gasLimit": 200000000})
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
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_mock_protocol_in_use()
    # Act
    eth_usd_price_feed.updateAnswer(1000_00000000, {"from": account}) # Started at 1300
    # Assert 
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1000_00000000
    with pytest.raises(ValueError):
        #              DEPOSIT            isCooled, isHeated, cAmount, hAmount {from, msg.value}
        tx = gwin_protocol.depositToTranche(0, True, False, 0, 0, {"from": non_owner_two, "value": 0})
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
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_mock_protocol_in_use()
    # Act
    eth_usd_price_feed.updateAnswer(1000_00000000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1000_00000000
    with pytest.raises(ValueError):
        # Attempts to adjust ledger records without sending ETH via "value"
        #              DEPOSIT           isCooled, isHeated, cAmount, hAmount {from, msg.value}
        tx = gwin_protocol.depositToTranche(0, True, False, Web3.toWei(1, "ether"), 0, {"from": non_owner_two, "value": 0})
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
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_mock_protocol_in_use()
    # Act
    eth_usd_price_feed.updateAnswer(1000_00000000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1000_00000000
    with pytest.raises(ValueError):
        #              WITHDRAWAL        isCooled, isHeated, cAmount, hAmount, isAll, {from, msg.value}
        tx = gwin_protocol.withdrawFromTranche(0, True, False, 0, 0, False, {"from": non_owner})
        tx.wait(1)

def test_can_create_second_pool():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    tx = gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    tx.wait(1)
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}) == 10_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}) == 10_000000000000000000 # hEth in protocol

    assert gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}) == 10_000000000000000000 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}) == 100_0000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}) == 10_000000000000000000 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 100_0000000000 # hEth % for account 

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 1000_00000000)
    assert valOne == 10_000000000000000000
    assert valTwo == 10_000000000000000000
    
    parent_id = 0
    tx2 = gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    tx2.wait(1)
    
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(1, {"from": account}) == 10_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(1, {"from": account}) == 10_000000000000000000 # hEth in protocol

    assert gwin_protocol.retrieveCEthBalance.call(1, account.address, {"from": account}) == 10_000000000000000000 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(1, account.address, {"from": account}) == 100_0000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthBalance.call(1, account.address, {"from": account}) == 10_000000000000000000 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(1, account.address, {"from": account}) == 100_0000000000 # hEth % for account 

    valOne, valTwo = gwin_protocol.simulateInteract.call(1, 1000_00000000)
    assert valOne == 10_000000000000000000
    assert valTwo == 10_000000000000000000

def test_cannot_deposit_before_initialized():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    eth_usd_price_feed.updateAnswer(1200_00000000, {"from": account})
    # Assert
    with brownie.reverts("Pool_Is_Not_Initialized"):
        gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1200_00000000 # no price feed set, should revert
    # Act
    ################### tx1 ###################
    # Assert
    with pytest.raises(ValueError):
        #                                     isCooled, isHeated, cAmount, hAmount {from, msg.value}
        tx = gwin_protocol.depositToTranche(0, True, False, Web3.toWei(1, "ether"), 0, {"from": non_owner, "value": Web3.toWei(1, "ether")})
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
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_mock_protocol_in_use()
    # Act
    eth_usd_price_feed.updateAnswer(1200_00000000, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1200_00000000 # no price feed set, should revert
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
            tx = gwin_protocol.reAdjust.call(0, possible_inputs[x])
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
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_mock_protocol_in_use()
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1300_00000000
    # Act
    eth_usd_price_feed.updateAnswer(1000_00000000, {"from": account}) # Started at 1300

    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(0, True, False, Web3.toWei(8, "ether"), 0, False, {"from": account})
    tx.wait(1)
    
    # Assert
    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 1000_00000000)
    assert rounded(valTwo) == 2_4959572741
    assert rounded(valOne) == 10_5352633861

    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account})) == 2_4959572741 # cEth in protocol
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account})) == 10_5352633861 # hEth in protocol

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account})) == 2_4959572741 # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}))) == rnd(100_0000000000) # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account})) == 9_6979736172 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 92_0525027407 # hEth % for account 

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner.address, {"from": account})) == 0 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert gwin_protocol.retrieveHEthBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_two.address, {"from": account})) == 0 # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_two.address, {"from": account})) == 8372897688 # hEth for non_owner_two
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 7_9474972592 # hEth % for non_owner_two

    # Act
    eth_usd_price_feed.updateAnswer(1100_00000000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1100_00000000
    #              DEPOSIT          isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.depositToTranche(0, True, False, Web3.toWei(1, "ether"), 0, {"from": non_owner, "value": Web3.toWei(1, "ether")})
    tx.wait(1)
    # Assert
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account})) == 3_3125127466 # cEth in protocol
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}))) == rnd(10_7187079136) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 1100_00000000)
    assert rounded(valTwo) == 3_3125127466
    assert rnd(rounded(valOne)) == rnd(10_7187079136)

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account})) == 2_3125127466 # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}))) == rnd(69_8114369218) # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account})) == 9_8668388959 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 92_0525027407 # hEth % for account 

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner.address, {"from": account})) == 1_0000000000 # cEth for non_owner
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner.address, {"from": account}))) == rnd(30_1885630781) # cEth % non_owner
    assert gwin_protocol.retrieveHEthBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_two.address, {"from": account})) == 0 # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_two.address, {"from": account})) == 8518690176 # hEth for non_owner_two
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 7_9474972592 # hEth % for non_owner_two

    # Act
    eth_usd_price_feed.updateAnswer(800_00000000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 800_00000000
    #              WITHDRAWAL        poolId, isCooled, isHeated, cAmount, hAmount, isAll {from, account}
    tx = gwin_protocol.withdrawFromTranche(0, True, False, 0, 0, True, {"from": non_owner})
    tx.wait(1)
    # Assert
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account})) == 3_4866854831 # cEth in protocol
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}))) == rnd(9_0367876033) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 800_00000000)
    assert rounded(valTwo) == 3_4866854831
    assert rnd(rounded(valOne)) == rnd(9_0367876033)

    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}))) == rnd(3_4866854831) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}))) == rnd(100_0000000000) # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account})) == 8_3185891562 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 92_0525027407 # hEth % for account 

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner.address, {"from": account})) == 0 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert gwin_protocol.retrieveHEthBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_two.address, {"from": account})) == 0 # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_two.address, {"from": account})) == 7181984470 # hEth for non_owner_two
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 7_9474972592 # hEth % for non_owner_two


def test_liquidation():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_mock_protocol_in_use()
    
    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 300_00000000)
    # test_value = gwin_protocol.simulateInteract.call(0, 300_00000000)
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
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_mock_protocol_in_use()
    
    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 300_00000000)
    # test_value = gwin_protocol.simulateInteract.call(0, 300_00000000)
    # assert test_value == 0
    assert rounded(valTwo) == 210312206602
    assert rounded(valOne) == 0

    # Act
    eth_usd_price_feed.updateAnswer(300_00000000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 300_00000000
    tx = gwin_protocol.depositToTranche(0, False, True, 0, Web3.toWei(1, "ether"), {"from": non_owner, "value": Web3.toWei(1, "ether")})
    tx.wait(1)
    # Assert
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account})) == 21_0312206602 # cEth in protocol
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account})) == 1_0000000000 # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 300_00000000)
    assert rounded(valTwo) == 21_0312206602 # cEth according to simulate interact call
    assert rounded(valOne) == 1_0000000000 # hEth according to simulate interact call

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account})) == 21_0312206602 # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}))) == rnd(100_0000000000) # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account})) == 0 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 0 # hEth % for account 

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner.address, {"from": account})) == 0 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner.address, {"from": account})) == 1_0000000000 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner.address, {"from": account}) == 100_0000000000 # hEth % for non_owner

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_two.address, {"from": account})) == 0 # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_two.address, {"from": account})) == 0 # hEth for non_owner_two
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # hEth % for non_owner_two

def test_withdrawal_after_liquidation():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_mock_protocol_in_use()
    
    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 300_00000000)
    # test_value = gwin_protocol.simulateInteract.call(0, 300_00000000)
    # assert test_value == 0
    assert rounded(valTwo) == 210312206602
    assert rounded(valOne) == 0

    # Act
    eth_usd_price_feed.updateAnswer(300_00000000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 300_00000000
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(0, True, False, Web3.toWei(10, "ether"), 0, False, {"from": account})
    tx.wait(1)
    # Assert
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account})) == 11_0312206602 # cEth in protocol
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account})) == 0 # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 300_00000000)
    assert rounded(valTwo) == 11_0312206602 # cEth according to simulate interact call
    assert rounded(valOne) == 0 # hEth according to simulate interact call

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account})) == 11_0312206602 # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}))) == rnd(100_0000000000) # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account})) == 0 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 0 # hEth % for account 

    assert gwin_protocol.retrieveAddressAtIndex.call(0, 0, {"from": account}) == account.address

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner.address, {"from": account})) == 0 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth % for non_owner
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner.address, {"from": account})) == 0 # hEth for non_owner
    
    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_two.address, {"from": account})) == 0 # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_two.address, {"from": account})) == 0 # hEth for non_owner_two
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # hEth % for non_owner_two

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\  XAU Long Short (-100, 100) /@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#

def test_initialize_xau_pool():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    eth_usd_price_feed.updateAnswer(1300_00000000, {"from": account})
    xau_usd_price_feed.updateAnswer(Web3.toWei(1600, "ether"), {"from": account}) 
    assert xau_usd_price_feed.decimals() == 18 
    # Act                                                       "ETH/USD"                               "XAU/USD"
    gwin_protocol.initializePool(1, eth_usd_price_feed.address, "0x455448", xau_usd_price_feed.address, "0x584155", -100_0000000000, 100_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 81250000 

    target_price = 0.85
    stable_eth = 1300
    feed_eth = 1300 * 100000000
    implied_xau_price_in_usd = stable_eth / target_price
    assert feed_eth == 1300_00000000
    assert implied_xau_price_in_usd == 1529.4117647058824
    assert Web3.toWei(implied_xau_price_in_usd, "ether") == 1529_411764705882400000
    assert stable_eth /implied_xau_price_in_usd == 0.85

    # Act
    xau_usd_price_feed.updateAnswer(Web3.toWei(implied_xau_price_in_usd, "ether"), {"from": account})
    eth_usd_price_feed.updateAnswer(feed_eth, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 85000000
    assert gwin_protocol.getProfit(0, 85000000) == 46153846 



#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\  XAU Long Short (-200, 400)  /@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#

def test_initialize_xau_pool():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    feed_eth = 1300_00000000
    assert xau_usd_price_feed.decimals() == 18 
    xau_ls_pool_id = 0
    xau_usd_price_feed.updateAnswer(Web3.toWei(1600, "ether"), {"from": account}) 
    eth_usd_price_feed.updateAnswer(feed_eth, {"from": account})

    parent_id = 0
    # Act                                                       "ETH/USD"                               "XAU/USD"
    gwin_protocol.initializePool(1, parent_id, eth_usd_price_feed.address, "0x455448", xau_usd_price_feed.address, "0x584155", -200_0000000000, 400_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(xau_ls_pool_id, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(xau_ls_pool_id, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    assert xau_usd_price_feed.decimals() == 18 
    assert gwin_protocol.retrieveCurrentPrice(xau_ls_pool_id, {"from": account}) == 81250000

    ################### XAU Set Up ###################        

    target_price = 0.85
    stable_eth = 1300
    feed_eth = 1300 * 100000000
    implied_xau_price_in_usd = stable_eth / target_price
    assert feed_eth == 1300_00000000
    assert implied_xau_price_in_usd == 1529.4117647058824
    assert Web3.toWei(implied_xau_price_in_usd, "ether") == 1529_411764705882400000
    assert stable_eth /implied_xau_price_in_usd == 0.85

    # Act
    xau_usd_price_feed.updateAnswer(Web3.toWei(implied_xau_price_in_usd, "ether"), {"from": account})
    eth_usd_price_feed.updateAnswer(feed_eth, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(xau_ls_pool_id, {"from": account}) == 85000000
    assert gwin_protocol.getProfit(xau_ls_pool_id, 85000000) == 46153846153

def test_everyone_withdraws():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_mock_protocol_in_use()
    
    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 300_00000000)
    # test_value = gwin_protocol.simulateInteract.call(0, 300_00000000)
    # assert test_value == 0
    assert rounded(valTwo) == 210312206602
    assert rounded(valOne) == 0

    # Act
    eth_usd_price_feed.updateAnswer(300_00000000, {"from": account}) # Started at 1300
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 300_00000000
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(0, True, False, 0, 0, True, {"from": account})
    tx.wait(1)
    # Assert
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account})) == 0 # cEth in protocol
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account})) == 0 # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 300_00000000)
    assert rounded(valTwo) == 0 # cEth according to simulate interact call
    assert rounded(valOne) == 0 # hEth according to simulate interact call

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account})) == 0 # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}))) == rnd(0) # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account})) == 0 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 0 # hEth % for account 

    assert gwin_protocol.retrieveAddressAtIndex.call(0, 0, {"from": account}) == account.address

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner.address, {"from": account})) == 0 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth % for non_owner
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner.address, {"from": account})) == 0 # hEth for non_owner
    
    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_two.address, {"from": account})) == 0 # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_two.address, {"from": account})) == 0 # hEth for non_owner_two
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # hEth % for non_owner_two

def test_zero_price_change_full_withdrawal():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1000_00000000 

    # Act - Withdraw all funds with zero price change
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(0, True, False, 0, 0, True, {"from": account})
    tx = gwin_protocol.withdrawFromTranche(0, False, True, 0, 0, True, {"from": account})
    tx.wait(1)

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}) == 0 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}) == 0 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 0 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}) == 0 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}) == 0 # hEth for account
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1000_00000000 

def test_full_withdrawal_then_both_pools_have_balances_in_interact_via_deposit():
    # Testing the bothPoolsHaveBalance() check in the interact function
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    pool_id = 0
    gwin_protocol.initializePool(pool_id, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    assert gwin_protocol.retrieveCurrentPrice(pool_id, {"from": account}) == 1000_00000000 

    # Act - Withdraw all funds with zero price change
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(pool_id, True, False, 0, 0, True, {"from": account})
    tx = gwin_protocol.withdrawFromTranche(pool_id, False, True, 0, 0, True, {"from": account})
    tx.wait(1)

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_id, {"from": account}) == 0 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_id, account.address, {"from": account}) == 0 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_id, account.address, {"from": account}) == 0 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_id, account.address, {"from": account}) == 0 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_id, account.address, {"from": account}) == 0 # hEth for account
    assert gwin_protocol.retrieveCurrentPrice(pool_id, {"from": account}) == 1000_00000000 

    # Act
    #              DEPOSIT                     isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.depositToTranche(pool_id, True, True, Web3.toWei(1, "ether"), Web3.toWei(1, "ether"), {"from": account, "value": Web3.toWei(2, "ether")})
    tx.wait(1)

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_id, {"from": account}) == 1000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_id, {"from": account}) == 1000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_id, account.address, {"from": account}) == 1000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_id, account.address, {"from": account}) == 1000000000000000000 # hEth for account
    assert gwin_protocol.retrieveCurrentPrice(pool_id, {"from": account}) == 1000_00000000 

    # Clean Up
    empty_account(gwin_protocol, account)
    empty_account(gwin_protocol, non_owner)

    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 0 # total in protocol

def test_zero_price_change_partial_heated_withdrawal():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    pool_id = 0
    gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    assert gwin_protocol.retrieveCurrentPrice(pool_id, {"from": account}) == 1000_00000000 

    # Act - Withdraw portion of heated funds with zero price change
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount, isAll {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(pool_id, False, True, 0, Web3.toWei(0.5, "ether"), False, {"from": account})
    tx.wait(1)

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_id, {"from": account}) == 9500000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_id, account.address, {"from": account}) == 9500000000000000000 # hEth for account

    # Clean Up
    # Act - Withdraw all funds
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(pool_id, True, True, 0, 0, True, {"from": account})
    tx.wait(1)

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_id, {"from": account}) == 0 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_id, account.address, {"from": account}) == 0 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_id, account.address, {"from": account}) == 0 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_id, account.address, {"from": account}) == 0 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_id, account.address, {"from": account}) == 0 # hEth for account
    
    # Clean Up
    empty_account(gwin_protocol, account)
    empty_account(gwin_protocol, non_owner)
    empty_account(gwin_protocol, non_owner_two)
    empty_account(gwin_protocol, non_owner_three)
    empty_account(gwin_protocol, non_owner_four)

    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 0 # total in protocol

def test_withdraw_not_all_with_zero_amounts():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    pool_id = 0
    gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    assert gwin_protocol.retrieveCurrentPrice(pool_id, {"from": account}) == 1000_00000000 

    # Act - Expecting revert with non-sensible withdraw, not all, no amount
    # Assert - does revert
    with pytest.raises(ValueError):
        #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount, isAll {from, msg.value}
        tx = gwin_protocol.withdrawFromTranche(pool_id, False, True, 0, 0, False, {"from": account})
        tx.wait(1)

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    
    # Clean Up
    empty_account(gwin_protocol, account)
    empty_account(gwin_protocol, non_owner)
    empty_account(gwin_protocol, non_owner_two)
    empty_account(gwin_protocol, non_owner_three)
    empty_account(gwin_protocol, non_owner_four)

    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 0 # total in protocol

def test_neither_heated_nor_cooled_withdraw():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    pool_id = 0
    gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    assert gwin_protocol.retrieveCurrentPrice(pool_id, {"from": account}) == 1000_00000000 

    # Act - Expecting revert with non-sensible withdraw, not all, no amount
    # Assert - does revert
    with pytest.raises(ValueError):
        #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount, isAll {from, msg.value}
        tx = gwin_protocol.withdrawFromTranche(pool_id, False, False, Web3.toWei(1, "ether"), 0, False, {"from": account})
        tx.wait(1)

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    
    # Clean Up
    empty_account(gwin_protocol, account)
    empty_account(gwin_protocol, non_owner)
    empty_account(gwin_protocol, non_owner_two)
    empty_account(gwin_protocol, non_owner_three)
    empty_account(gwin_protocol, non_owner_four)

    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 0 # total in protocol

def test_deposit_with_partial_msg_value():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    pool_id = 0
    gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    assert gwin_protocol.retrieveCurrentPrice(pool_id, {"from": account}) == 1000_00000000 

    # Act - Expecting revert with non-sensible deposit, partial msg.value
    # Assert - does revert
    with pytest.raises(ValueError):
        #              DEPOSIT                     isCooled, isHeated, cAmount, hAmount {from, msg.value}
        tx = gwin_protocol.depositToTranche(pool_id, False, True, 0, Web3.toWei(1, "ether"), {"from": account, "value": Web3.toWei(0.1, "ether")})
        tx.wait(1)

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    
    # Clean Up
    empty_account(gwin_protocol, account)
    empty_account(gwin_protocol, non_owner)
    empty_account(gwin_protocol, non_owner_two)
    empty_account(gwin_protocol, non_owner_three)
    empty_account(gwin_protocol, non_owner_four)

    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 0 # total in protocol

def test_deposit_with_zero_msg_value():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    pool_id = 0
    gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    assert gwin_protocol.retrieveCurrentPrice(pool_id, {"from": account}) == 1000_00000000 

    # Act - Expecting revert with non-sensible deposit, zero msg.value
    # Assert - does revert
    with pytest.raises(ValueError):
        #              DEPOSIT                     isCooled, isHeated, cAmount, hAmount {from, msg.value}
        tx = gwin_protocol.depositToTranche(pool_id, False, True, 0, Web3.toWei(1, "ether"), {"from": account, "value": Web3.toWei(0, "ether")})
        tx.wait(1)

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    
    # Clean Up
    empty_account(gwin_protocol, account)
    empty_account(gwin_protocol, non_owner)
    empty_account(gwin_protocol, non_owner_two)
    empty_account(gwin_protocol, non_owner_three)
    empty_account(gwin_protocol, non_owner_four)

    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 0 # total in protocol

def test_deposit_to_uninitialized_pool():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    pool_id = 100

    # Act - Expecting revert with deposit to uninitialized pool
    # Assert - does revert
    with pytest.raises(ValueError):
        #              DEPOSIT                     isCooled, isHeated, cAmount, hAmount {from, msg.value}
        tx = gwin_protocol.depositToTranche(pool_id, False, True, 0, Web3.toWei(1, "ether"), {"from": account, "gasLimit": 200000000, "value": Web3.toWei(1, "ether")})
        tx.wait(1)

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_id, {"from": account}) == 0 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_id, account.address, {"from": account}) == 0 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_id, account.address, {"from": account}) == 0 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_id, account.address, {"from": account}) == 0 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_id, account.address, {"from": account}) == 0 # hEth for account

def test_deposit_with_neither_cooled_nor_heated():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    pool_id = 0
    gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    assert gwin_protocol.retrieveCurrentPrice(pool_id, {"from": account}) == 1000_00000000 

    # Act - Expecting revert with non-sensible deposit, i.e. neither cooled nor heated
    # Assert - does revert
    with pytest.raises(ValueError):
        #              DEPOSIT                     isCooled, isHeated, cAmount, hAmount {from, msg.value}
        tx = gwin_protocol.depositToTranche(pool_id, False, False, 0, Web3.toWei(1, "ether"), {"from": account, "value": Web3.toWei(1, "ether")})
        tx.wait(1)

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_id, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_id, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_id, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    
    # Clean Up
    empty_account(gwin_protocol, account)
    empty_account(gwin_protocol, non_owner)
    empty_account(gwin_protocol, non_owner_two)
    empty_account(gwin_protocol, non_owner_three)
    empty_account(gwin_protocol, non_owner_four)

    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 0 # total in protocol

def test_can_withdraw_all_after_all_heated():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act

    parent_id = 1
    pool_type = 0 # classic type pool
    pool_h_rate = 100_0000000000 # 2x leverage
    pool_c_rate = -100_0000000000 # stable

    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x4554482f555344", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(20, "ether")})
    tx.wait(1)
    pool_2x_id = 0

    # Assert
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(10_0000000000) # hEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(10_0000000000) # cEth in parent pool
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # hEth in protocol

    pool_type = 0 # classic type pool
    pool_h_rate = 400_0000000000 # 5x leverage
    pool_c_rate = -100_0000000000 # stable

    # Act
    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x4554482f555344", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(20, "ether")})
    tx.wait(1)
    pool_5x_id = 1

    # Assert
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_5x_id, {"from": account}))) == rnd(26_0000000000) # cEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_5x_id, {"from": account}))) == rnd(14_0000000000) # hEth in parent pool
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 4_000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 16_000000000000000000 # cEth in protocol
        
    
    pool_type = 0 # classic type pool
    pool_h_rate = 900_0000000000 # 10x leverage
    pool_c_rate = -100_0000000000 # stable

    # Act
    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x4554482f555344", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(20, "ether")})
    tx.wait(1)
    pool_10x_id = 2

    # Assert
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_10x_id, {"from": account}))) == rnd(44_0000000000) # cEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_10x_id, {"from": account}))) == rnd(16_0000000000) # hEth in parent pool
    
    eth_usd, last_eth = gwin_protocol.retrieveProtocolEthPrice(pool_10x_id)
    assert eth_usd == 1000_00000000
    assert last_eth == 1000_00000000

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_10x_id, {"from": account}) == 18_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_10x_id, {"from": account}) == 2_000000000000000000 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 16_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 4_000000000000000000 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # hEth in protocol



    eth_usd, last_eth = gwin_protocol.retrieveProtocolEthPrice(pool_10x_id)
    assert eth_usd == 1000_00000000
    assert last_eth == 1000_00000000

    valOne, valTwo = gwin_protocol.simulateInteract.call(pool_10x_id, 1000_00000000)
    assert valOne == 2_000000000000000000
    assert valTwo == 18_000000000000000000

    # check percent calculated user cbal in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, account.address, {"from": account}))) == rnd(44_0000000000) # cEth user has in parent pool
    # check user cbal in parent pool
    assert rnd(rounded(gwin_protocol.seeUserParentPoolBal.call(pool_2x_id, account.address, {"from": account}))) == rnd(44_0000000000) # cEth user has in parent pool

    ################### tx1 ###################         Withdraw ALL from Child HEATED Pools, no price change

    # Act
    #              WITHDRAWAL              ID, isCooled, isHeated, cAmount, hAmount, isAll, {from}
    tx = gwin_protocol.withdrawFromTranche(pool_2x_id, False, True, 0, 0, True, {"from": account})
    tx.wait(1)
    tx = gwin_protocol.withdrawFromTranche(pool_5x_id, False, True, 0, 0, True, {"from": account})
    tx.wait(1)
    tx = gwin_protocol.withdrawFromTranche(pool_10x_id, False, True, 0, 0, True, {"from": account})
    tx.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 44_000000000000000000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 44_0000000000 # total in protocol
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(0) # hEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(44_0000000000) # cEth in parent pool

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_10x_id, {"from": account}) == 18_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_10x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 16_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 0 # hEth in protocol

    # Owner 
    # 2x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 
    # 5x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 
    # 10x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account})) == rnd(roundedDec(0)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four

    # SHARED POOL BALANCES cEth
    # Owner
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, account.address, {"from": account}))) == rnd(44_0000000000) # cEth user has in parent pool
    assert rnd(roundedDec(gwin_protocol.getParentUserCEthPercent(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(100_0000000000)) # cEth user has in parent pool

    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth user has in parent pool

    ################### tx2 ###################         Withdraw ALL from Parent COOLED, no price change

    # Act
    #              WITHDRAWAL              ID, isCooled, isHeated, cAmount, hAmount, isAll, {from}
    tx = gwin_protocol.withdrawFromTranche(pool_2x_id, True, False, 0, 0, True, {"from": account})
    tx.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 0 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 0 # total in protocol
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(0) # hEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(0) # cEth in parent pool

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_10x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_10x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 0 # hEth in protocol

    # Owner 
    # 2x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 
    # 5x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 
    # 10x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account})) == rnd(roundedDec(0)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four

    # SHARED POOL BALANCES cEth
    # Owner
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, account.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(roundedDec(gwin_protocol.getParentUserCEthPercent(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth user has in parent pool

    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth user has in parent pool

    ################### tx3 ###################         Can Deposit, no price change

    # Act
    #              DEPOSIT                     isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.depositToTranche(pool_2x_id, False, True, 0, Web3.toWei(1, "ether"), {"from": account, "value": Web3.toWei(1, "ether")})
    tx.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 1_000000000000000000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 1_0000000000 # total in protocol
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(1_0000000000) # hEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(0) # cEth in parent pool

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_10x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_10x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 1_000000000000000000 # hEth in protocol

    # Owner 
    # 2x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(1_0000000000) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(100_0000000000)) # hEth % for account 
    # 5x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 
    # 10x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account})) == rnd(roundedDec(0)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four

    # SHARED POOL BALANCES cEth
    # Owner
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, account.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(roundedDec(gwin_protocol.getParentUserCEthPercent(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth user has in parent pool

    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth user has in parent pool

def test_both_pools_have_balances_is_false():
    # Heated is zero and Cooled is zero
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1000_00000000 

    # Act - Withdraw all funds with zero price change
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(0, True, False, 0, 0, True, {"from": account})
    tx.wait(1)
    tx = gwin_protocol.withdrawFromTranche(0, False, True, 0, 0, True, {"from": account})
    tx.wait(1)

    # Assert
    assert gwin_protocol.bothPoolsHaveBalance.call(0) == False

def test_both_pools_have_balances():
    # Heated is positive and Cooled is positive
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1000_00000000 

    # Assert
    assert gwin_protocol.bothPoolsHaveBalance.call(0) == True

    # Clean up
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(0, True, False, 0, 0, True, {"from": account})
    tx.wait(1)
    tx = gwin_protocol.withdrawFromTranche(0, False, True, 0, 0, True, {"from": account})
    tx.wait(1)

def test_both_pools_have_balances_heated_zeroed():
    # Heated is positive and Cooled is zero
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1000_00000000 

    # Assert
    # Act - Withdraw all funds from cooled to test heated branch
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(0, True, False, 0, 0, True, {"from": account})
    tx.wait(1)
    # Check cEth bal is zero returns both pools have balance = false
    assert gwin_protocol.bothPoolsHaveBalance.call(0) == False
    
    # Clean up
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(0, False, True, 0, 0, True, {"from": account})
    tx.wait(1)

def test_both_pools_have_balances_cooled_zeroed():
    # Heated is zero and Cooled is positive
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1000_00000000 

    # Assert
    # Act - Withdraw all funds from heated to test cooled branch
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(0, False, True, 0, 0, True, {"from": account})
    tx.wait(1)
    # Check hEth bal is zero returns both pools have balance = false
    assert gwin_protocol.bothPoolsHaveBalance.call(0) == False

    # Clean up
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(0, True, False, 0, 0, True, {"from": account})
    tx.wait(1)

def test_withdraw_all():
    # Heated is zero and Cooled is positive
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1000_00000000 

    # Assert
    # Act - Withdraw all funds 
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(0, True, True, 0, 0, True, {"from": account})
    tx.wait(1)

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}) == 0 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}) == 0 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 0 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}) == 0 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}) == 0 # hEth for account


def test_dual_deposit():
    # Heated is zero and Cooled is positive
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act
    parent_id = 0
    gwin_protocol.initializePool(0, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", -50_0000000000, 50_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    
    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1000_00000000 

    # Act
    #              DEPOSIT                     isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.depositToTranche(0, True, True, Web3.toWei(1, "ether"), Web3.toWei(1, "ether"), {"from": account, "value": Web3.toWei(2, "ether")})

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}) == 11000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}) == 11000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}) == 11000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}) == 11000000000000000000 # hEth for account
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1000_00000000 

    # Clean Up
    # Act - Withdraw all funds
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(0, True, True, 0, 0, True, {"from": account})
    tx.wait(1)

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}) == 0 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}) == 0 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 0 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}) == 0 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}) == 0 # hEth for account

def test_ceth_needed_for_zeroed_parent():
    # Set up parent pool, withdraw, and then do dual deposit
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act

    parent_id = 1
    pool_type = 0 # classic type pool
    pool_h_rate = 100_0000000000 # 2x leverage
    pool_c_rate = -100_0000000000 # stable

    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x4554482f555344", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(20, "ether")})
    tx.wait(1)
    pool_2x_id = 0

    # Assert
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(10_0000000000) # hEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(10_0000000000) # cEth in parent pool
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # hEth in protocol

    pool_type = 0 # classic type pool
    pool_h_rate = 400_0000000000 # 5x leverage
    pool_c_rate = -100_0000000000 # stable

    # Act
    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x4554482f555344", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(20, "ether")})
    tx.wait(1)
    pool_5x_id = 1

    # Assert
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_5x_id, {"from": account}))) == rnd(26_0000000000) # cEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_5x_id, {"from": account}))) == rnd(14_0000000000) # hEth in parent pool
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 4_000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 16_000000000000000000 # cEth in protocol
        
    
    pool_type = 0 # classic type pool
    pool_h_rate = 900_0000000000 # 10x leverage
    pool_c_rate = -100_0000000000 # stable

    # Act
    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x4554482f555344", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(20, "ether")})
    tx.wait(1)
    pool_10x_id = 2

    # Assert
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_10x_id, {"from": account}))) == rnd(44_0000000000) # cEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_10x_id, {"from": account}))) == rnd(16_0000000000) # hEth in parent pool
    
    eth_usd, last_eth = gwin_protocol.retrieveProtocolEthPrice(pool_10x_id)
    assert eth_usd == 1000_00000000
    assert last_eth == 1000_00000000

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_10x_id, {"from": account}) == 18_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_10x_id, {"from": account}) == 2_000000000000000000 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 16_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 4_000000000000000000 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # hEth in protocol



    eth_usd, last_eth = gwin_protocol.retrieveProtocolEthPrice(pool_10x_id)
    assert eth_usd == 1000_00000000
    assert last_eth == 1000_00000000

    valOne, valTwo = gwin_protocol.simulateInteract.call(pool_10x_id, 1000_00000000)
    assert valOne == 2_000000000000000000
    assert valTwo == 18_000000000000000000

    # check percent calculated user cbal in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, account.address, {"from": account}))) == rnd(44_0000000000) # cEth user has in parent pool
    # check user cbal in parent pool
    assert rnd(rounded(gwin_protocol.seeUserParentPoolBal.call(pool_2x_id, account.address, {"from": account}))) == rnd(44_0000000000) # cEth user has in parent pool

    ################### tx1 ###################         Withdraw ALL from Child HEATED Pools, no price change

    # Act
    #              WITHDRAWAL              ID, isCooled, isHeated, cAmount, hAmount, isAll, {from}
    tx = gwin_protocol.withdrawFromTranche(pool_2x_id, False, True, 0, 0, True, {"from": account})
    tx.wait(1)
    tx = gwin_protocol.withdrawFromTranche(pool_5x_id, False, True, 0, 0, True, {"from": account})
    tx.wait(1)
    tx = gwin_protocol.withdrawFromTranche(pool_10x_id, False, True, 0, 0, True, {"from": account})
    tx.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 44_000000000000000000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 44_0000000000 # total in protocol
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(0) # hEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(44_0000000000) # cEth in parent pool

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_10x_id, {"from": account}) == 18_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_10x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 16_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 0 # hEth in protocol

    # Owner 
    # 2x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 
    # 5x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 
    # 10x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account})) == rnd(roundedDec(0)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four

    # SHARED POOL BALANCES cEth
    # Owner
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, account.address, {"from": account}))) == rnd(44_0000000000) # cEth user has in parent pool
    assert rnd(roundedDec(gwin_protocol.getParentUserCEthPercent(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(100_0000000000)) # cEth user has in parent pool

    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth user has in parent pool

    ################### tx2 ###################         Withdraw ALL from Parent COOLED, no price change

    # Act
    #              WITHDRAWAL              ID, isCooled, isHeated, cAmount, hAmount, isAll, {from}
    tx = gwin_protocol.withdrawFromTranche(pool_2x_id, True, False, 0, 0, True, {"from": account})
    tx.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 0 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 0 # total in protocol
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(0) # hEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(0) # cEth in parent pool

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_10x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_10x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 0 # hEth in protocol

    # Owner 
    # 2x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 
    # 5x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 
    # 10x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account})) == rnd(roundedDec(0)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four

    # SHARED POOL BALANCES cEth
    # Owner
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, account.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(roundedDec(gwin_protocol.getParentUserCEthPercent(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth user has in parent pool

    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth user has in parent pool

    ################### tx3 ###################         Can Deposit, no price change

    # Act
    #              DEPOSIT                     isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.depositToTranche(pool_2x_id, True, True, Web3.toWei(1, "ether"), Web3.toWei(1, "ether"), {"from": account, "value": Web3.toWei(2, "ether")})
    tx.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 2_000000000000000000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 2_0000000000 # total in protocol
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(1_0000000000) # hEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(1_0000000000) # cEth in parent pool

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_10x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_10x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 1_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 1_000000000000000000 # hEth in protocol

    # Check that cEth needed == 1 ETH

    assert gwin_protocol.cEthNeededForPools.call(pool_2x_id, {"from": account}) == 1_000000000000000000

def test_dual_deposit_with_parent():
    # Set up parent pool, withdraw, and then do dual deposit
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act

    parent_id = 1
    pool_type = 0 # classic type pool
    pool_h_rate = 100_0000000000 # 2x leverage
    pool_c_rate = -100_0000000000 # stable

    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x4554482f555344", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(20, "ether")})
    tx.wait(1)
    pool_2x_id = 0

    # Assert
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(10_0000000000) # hEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(10_0000000000) # cEth in parent pool
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # hEth in protocol

    pool_type = 0 # classic type pool
    pool_h_rate = 400_0000000000 # 5x leverage
    pool_c_rate = -100_0000000000 # stable

    # Act
    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x4554482f555344", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(20, "ether")})
    tx.wait(1)
    pool_5x_id = 1

    # Assert
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_5x_id, {"from": account}))) == rnd(26_0000000000) # cEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_5x_id, {"from": account}))) == rnd(14_0000000000) # hEth in parent pool
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 4_000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 16_000000000000000000 # cEth in protocol
        
    
    pool_type = 0 # classic type pool
    pool_h_rate = 900_0000000000 # 10x leverage
    pool_c_rate = -100_0000000000 # stable

    # Act
    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x4554482f555344", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(20, "ether")})
    tx.wait(1)
    pool_10x_id = 2

    # Assert
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_10x_id, {"from": account}))) == rnd(44_0000000000) # cEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_10x_id, {"from": account}))) == rnd(16_0000000000) # hEth in parent pool
    
    eth_usd, last_eth = gwin_protocol.retrieveProtocolEthPrice(pool_10x_id)
    assert eth_usd == 1000_00000000
    assert last_eth == 1000_00000000

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_10x_id, {"from": account}) == 18_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_10x_id, {"from": account}) == 2_000000000000000000 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 16_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 4_000000000000000000 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # hEth in protocol



    eth_usd, last_eth = gwin_protocol.retrieveProtocolEthPrice(pool_10x_id)
    assert eth_usd == 1000_00000000
    assert last_eth == 1000_00000000

    valOne, valTwo = gwin_protocol.simulateInteract.call(pool_10x_id, 1000_00000000)
    assert valOne == 2_000000000000000000
    assert valTwo == 18_000000000000000000

    # check percent calculated user cbal in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, account.address, {"from": account}))) == rnd(44_0000000000) # cEth user has in parent pool
    # check user cbal in parent pool
    assert rnd(rounded(gwin_protocol.seeUserParentPoolBal.call(pool_2x_id, account.address, {"from": account}))) == rnd(44_0000000000) # cEth user has in parent pool

    ################### tx1 ###################         Withdraw ALL from Child HEATED Pools, no price change

    # Act
    #              WITHDRAWAL              ID, isCooled, isHeated, cAmount, hAmount, isAll, {from}
    tx = gwin_protocol.withdrawFromTranche(pool_2x_id, False, True, 0, 0, True, {"from": account})
    tx.wait(1)
    tx = gwin_protocol.withdrawFromTranche(pool_5x_id, False, True, 0, 0, True, {"from": account})
    tx.wait(1)
    tx = gwin_protocol.withdrawFromTranche(pool_10x_id, False, True, 0, 0, True, {"from": account})
    tx.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 44_000000000000000000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 44_0000000000 # total in protocol
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(0) # hEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(44_0000000000) # cEth in parent pool

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_10x_id, {"from": account}) == 18_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_10x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 16_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 0 # hEth in protocol

    # Owner 
    # 2x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 
    # 5x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 
    # 10x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account})) == rnd(roundedDec(0)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four

    # SHARED POOL BALANCES cEth
    # Owner
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, account.address, {"from": account}))) == rnd(44_0000000000) # cEth user has in parent pool
    assert rnd(roundedDec(gwin_protocol.getParentUserCEthPercent(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(100_0000000000)) # cEth user has in parent pool

    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth user has in parent pool

    ################### tx2 ###################         Withdraw ALL from Parent COOLED, no price change

    # Act
    #              WITHDRAWAL              ID, isCooled, isHeated, cAmount, hAmount, isAll, {from}
    tx = gwin_protocol.withdrawFromTranche(pool_2x_id, True, False, 0, 0, True, {"from": account})
    tx.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 0 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 0 # total in protocol
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(0) # hEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(0) # cEth in parent pool

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_10x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_10x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 0 # hEth in protocol

    # Owner 
    # 2x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 
    # 5x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 
    # 10x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account})) == rnd(roundedDec(0)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four

    # SHARED POOL BALANCES cEth
    # Owner
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, account.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(roundedDec(gwin_protocol.getParentUserCEthPercent(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth user has in parent pool

    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth user has in parent pool

    ################### tx3 ###################         Can Dual Deposit, no price change

     # Act
    #              DEPOSIT                     isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.depositToTranche(pool_2x_id, True, True, Web3.toWei(1, "ether"), Web3.toWei(1, "ether"), {"from": account, "value": Web3.toWei(2, "ether")})
    tx.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 2_000000000000000000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 2_0000000000 # total in protocol
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(1_0000000000) # hEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(1_0000000000) # cEth in parent pool

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_10x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_10x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 1_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 1_000000000000000000 # hEth in protocol

    # Owner 
    # 2x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(1_0000000000) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(100_0000000000)) # hEth % for account 
    # 5x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 
    # 10x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account})) == rnd(roundedDec(0)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four

    # SHARED POOL BALANCES cEth
    # Owner
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, account.address, {"from": account}))) == rnd(1_0000000000) # cEth user has in parent pool
    assert rnd(roundedDec(gwin_protocol.getParentUserCEthPercent(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(100_0000000000)) # cEth user has in parent pool

    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth user has in parent pool

    # Clean Up
    # Act - Withdraw all funds
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(pool_2x_id, True, True, 0, 0, True, {"from": account})
    tx.wait(1)

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 0 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, account.address, {"from": account}) == 0 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, account.address, {"from": account}) == 0 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_2x_id, account.address, {"from": account}) == 0 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_2x_id, account.address, {"from": account}) == 0 # hEth for account

    # Clean Up
    # Act - Withdraw all funds
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(pool_2x_id, True, True, 0, 0, True, {"from": account})
    tx.wait(1)

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 0 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, account.address, {"from": account}) == 0 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, account.address, {"from": account}) == 0 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_2x_id, account.address, {"from": account}) == 0 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_2x_id, account.address, {"from": account}) == 0 # hEth for account

def test_cooled_deposit_to_parent():
    # Set up parent pool, withdraw, and then do cooled deposit
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account() # Protocol 
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()
    # Act

    parent_id = 1
    pool_type = 0 # classic type pool
    pool_h_rate = 100_0000000000 # 2x leverage
    pool_c_rate = -100_0000000000 # stable

    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x4554482f555344", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(20, "ether")})
    tx.wait(1)
    pool_2x_id = 0

    # Assert
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(10_0000000000) # hEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(10_0000000000) # cEth in parent pool
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # hEth in protocol

    pool_type = 0 # classic type pool
    pool_h_rate = 400_0000000000 # 5x leverage
    pool_c_rate = -100_0000000000 # stable

    # Act
    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x4554482f555344", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(20, "ether")})
    tx.wait(1)
    pool_5x_id = 1

    # Assert
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_5x_id, {"from": account}))) == rnd(26_0000000000) # cEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_5x_id, {"from": account}))) == rnd(14_0000000000) # hEth in parent pool
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 4_000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 16_000000000000000000 # cEth in protocol
        
    
    pool_type = 0 # classic type pool
    pool_h_rate = 900_0000000000 # 10x leverage
    pool_c_rate = -100_0000000000 # stable

    # Act
    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x4554482f555344", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(20, "ether")})
    tx.wait(1)
    pool_10x_id = 2

    # Assert
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_10x_id, {"from": account}))) == rnd(44_0000000000) # cEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_10x_id, {"from": account}))) == rnd(16_0000000000) # hEth in parent pool
    
    eth_usd, last_eth = gwin_protocol.retrieveProtocolEthPrice(pool_10x_id)
    assert eth_usd == 1000_00000000
    assert last_eth == 1000_00000000

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_10x_id, {"from": account}) == 18_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_10x_id, {"from": account}) == 2_000000000000000000 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 16_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 4_000000000000000000 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # hEth in protocol



    eth_usd, last_eth = gwin_protocol.retrieveProtocolEthPrice(pool_10x_id)
    assert eth_usd == 1000_00000000
    assert last_eth == 1000_00000000

    valOne, valTwo = gwin_protocol.simulateInteract.call(pool_10x_id, 1000_00000000)
    assert valOne == 2_000000000000000000
    assert valTwo == 18_000000000000000000

    # check percent calculated user cbal in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, account.address, {"from": account}))) == rnd(44_0000000000) # cEth user has in parent pool
    # check user cbal in parent pool
    assert rnd(rounded(gwin_protocol.seeUserParentPoolBal.call(pool_2x_id, account.address, {"from": account}))) == rnd(44_0000000000) # cEth user has in parent pool

    ################### tx1 ###################         Withdraw ALL from Child HEATED Pools, no price change

    # Act
    #              WITHDRAWAL              ID, isCooled, isHeated, cAmount, hAmount, isAll, {from}
    tx = gwin_protocol.withdrawFromTranche(pool_2x_id, False, True, 0, 0, True, {"from": account})
    tx.wait(1)
    tx = gwin_protocol.withdrawFromTranche(pool_5x_id, False, True, 0, 0, True, {"from": account})
    tx.wait(1)
    tx = gwin_protocol.withdrawFromTranche(pool_10x_id, False, True, 0, 0, True, {"from": account})
    tx.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 44_000000000000000000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 44_0000000000 # total in protocol
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(0) # hEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(44_0000000000) # cEth in parent pool

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_10x_id, {"from": account}) == 18_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_10x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 16_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 0 # hEth in protocol

    # Owner 
    # 2x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 
    # 5x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 
    # 10x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account})) == rnd(roundedDec(0)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four

    # SHARED POOL BALANCES cEth
    # Owner
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, account.address, {"from": account}))) == rnd(44_0000000000) # cEth user has in parent pool
    assert rnd(roundedDec(gwin_protocol.getParentUserCEthPercent(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(100_0000000000)) # cEth user has in parent pool

    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth user has in parent pool

    ################### tx2 ###################         Can Deposit to cooled, no price change

     # Act
    #              DEPOSIT                     isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.depositToTranche(pool_2x_id, True, False, Web3.toWei(1, "ether"), 0, {"from": account, "value": Web3.toWei(1, "ether")})
    tx.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 45_000000000000000000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 45_0000000000 # total in protocol
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(0) # hEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(45_0000000000) # cEth in parent pool

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_10x_id, {"from": account}) == 18_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_10x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}) == 16_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}) == 0 # hEth in protocol

    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 11_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 0 # hEth in protocol

    # Owner 
    # 2x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 
    # 5x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 
    # 10x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account})) == rnd(roundedDec(0)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four

    # SHARED POOL BALANCES cEth
    # Owner
    assert rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, account.address, {"from": account})) == 45_0000000000 # cEth user has in parent pool
    assert rnd(roundedDec(gwin_protocol.getParentUserCEthPercent(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(100_0000000000)) # cEth user has in parent pool
    assert rounded(gwin_protocol.getParentUserCEthBalance(pool_5x_id, account.address, {"from": account})) == 45_0000000000 # cEth user has in parent pool
    assert rnd(roundedDec(gwin_protocol.getParentUserCEthPercent(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(100_0000000000)) # cEth user has in parent pool
    assert rounded(gwin_protocol.getParentUserCEthBalance(pool_10x_id, account.address, {"from": account})) == 45_0000000000 # cEth user has in parent pool
    assert rnd(roundedDec(gwin_protocol.getParentUserCEthPercent(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(100_0000000000)) # cEth user has in parent pool

    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth user has in parent pool

    # Clean Up
    # Act - Withdraw all funds
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.withdrawFromTranche(pool_2x_id, True, True, 0, 0, True, {"from": account})
    tx.wait(1)

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 0 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 0 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, account.address, {"from": account}) == 0 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, account.address, {"from": account}) == 0 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(pool_2x_id, account.address, {"from": account}) == 0 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(pool_2x_id, account.address, {"from": account}) == 0 # hEth for account