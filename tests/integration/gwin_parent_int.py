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

    # Assert
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(10_0000000000) # hEth in parent pool
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(10_0000000000) # cEth in parent pool
    assert gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}) == 10_000000000000000000 # hEth in protocol

    pool_type = 0 # classic type pool
    pool_h_rate = 400_0000000000 # 5x leverage
    pool_c_rate = -100_0000000000 # stable

    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(20, "ether")})
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

    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(20, "ether")})
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


    ################### tx1 ###################         Child Pool Rebalancing Test - 1% Gain
    # Act
    eth_usd_price_feed.updateAnswer(1010_00000000, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(pool_2x_id, {"from": account}) == 1010_00000000

    # Act
    #              DEPOSIT              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.depositToTranche(pool_2x_id, False, True, 0, Web3.toWei(1, "ether"), {"from": non_owner, "value": Web3.toWei(1, "ether")})
    tx.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 61_000000000000000000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 61_0000000000 # total in protocol
    # 17_158420000
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(17_4356435643) # hEth in parent pool
    # 43_841590000
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(43_5643564356) # cEth in parent pool

    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(10_2145249037) # cEth in protocol
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(11_0990099010) # hEth in protocol

    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}))) == rnd(15_3081193917) # cEth in protocol
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}))) == rnd(4_1584158416) # hEth in protocol

    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(pool_10x_id, {"from": account}))) == rnd(18_0417121403) # cEth in protocol
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(pool_10x_id, {"from": account}))) == rnd(2_1782178217) # hEth in protocol

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(10_0990099009) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(90_9901873327)) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(1_0000000000) # hEth for non_owner
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(roundedDec(9_0098126672)) # hEth % for non_owner

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
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, account.address, {"from": account}))) == rnd(43_5643564356) # cEth user has in parent pool
    assert rnd(roundedDec(gwin_protocol.getParentUserCEthPercent(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(100_0000000000)) # cEth user has in parent pool

    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth user has in parent pool



    ################### tx2 ###################         Child Pool Rebalancing Test - 5% Loss
    # Act
    eth_usd_price_feed.updateAnswer(960_00000000, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(pool_2x_id, {"from": account}) == 960_00000000

    # Act
    #              DEPOSIT                        isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.depositToTranche(pool_2x_id, True, False, Web3.toWei(1, "ether"), 0, {"from": non_owner, "value": Web3.toWei(1, "ether")})
    tx.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 62_000000000000000000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 62_0000000000 # total in protocol

    #                                                                                                     -15_471270000
    assert rnd(rounded(gwin_protocol.getParentPoolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(15_1191640013) # hEth in parent pool
    #                                                                                                     -46_528740000
    assert rnd(rounded(gwin_protocol.getParentPoolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(46_8808359986) # cEth in parent pool
    #                                                                                                     -13_339350000
    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(pool_2x_id, {"from": account}))) == rnd(14_5044549090) # cEth in protocol
    #                                                                                                     -10_559460000
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(pool_2x_id, {"from": account}))) == rnd(10_5430140722) # hEth in protocol
    #                                                                                                     -16_772300000
    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(pool_5x_id, {"from": account}))) == rnd(17_3469207937) # cEth in protocol
    #                                                                                                     -3_498110000
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(pool_5x_id, {"from": account}))) == rnd(3_3463699892) # hEth in protocol
    #                                                                                                     -16_425710000
    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(pool_10x_id, {"from": account}))) == rnd(15_0294602959) # cEth in protocol
    #                                                                                                     -1_405100000
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(pool_10x_id, {"from": account}))) == rnd(1_2297799398) # hEth in protocol

    # Owner 
    # 2x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(9_5931082548) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(90_9901873327)) # hEth % for account 
    # 5x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(3_3463699892) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(100_0000000000)) # hEth % for account 
    # 10x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(0) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(0)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(1_2297799398) # hEth for account
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(100_0000000000)) # hEth % for account 

    # Alice
    # 2x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(9499058173) # hEth for non_owner
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner.address, {"from": account}))) == rnd(roundedDec(9_0098126672)) # hEth % for non_owner

    # Bob
    # 2x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    # 2x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    # 2x Pool
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account})) == rnd(roundedDec(0)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four

    # SHARED POOL BALANCES cEth
    # Owner
    # 2x Pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, account.address, {"from": account}))) == rnd(45_8808359986) # cEth user has in parent pool
    assert rnd(roundedDec(gwin_protocol.getParentUserCEthPercent(pool_2x_id, account.address, {"from": account}))) == rnd(roundedDec(97_8669322363)) # cEth user has in parent pool
    # 5x Pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_5x_id, account.address, {"from": account}))) == rnd(45_8808359986) # cEth user has in parent pool
    assert rnd(roundedDec(gwin_protocol.getParentUserCEthPercent(pool_5x_id, account.address, {"from": account}))) == rnd(roundedDec(97_8669322363)) # cEth user has in parent pool
    # 10x Pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_10x_id, account.address, {"from": account}))) == rnd(45_8808359986) # cEth user has in parent pool
    assert rnd(roundedDec(gwin_protocol.getParentUserCEthPercent(pool_10x_id, account.address, {"from": account}))) == rnd(roundedDec(97_8669322363)) # cEth user has in parent pool

    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner.address, {"from": account}))) == rnd(1_0000000000) # cEth user has in parent pool
    assert rnd(roundedDec(gwin_protocol.getParentUserCEthPercent(pool_2x_id, non_owner.address, {"from": account}))) == rnd(roundedDec(2_1330677636)) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth user has in parent pool
    assert rnd(rounded(gwin_protocol.getParentUserCEthBalance(pool_2x_id, non_owner_four.address, {"from": account}))) == rnd(0) # cEth user has in parent pool