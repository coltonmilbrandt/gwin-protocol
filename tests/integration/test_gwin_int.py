from brownie import GwinProtocol, GwinToken, network, exceptions
from pyparsing import null_debug_action
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, INITIAL_VALUE, DECIMALS, get_account, get_contract, rounded, roundedDec, extra_rounded, rnd, empty_account
from scripts.deploy import deploy_gwin_protocol_and_gwin_token
from web3 import Web3
import pytest

# NOTE: If you start a new instance of Ganache etc., be sure to delete the previous deployments in the build folder

def test_use_protocol():
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
    
    eth_usd, last_eth = gwin_protocol.retrieveProtocolEthPrice(0)
    assert eth_usd == 1000_00000000
    assert last_eth == 1000_00000000

    # Assert
    assert gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}) == 10_000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}) == 10_000000000000000000 # hEth in protocol

    assert gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}) == 10_000000000000000000 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}) == 100_0000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}) == 10_000000000000000000 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 100_0000000000 # hEth % for account 

    eth_usd, last_eth = gwin_protocol.retrieveProtocolEthPrice(0)
    assert eth_usd == 1000_00000000
    assert last_eth == 1000_00000000

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 1000_00000000)
    assert valOne == 10_000000000000000000
    assert valTwo == 10_000000000000000000



    # Act
    eth_usd_price_feed.updateAnswer(1200_00000000, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1200_00000000
    
    # Act -- test if preview shows correct balance before transaction
    hEthEst, cEthEst = gwin_protocol.previewPoolBalances.call(0, {"from": account})
    # Assert
    assert rounded(cEthEst) == 9_1666666666 # this is before deposit
    assert rounded(hEthEst) == 10_8333333333

    # Act -- test if preview shows correct balance before transaction with price inputed
    hEthEst, cEthEst = gwin_protocol.previewPoolBalancesAtPrice.call(0, 1200_00000000, {"from": account})
    # Assert
    assert rounded(cEthEst) == 9_1666666666 # this is before deposit
    assert rounded(hEthEst) == 10_8333333333

    # Act -- test if preview shows correct hEth balance before transaction
    userHEthEst = gwin_protocol.previewUserHEthBalance.call(0, account.address, {"from": account})
    # Assert
    assert rounded(userHEthEst) == 10_8333333333 # this is before deposit

    # Act -- test if preview shows correct hEth balance before transaction with price inputed
    userHEthEst = gwin_protocol.previewUserHEthBalanceAtPrice.call(0, 1200_00000000, account.address, {"from": account})
    # Assert
    assert rounded(userHEthEst) == 10_8333333333 # this is before deposit

    # Act -- test if preview shows correct hEth balance before transaction
    userCEthEst = gwin_protocol.previewUserCEthBalance.call(0, account.address, {"from": account})
    # Assert
    assert rounded(userCEthEst) == 9_1666666666 # this is before deposit

    # Act -- test if preview shows correct cEth balance before transaction with price inputed
    userCEthEst = gwin_protocol.previewUserCEthBalanceAtPrice.call(0, 1200_00000000, account.address, {"from": account})
    # Assert
    assert rounded(userCEthEst) == 9_1666666666 # this is before deposit
    
    

    # Act
    ################### tx1 ###################
    #                                     isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txOne = gwin_protocol.depositToTranche(0, True, False, Web3.toWei(1, "ether"), 0, {"from": non_owner, "value": Web3.toWei(1, "ether")})
    txOne.wait(1)
    # Assert
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account})) == 10_1666666666 # cEth in protocol
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account})) == 10_8333333333 # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 1200_00000000)
    assert rounded(valTwo) == 10_1666666666
    assert rounded(valOne) == 10_8333333333

    assert gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}) == 9_166666666666666666 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}) == 90_1639344262 # cEth % for account
    assert gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}) == 10_833333333333333333 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 100_0000000000 # hEth % for account 

    assert gwin_protocol.retrieveCEthBalance.call(0, non_owner.address, {"from": account}) == 1_000000000000000000 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner.address, {"from": account}) == 9_8360655737 # cEth % non_owner
    assert gwin_protocol.retrieveHEthBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth % for non_owner


    ################### tx2 ###################
    # Act
    eth_usd_price_feed.updateAnswer(1400_00000000, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1400_00000000
    # Act
    #              DEPOSIT              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txTwo = gwin_protocol.depositToTranche(0, False, True, 0, Web3.toWei(1, "ether"), {"from": non_owner_two, "value": Web3.toWei(1, "ether")})
    txTwo.wait(1)
    # Assert
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account})) == 9_4174225245 # cEth in protocol
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account})) == 12_5825774754 # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 1400_00000000)
    assert rounded(valTwo) == 9_4174225245
    assert rounded(valOne) == 12_5825774754

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account})) == 8_4911186696 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}) == 90_1639344262 # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account})) == 11_5825774754 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 92_0525027407 # hEth % for account 

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner.address, {"from": account})) == 9263038548 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner.address, {"from": account}) == 9_8360655737 # cEth % non_owner
    assert gwin_protocol.retrieveHEthBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_two.address, {"from": account})) == 0 # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_two.address, {"from": account}))) == rnd(1_0000000000) # hEth for non_owner_two
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 7_9474972592 # hEth % for non_owner_two 



    # Act
    eth_usd_price_feed.updateAnswer(1300_00000000, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1300_00000000
    # Act
    ################### tx3 ###################
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txThree = gwin_protocol.withdrawFromTranche(0, True, False, 0, 0, True, {"from": non_owner})
    txThree.wait(1)
    # Assert
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account})) == 8_8804772808 # cEth in protocol
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account})) == 12_1507433794 # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 1300_00000000)
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

    # NOTE: test_deploy_mock_protocol_in_use does a unit test up until this point

    # Act
    eth_usd_price_feed.updateAnswer(1150_00000000, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1150_00000000
    # Act
    ################### tx4 ###################
    #              DEPOSIT              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txFour = gwin_protocol.depositToTranche(0, False, True, 0, Web3.toWei(2, "ether"), {"from": non_owner_three, "value": Web3.toWei(2, "ether")})
    txFour.wait(1)
    # Assert
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account})) == 9_5828598866 # cEth in protocol
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account})) == 13_4483607736 # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 1150_00000000) # Test view function can estimate balances as well
    assert rounded(valTwo) == 9_5828598866
    assert rounded(valOne) == 13_4483607736

    # Owner 
    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account})) == 9_5828598866 # cEth for account 
    assert roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account})) == 100_0000000000 # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account})) == 10_5385026149 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account}) == 78_3627297951 # hEth % for account 

    # Alice
    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner.address, {"from": account})) == 0 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert gwin_protocol.retrieveHEthBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    # Bob
    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_two.address, {"from": account})) == 0 # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_two.address, {"from": account}))) == rnd(9098581587) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_two.address, {"from": account})) == 6_7655692320 # hEth % for non_owner_two     

    # Chris
    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_three.address, {"from": account})) == 0 # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_three.address, {"from": account}))) == rnd(2_0000000000) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_three.address, {"from": account})) == 14_8717009730 # hEth % for non_owner_three


    
    # Act
    eth_usd_price_feed.updateAnswer(1100_00000000, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1100_00000000

    # Act -- test if preview shows correct balance before transaction
    hEthEst, cEthEst = gwin_protocol.previewPoolBalances.call(0, {"from": account})
    # Assert
    assert rnd(rounded(cEthEst)) == rnd(9_8519507547) # this is before deposit
    assert rnd(rounded(hEthEst)) == rnd(13_1792699054)

    # Act -- test if preview shows correct balance before transaction with price inputed
    hEthEst, cEthEst = gwin_protocol.previewPoolBalancesAtPrice.call(0, 1100_00000000, {"from": account})
    # Assert
    assert rnd(rounded(cEthEst)) == rnd(9_8519507547) # this is before deposit
    assert rnd(rounded(hEthEst)) == rnd(13_1792699054)

    # Act -- test if preview shows correct hEth balance before transaction
    userHEthEst = gwin_protocol.previewUserHEthBalance.call(0, account.address, {"from": account})
    # Assert
    assert rnd(rounded(userHEthEst)) == rnd(10_3276356650) # this is before deposit

    # Act -- test if preview shows correct hEth balance before transaction with price inputed
    userHEthEst = gwin_protocol.previewUserHEthBalanceAtPrice.call(0, 1100_00000000, account.address, {"from": account})
    # Assert
    assert rnd(rounded(userHEthEst)) == rnd(10_3276356650) # this is before deposit

    # Act -- test if preview shows correct hEth balance before transaction
    userCEthEst = gwin_protocol.previewUserCEthBalance.call(0, account.address, {"from": account})
    # Assert
    assert rnd(rounded(userCEthEst)) == rnd(9_8519507547) # this is before deposit

    # Act -- test if preview shows correct cEth balance before transaction with price inputed
    userCEthEst = gwin_protocol.previewUserCEthBalanceAtPrice.call(0, 1100_00000000, account.address, {"from": account})
    # Assert
    assert rnd(rounded(userCEthEst)) == rnd(9_8519507547) # this is before deposit

    # Act -- test if preview shows correct hEth balance before transaction
    userHEthEst = gwin_protocol.previewUserHEthBalance.call(0, non_owner_two.address, {"from": account})
    # Assert
    assert rnd(rounded(userHEthEst)) == rnd(8916526297) # this is before deposit

    # Act -- test if preview shows correct cEth balance before transaction with price inputed
    userHEthEst = gwin_protocol.previewUserHEthBalanceAtPrice.call(0, 1100_00000000, non_owner_two.address, {"from": account})
    # Assert
    assert rnd(rounded(userHEthEst)) == rnd(8916526297) # this is before deposit

    # Act -- test if preview shows correct hEth balance before transaction
    userHEthEst = gwin_protocol.previewUserHEthBalance.call(0, non_owner_three.address, {"from": account})
    # Assert
    assert rnd(rounded(userHEthEst)) == rnd(1_9599816107) # this is before deposit

    # Act -- test if preview shows correct cEth balance before transaction with price inputed
    userHEthEst = gwin_protocol.previewUserHEthBalanceAtPrice.call(0, 1100_00000000, non_owner_three.address, {"from": account})
    # Assert
    assert rnd(rounded(userHEthEst)) == rnd(1_9599816107) # this is before deposit



    # Act
    ################### tx5 ###################
    #              DEPOSIT              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txFive = gwin_protocol.depositToTranche(0, True, True, Web3.toWei(3, "ether"), Web3.toWei(1, "ether"), {"from": non_owner, "value": Web3.toWei(4, "ether")})
    txFive.wait(1)
    # Assert
    # Make sure all ETH has been accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 27_031220660268900000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 27_0312206602 # total in protocol

    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account})) == 12_8519507547 # cEth in protocol 
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}))) == rnd(14_1792699054) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 1100_00000000) # Test view function can estimate balances as well
    assert rounded(valTwo) == 12_8519507547
    assert rnd(rounded(valOne)) == rnd(14_1792699054)

    # Owner 
    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account})) == 9_8519507547 # cEth for account 
    assert roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account})) == roundedDec(76_6572401556) # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account})) == 10_3276356650 # hEth for account
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account})) == 72_8361596460 # hEth % for account 

    # Alice
    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner.address, {"from": account})) == 3_0000000000 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner.address, {"from": account}) == 23_3427598443 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner.address, {"from": account}))) == rnd(1_0000000000) # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner.address, {"from": account}) == 7_0525492967 # hEth % for non_owner

    # Bob
    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_two.address, {"from": account})) == 0 # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_two.address, {"from": account})) == 8916526297 # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_two.address, {"from": account})) == roundedDec(6_2884241267) # hEth % for non_owner_two     

    # Chris
    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_three.address, {"from": account})) == 0 # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_three.address, {"from": account})) == 1_9599816107 # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_three.address, {"from": account})) == roundedDec(13_8228669304) # hEth % for non_owner_three



    # Act
    eth_usd_price_feed.updateAnswer(1000_00000000, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1000_00000000
    # Act
    ################### tx6 ###################
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txSix = gwin_protocol.withdrawFromTranche(0, False, True, 0, 0, True, {"from": non_owner_two})
    txSix.wait(1)
    # Assert
    # Make sure all ETH has been accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 26_182166438542800000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 26_1821664385 # total in protocol

    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account})) == 13_5293606613 # cEth in protocol 
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account})) == 12_6528057772 # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 1000_00000000) # Test view function can estimate balances as well
    assert rounded(valTwo) == 13_5293606613
    assert rounded(valOne) == 12_6528057772

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}))) == rnd(10_3712344937) # cEth for account 
    assert roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account})) == roundedDec(76_6572401556) # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account})) == 9_8342363039 # hEth for account
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account})) == roundedDec(77_7237592766) # hEth % for account 

    # Alice
    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner.address, {"from": account})) == 3_1581261676 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner.address, {"from": account}) == 23_3427598443 # cEth % non_owner
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner.address, {"from": account})) == 9522253323 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner.address, {"from": account}) == 7_5258037558 # hEth % for non_owner

    # Bob
    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_two.address, {"from": account})) == 0 # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_two.address, {"from": account})) == 0 # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    assert rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_three.address, {"from": account})) == 0 # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_three.address, {"from": account})) == 1_8663441407 # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_three.address, {"from": account})) == roundedDec(14_7504369675) # hEth % for non_owner_three



    # Act
    eth_usd_price_feed.updateAnswer(1300_00000000, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1300_00000000
    # Act
    ################### tx7 ###################
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txSeven = gwin_protocol.withdrawFromTranche(0, True, True, 0, 0, True, {"from": non_owner})
    txSeven.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 22_310999368436800000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 22_3109993684 # total in protocol

    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account})) == 9_2120216726 # cEth in protocol 
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}))) == rnd(13_0989776957) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 1300_00000000) # Test view function can estimate balances as well
    assert rounded(valTwo) == 9_2120216726
    assert rnd(rounded(valOne)) == rnd(13_0989776957)

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}))) == rnd(9_2120216726) # cEth for account 
    assert roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account})) == roundedDec(100_0000000000) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}))) == rnd(11_0095770555) # hEth for account
    assert rnd(gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account})) == rnd(84_0491320102) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_three.address, {"from": account}))) == rnd(2_0894006402) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_three.address, {"from": account})) == roundedDec(15_9508679897) # hEth % for non_owner_three



    # Act
    eth_usd_price_feed.updateAnswer(1400_00000000, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1400_00000000
    # Act
    ################### tx8 ###################         Dual Deposit Test
    #              DEPOSIT              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txEight = gwin_protocol.depositToTranche(0, True, True, Web3.toWei(3, "ether"), Web3.toWei(1, "ether"), {"from": non_owner_four, "value": Web3.toWei(4, "ether")})
    txEight.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 26.310999368436800000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 26_3109993684 # total in protocol

    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account})) == 11_8257033612 # cEth in protocol 
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}))) == rnd(14_4852960071) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 1400_00000000) # Test view function can estimate balances as well
    assert rounded(valTwo) == 11_8257033612
    assert rnd(rounded(valOne)) == rnd(14_4852960071)

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}))) == rnd(8_8257033612) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}))) == rnd(roundedDec(74_6315300802)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}))) == rnd(11_3342742430) # hEth for account
    assert rnd(gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account})) == rnd(78_2467561410) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_three.address, {"from": account}))) == rnd(2_1510217641) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_three.address, {"from": account})) == roundedDec(14_8496914600) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_four.address, {"from": account}))) == rnd(3_0000000000) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_four.address, {"from": account})) == rnd(roundedDec(25_3684699197)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_four.address, {"from": account}))) == rnd(1_0000000000) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_four.address, {"from": account}))) == rnd(roundedDec(6_9035523989)) # hEth % for non_owner_four




    # Act
    eth_usd_price_feed.updateAnswer(1300_00000000, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1300_00000000
    # Act
    ################### tx9 ###################         Dual Partial Withdrawal Test
    #              DEPOSIT              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txNine = gwin_protocol.withdrawFromTranche(0, True, True, Web3.toWei(0.5, "ether"), Web3.toWei(0.5, "ether"), False, {"from": non_owner_four})
    txNine.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) > 25_310999368436800000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 25_3109993684 # total in protocol

    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}))) == rnd(11_8368541066) # cEth in protocol 
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}))) == rnd(13_4741452618) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 1300_00000000) # Test view function can estimate balances as well
    assert rnd(rounded(valTwo)) == rnd(11_8368541066)
    assert rnd(rounded(valOne)) == rnd(13_4741452618)

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}))) == rnd(9_2071829835) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}))) == rnd(roundedDec(77_7840370473)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}))) == rnd(10_9343153658) # hEth for account
    assert rnd(gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account})) == rnd(81_1503450003) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_three.address, {"from": account}))) == rnd(2_0751174555) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_three.address, {"from": account})) == roundedDec(15_4007353730) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_four.address, {"from": account}))) == rnd(2_6296711230) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_four.address, {"from": account})) == rnd(roundedDec(22_2159629526)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_four.address, {"from": account}))) == rnd(4647124404) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_four.address, {"from": account}))) == rnd(roundedDec(34489196266)) # hEth % for non_owner_four



    # Act
    eth_usd_price_feed.updateAnswer(1500_00000000, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1500_00000000
    # Act
    ################### tx10 ###################         Heated Partial Withdrawal Test
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txTen = gwin_protocol.withdrawFromTranche(0, False, True, 0, Web3.toWei(0.7, "ether"), False, {"from": non_owner_three})
    txTen.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 24_610999368436800000 # total ETH in protocol is slightly larger than recorded
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 24_6109993684 # total ETH in protocol

    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}))) == rnd(10_9966845062) # cEth in protocol 
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}))) == rnd(13_6143148621) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 1500_00000000) # Test view function can estimate balances as well
    assert rnd(rounded(valTwo)) == rnd(10_9966845062)
    assert rnd(rounded(valOne)) == rnd(13_6143148621)

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}))) == rnd(8_5536651503) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}))) == rnd(roundedDec(77_7840370473)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}))) == rnd(11_6161158950) # hEth for account
    assert rnd(gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account})) == rnd(85_3228092098) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_three.address, {"from": account}))) == rnd(1_5045097523) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_three.address, {"from": account})) == roundedDec(11_0509398939) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_four.address, {"from": account}))) == rnd(2_4430193559) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_four.address, {"from": account})) == rnd(roundedDec(22_2159629526)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_four.address, {"from": account}))) == rnd(4936892146) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_four.address, {"from": account}))) == rnd(roundedDec(3_6262508961)) # hEth % for non_owner_four



    # Act
    eth_usd_price_feed.updateAnswer(1300_00000000, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1300_00000000
    # Act
    ################### tx11 ###################         Heated Partial Withdrawal Test
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txEleven = gwin_protocol.withdrawFromTranche(0, True, False, Web3.toWei(0.1, "ether"), 0, False, {"from": non_owner_four})
    txEleven.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 24_510999368436800000 # total ETH in protocol is slightly larger than recorded
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 24_5109993684 # total ETH in protocol

    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(0, {"from": account}))) == rnd(11_8539695450) # cEth in protocol 
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(0, {"from": account}))) == rnd(12_6570298233) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(0, 1300_00000000) # Test view function can estimate balances as well
    assert rnd(rounded(valTwo)) == rnd(11_8539695450)
    assert rnd(rounded(valOne)) == rnd(12_6570298233)

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, account.address, {"from": account}))) == rnd(9_2982800995) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(0, account.address, {"from": account}))) == rnd(roundedDec(78_4402226124)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, account.address, {"from": account}))) == rnd(10_7993334078) # hEth for account
    assert rnd(gwin_protocol.retrieveHEthPercentBalance.call(0, account.address, {"from": account})) == rnd(85_3228092098) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_three.address, {"from": account}))) == rnd(1_3987207581) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_three.address, {"from": account})) == roundedDec(11_0509398939) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(0, non_owner_four.address, {"from": account}))) == rnd(2_5556894454) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(0, non_owner_four.address, {"from": account})) == rnd(roundedDec(21_5597773875)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(0, non_owner_four.address, {"from": account}))) == rnd(4589756574) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(0, non_owner_four.address, {"from": account}))) == rnd(roundedDec(3_6262508961)) # hEth % for non_owner_four

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\  XAU Stable / Short  /@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#

    parent_id = 0
    # Act                                                       "ETH/USD"                               "XAU/USD"
    gwin_protocol.initializePool(1, parent_id, eth_usd_price_feed.address, "0x455448", xau_usd_price_feed.address, "0x584155", -100_0000000000, 100_0000000000, {"from": account, "value": Web3.toWei(20, "ether")})
    # Assert
    xau_usd_price_feed.updateAnswer(Web3.toWei(1600, "ether"), {"from": account}) 
    assert gwin_protocol.retrieveProtocolCEthBalance.call(1, {"from": account}) == 10000000000000000000 # cEth in protocol
    assert gwin_protocol.retrieveProtocolHEthBalance.call(1, {"from": account}) == 10000000000000000000 # hEth in protocol
    assert gwin_protocol.retrieveCEthPercentBalance.call(1, account.address, {"from": account}) == 1000000000000 # cEth % for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(1, account.address, {"from": account}) == 1000000000000 # hEth % for account
    assert gwin_protocol.retrieveCEthBalance.call(1, account.address, {"from": account}) == 10000000000000000000 # cEth for account
    assert gwin_protocol.retrieveHEthBalance.call(1, account.address, {"from": account}) == 10000000000000000000 # hEth for account
    assert xau_usd_price_feed.decimals() == 18 
    assert gwin_protocol.retrieveCurrentPrice(1, {"from": account}) == 81250000 

    ################### XAU Set Up for tx1 ###################        

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
    assert gwin_protocol.retrieveCurrentPrice(1, {"from": account}) == 85000000
    assert gwin_protocol.getProfit(1, 85000000) == 46153846153
    #                                              (i.e. 4.6%)
    # Act
    ################### XAU tx1 ###################         Deposit
    #              DEPOSIT            poolId, isCooled, isHeated, cAmount, hAmount {from, msg.value}
    xauTxOne = gwin_protocol.depositToTranche(1, True, False, Web3.toWei(1, "ether"), 0, {"from": non_owner_four, "value": Web3.toWei(1, "ether")})
    xauTxOne.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 45_510999368436800000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 45_5109993684 # total in protocol

    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(1, {"from": account}))) == rnd(10_5588235294) # cEth in protocol 
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(1, {"from": account}))) == rnd(10_4411764705) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(1, 85000000) # Test view function can estimate balances as well
    assert rnd(rounded(valTwo)) == rnd(10_5588235294)
    assert rnd(rounded(valOne)) == rnd(10_4411764705)

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, account.address, {"from": account}))) == rnd(9_5588235294) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(1, account.address, {"from": account}))) == rnd(roundedDec(90_5292479108)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, account.address, {"from": account}))) == rnd(10_4411764705) # hEth for account
    assert rnd(gwin_protocol.retrieveHEthPercentBalance.call(1, account.address, {"from": account})) == rnd(100_0000000000) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner_four.address, {"from": account}))) == rnd(1_0000000000) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner_four.address, {"from": account})) == rnd(roundedDec(9_4707520891)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four



    ################### XAU Set Up for tx2 ###################        

    target_price = 0.8
    implied_xau_price_in_usd = stable_eth / target_price
    assert feed_eth == 1300_00000000
    assert stable_eth /implied_xau_price_in_usd == target_price

    # Act
    xau_usd_price_feed.updateAnswer(Web3.toWei(implied_xau_price_in_usd, "ether"), {"from": account})
    eth_usd_price_feed.updateAnswer(feed_eth, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(1, {"from": account}) == 80000000
    # Act
    ################### XAU tx2 ###################         Deposit
    #              DEPOSIT            poolId, isCooled, isHeated, cAmount, hAmount {from, msg.value}
    xauTxTwo = gwin_protocol.depositToTranche(1, False, True, 0, Web3.toWei(1, "ether"), {"from": non_owner_two, "value": Web3.toWei(1, "ether")})
    xauTxTwo.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 46_510999368436800000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 46_5109993684 # total in protocol

    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(1, {"from": account}))) == rnd(11_2150529329) # cEth in protocol 
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(1, {"from": account}))) == rnd(10_7849470670) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(1, 80000000) # Test view function can estimate balances as well
    assert rnd(rounded(valTwo)) == rnd(11_2150529329) # cEth in protocol 
    assert rnd(rounded(valOne)) == rnd(10_7849470670) # hEth in protocol

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, account.address, {"from": account}))) == rnd(10_1529030729) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(1, account.address, {"from": account}))) == rnd(roundedDec(90_5292479108)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, account.address, {"from": account}))) == rnd(9_7849470670) # hEth for account
    assert rnd(gwin_protocol.retrieveHEthPercentBalance.call(1, account.address, {"from": account})) == rnd(90_7278172643) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner_two.address, {"from": account}))) == rnd(1_0000000000) # hEth for non_owner_two
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner_two.address, {"from": account}))) == rnd(roundedDec(92_721827356)) # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner_four.address, {"from": account}))) == rnd(1_0621498599) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner_four.address, {"from": account})) == rnd(roundedDec(9_4707520891)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four



    ################### XAU Set Up for tx3 ###################        

    target_price = 2.15
    implied_xau_price_in_usd = stable_eth / target_price
    assert feed_eth == 1300_00000000
    assert stable_eth /implied_xau_price_in_usd == target_price

    # Act
    xau_usd_price_feed.updateAnswer(Web3.toWei(implied_xau_price_in_usd, "ether"), {"from": account})
    eth_usd_price_feed.updateAnswer(feed_eth, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(1, {"from": account}) == 2_15000000
    # Act
    ################### XAU tx3 ###################         Deposit
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txThree = gwin_protocol.withdrawFromTranche(1, False, True, 0, 0, True, {"from": non_owner_two})
    txThree.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 44_857561775382400000 # total in protocol
    assert rnd(rounded(gwin_protocol.retrieveEthInContract({"from": account}))) == rnd(44_8575617753) # total in protocol

    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(1, {"from": account}))) == rnd(4_1677630802) # cEth in protocol 
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(1, {"from": account}))) == rnd(16_1787993267) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(1, 2_15000000) # Test view function can estimate balances as well
    assert rnd(rounded(valTwo)) == rnd(4_1677630802) # cEth in protocol 
    assert rnd(rounded(valOne)) == rnd(16_1787993267) # hEth in protocol

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, account.address, {"from": account}))) == rnd(3_7730445712) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(1, account.address, {"from": account}))) == rnd(roundedDec(90_5292479108)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, account.address, {"from": account}))) == rnd(16_1787993267) # hEth for account
    assert rnd(gwin_protocol.retrieveHEthPercentBalance.call(1, account.address, {"from": account})) == rnd(100_0000000000) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner_two.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner_four.address, {"from": account}))) == rnd(3947185089) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner_four.address, {"from": account})) == rnd(roundedDec(9_4707520891)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four




    ################### XAU Set Up for tx4 ###################        

    target_price = 0.75
    implied_xau_price_in_usd = stable_eth / target_price
    assert feed_eth == 1300_00000000
    assert stable_eth /implied_xau_price_in_usd == target_price

    # Act
    xau_usd_price_feed.updateAnswer(Web3.toWei(implied_xau_price_in_usd, "ether"), {"from": account})
    eth_usd_price_feed.updateAnswer(feed_eth, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(1, {"from": account}) == 75000000
    # Act
    ################### XAU tx4 ###################         Deposit
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txFour = gwin_protocol.withdrawFromTranche(1, True, False, Web3.toWei(1, "ether"), 0, False, {"from": non_owner_four})
    txFour.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 43_857561775382400000 # total in protocol
    assert rnd(rounded(gwin_protocol.retrieveEthInContract({"from": account}))) == rnd(43_8575617753) # total in protocol

    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(1, {"from": account}))) == rnd(15_5401939127) # cEth in protocol 
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(1, {"from": account}))) == rnd(3_8063684941) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(1, 75000000) # Test view function can estimate balances as well
    assert rnd(rounded(valTwo)) == rnd(15_5401939127) # cEth in protocol 
    assert rnd(rounded(valOne)) == rnd(3_8063684941) # hEth in protocol

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, account.address, {"from": account}))) == rnd(14_9737131522) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(1, account.address, {"from": account}))) == rnd(roundedDec(96_3547381472)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, account.address, {"from": account}))) == rnd(3_8063684941) # hEth for account
    assert rnd(gwin_protocol.retrieveHEthPercentBalance.call(1, account.address, {"from": account})) == rnd(100_0000000000) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner_two.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner_four.address, {"from": account}))) == rnd(5664807605) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner_four.address, {"from": account})) == rnd(roundedDec(3_6452618527)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four




    ################### XAU Set Up for tx5 ###################    
    # Let's Liquidate It!    

    target_price = 0.4
    implied_xau_price_in_usd = stable_eth / target_price
    assert feed_eth == 1300_00000000
    assert stable_eth /implied_xau_price_in_usd == target_price

    # Act
    xau_usd_price_feed.updateAnswer(Web3.toWei(implied_xau_price_in_usd, "ether"), {"from": account})
    eth_usd_price_feed.updateAnswer(feed_eth, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(1, {"from": account}) == 40000000
    # Act
    ################### XAU tx5 ###################         Deposit
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txFour = gwin_protocol.withdrawFromTranche(1, True, False, Web3.toWei(1, "ether"), 0, False, {"from": account})
    txFour.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 42_857561775382400000 # total in protocol
    assert rnd(rounded(gwin_protocol.retrieveEthInContract({"from": account}))) == rnd(42_8575617753) # total in protocol

    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(1, {"from": account}))) == rnd(18_3465624069) # cEth in protocol 
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(1, {"from": account}))) == rnd(0) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(1, 40000000) # Test view function can estimate balances as well
    assert rnd(rounded(valTwo)) == rnd(18_3465624069) # cEth in protocol 
    assert rnd(rounded(valOne)) == rnd(0) # hEth in protocol

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, account.address, {"from": account}))) == rnd(17_6413295477) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(1, account.address, {"from": account}))) == rnd(roundedDec(96_1560490538)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(gwin_protocol.retrieveHEthPercentBalance.call(1, account.address, {"from": account})) == rnd(0) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner_two.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(1, non_owner_four.address, {"from": account}))) == rnd(7052328592) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(1, non_owner_four.address, {"from": account})) == rnd(roundedDec(3_8439509461)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(1, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(1, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four






#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\  XAU Long Short (-200, 400)  /@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#
    xau_ls_pool_id = 2
    xau_usd_price_feed.updateAnswer(Web3.toWei(1600, "ether"), {"from": account}) 
    eth_usd_price_feed.updateAnswer(feed_eth, {"from": account})
    assert gwin_protocol.retrieveCurrentPrice(0, {"from": account}) == 1300_00000000

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

    ################### XAU Set Up for tx1 ###################        

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
    #                                              (i.e. 4.6%)
    # Act
    ################### XAU tx1 ###################         Deposit
    #              DEPOSIT            poolId, isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.depositToTranche(xau_ls_pool_id, True, False, Web3.toWei(1, "ether"), 0, {"from": non_owner_four, "value": Web3.toWei(1, "ether")})
    tx.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 63_857561775382400000 # total in protocol
    assert rnd(rounded(gwin_protocol.retrieveEthInContract({"from": account}))) == rnd(63_8575617753) # total in protocol

    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(xau_ls_pool_id, {"from": account}))) == rnd(9_6764705882) # cEth in protocol 
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(xau_ls_pool_id, {"from": account}))) == rnd(11_3235294117) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(xau_ls_pool_id, 85000000) # Test view function can estimate balances as well
    assert rnd(rounded(valTwo)) == rnd(9_6764705882)
    assert rnd(rounded(valOne)) == rnd(11_3235294117)

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, account.address, {"from": account}))) == rnd(8_6764705882) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, account.address, {"from": account}))) == rnd(roundedDec(89_6656534954)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, account.address, {"from": account}))) == rnd(11_3235294117) # hEth for account
    assert rnd(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, account.address, {"from": account})) == rnd(100_0000000000) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account})) == 0 # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account}))) == rnd(1_0000000000) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account})) == rnd(roundedDec(10_3343465045)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four



    ################### XAU Set Up for tx2 ###################        

    target_price = 0.8
    implied_xau_price_in_usd = stable_eth / target_price
    assert feed_eth == 1300_00000000
    assert stable_eth /implied_xau_price_in_usd == target_price

    # Act
    xau_usd_price_feed.updateAnswer(Web3.toWei(implied_xau_price_in_usd, "ether"), {"from": account})
    eth_usd_price_feed.updateAnswer(feed_eth, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(xau_ls_pool_id, {"from": account}) == 80000000
    # Act
    ################### XAU tx2 ###################         Deposit
    #              DEPOSIT            poolId, isCooled, isHeated, cAmount, hAmount {from, msg.value}
    tx = gwin_protocol.depositToTranche(xau_ls_pool_id, False, True, 0, Web3.toWei(1, "ether"), {"from": non_owner_two, "value": Web3.toWei(1, "ether")})
    tx.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 64_857561775382400000 # total in protocol
    assert rnd(rounded(gwin_protocol.retrieveEthInContract({"from": account}))) == rnd(64_8575617753) # total in protocol

    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(xau_ls_pool_id, {"from": account}))) == rnd(11_7047649942) # cEth in protocol 
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(xau_ls_pool_id, {"from": account}))) == rnd(10_2952350057) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(xau_ls_pool_id, 80000000) # Test view function can estimate balances as well
    assert rnd(rounded(valTwo)) == rnd(11_7047649942) # cEth in protocol 
    assert rnd(rounded(valOne)) == rnd(10_2952350057) # hEth in protocol

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, account.address, {"from": account}))) == rnd(10_4951540221) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, account.address, {"from": account}))) == rnd(roundedDec(89_6656534954)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, account.address, {"from": account}))) == rnd(9_2952350057) # hEth for account
    assert rnd(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, account.address, {"from": account})) == rnd(90_2867685930) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}))) == rnd(1_0000000000) # hEth for non_owner_two
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}))) == rnd(roundedDec(9_7132314069)) # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account}))) == rnd(1_2096109720) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account})) == rnd(roundedDec(10_3343465045)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four



    ################### XAU Set Up for tx3 ###################        

    target_price = 1
    implied_xau_price_in_usd = stable_eth / target_price
    assert feed_eth == 1300_00000000
    assert stable_eth /implied_xau_price_in_usd == target_price

    # Act
    xau_usd_price_feed.updateAnswer(Web3.toWei(implied_xau_price_in_usd, "ether"), {"from": account})
    eth_usd_price_feed.updateAnswer(feed_eth, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(xau_ls_pool_id, {"from": account}) == 1_00000000
    # Act
    ################### XAU tx3 ###################         Withdrawal
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txThree = gwin_protocol.withdrawFromTranche(xau_ls_pool_id, False, True, 0, 0, True, {"from": non_owner_two})
    txThree.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 63_219120048424200000 # total in protocol
    assert rnd(rounded(gwin_protocol.retrieveEthInContract({"from": account}))) == rnd(63_2191200484) # total in protocol

    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(xau_ls_pool_id, {"from": account}))) == rnd(5_1318573777) # cEth in protocol 
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(xau_ls_pool_id, {"from": account}))) == rnd(15_2297008953) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(xau_ls_pool_id, 1_00000000) # Test view function can estimate balances as well
    assert rnd(rounded(valTwo)) == rnd(5_1318573777) # cEth in protocol 
    assert rnd(rounded(valOne)) == rnd(15_2297008953) # hEth in protocol

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, account.address, {"from": account}))) == rnd(4_6015134541) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, account.address, {"from": account}))) == rnd(roundedDec(89_6656534954)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, account.address, {"from": account}))) == rnd(15_2297008953) # hEth for account
    assert rnd(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, account.address, {"from": account})) == rnd(100_0000000000) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account}))) == rnd(5303439235) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account})) == rnd(roundedDec(10_3343465045)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four




    ################### XAU Set Up for tx4 ###################        

    target_price = 0.8
    implied_xau_price_in_usd = stable_eth / target_price
    assert feed_eth == 1300_00000000
    assert stable_eth /implied_xau_price_in_usd == target_price

    # Act
    xau_usd_price_feed.updateAnswer(Web3.toWei(implied_xau_price_in_usd, "ether"), {"from": account})
    eth_usd_price_feed.updateAnswer(feed_eth, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(xau_ls_pool_id, {"from": account}) == 80000000
    # Act
    ################### XAU tx4 ###################         Withdrawal
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txFour = gwin_protocol.withdrawFromTranche(xau_ls_pool_id, True, False, Web3.toWei(1, "ether"), 0, False, {"from": non_owner_four})
    txFour.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 62_219120048424200000 # total in protocol
    assert rnd(rounded(gwin_protocol.retrieveEthInContract({"from": account}))) == rnd(62_2191200484) # total in protocol

    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(xau_ls_pool_id, {"from": account}))) == rnd(14_2816201093) # cEth in protocol 
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(xau_ls_pool_id, {"from": account}))) == rnd(5_0799381636) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(xau_ls_pool_id, 80000000) # Test view function can estimate balances as well
    assert rnd(rounded(valTwo)) == rnd(14_2816201093) # cEth in protocol 
    assert rnd(rounded(valOne)) == rnd(5_0799381636) # hEth in protocol

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, account.address, {"from": account}))) == rnd(13_7023645357) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, account.address, {"from": account}))) == rnd(roundedDec(95_9440485800)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, account.address, {"from": account}))) == rnd(5_0799381636) # hEth for account
    assert rnd(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, account.address, {"from": account})) == rnd(100_0000000000) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account}))) == rnd(5792555736) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account})) == rnd(roundedDec(4_0559514199)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four




    ################### XAU Set Up for tx5 ###################    
    # Let's Liquidate It!    

    target_price = 0.4
    implied_xau_price_in_usd = stable_eth / target_price
    assert feed_eth == 1300_00000000
    assert stable_eth /implied_xau_price_in_usd == target_price

    # Act
    xau_usd_price_feed.updateAnswer(Web3.toWei(implied_xau_price_in_usd, "ether"), {"from": account})
    eth_usd_price_feed.updateAnswer(feed_eth, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentPrice(xau_ls_pool_id, {"from": account}) == 40000000
    # Act
    ################### XAU tx5 ###################         Withdrawal
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txFour = gwin_protocol.withdrawFromTranche(xau_ls_pool_id, True, False, Web3.toWei(1, "ether"), 0, False, {"from": account})
    txFour.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) >= 61_219120048424200000 # total in protocol
    assert rnd(rounded(gwin_protocol.retrieveEthInContract({"from": account}))) == rnd(61_2191200484) # total in protocol

    assert rnd(rounded(gwin_protocol.retrieveProtocolCEthBalance.call(xau_ls_pool_id, {"from": account}))) == rnd(18_3615582730) # cEth in protocol 
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call(xau_ls_pool_id, {"from": account}))) == rnd(0) # hEth in protocol

    valOne, valTwo = gwin_protocol.simulateInteract.call(xau_ls_pool_id, 40000000) # Test view function can estimate balances as well
    assert rnd(rounded(valTwo)) == rnd(18_3615582730) # cEth in protocol 
    assert rnd(rounded(valOne)) == rnd(0) # hEth in protocol

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, account.address, {"from": account}))) == rnd(17_5762628753) # cEth for account 
    assert rnd(roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, account.address, {"from": account}))) == rnd(roundedDec(95_7231549413)) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, account.address, {"from": account}))) == rnd(0) # hEth for account
    assert rnd(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, account.address, {"from": account})) == rnd(0) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}))) == rnd(0) # cEth for non_owner_two 
    assert gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}) == 0 # cEth % for non_owner_two
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}))) == rnd(0) # hEth for non_owner_two
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner_two.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_two     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account}))) == rnd(0) # cEth for non_owner_three 
    assert gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account}) == 0 # cEth % for non_owner_three
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account}))) == rnd(0) # hEth for non_owner_three
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner_three.address, {"from": account})) == roundedDec(0) # hEth % for non_owner_three

    # Dan
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account}))) == rnd(7852953976) # cEth for non_owner_four 
    assert rnd(gwin_protocol.retrieveCEthPercentBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account})) == rnd(roundedDec(4_2768450586)) # cEth % for non_owner_four
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account}))) == rnd(0) # hEth for non_owner_four
    assert rnd(roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(xau_ls_pool_id, non_owner_four.address, {"from": account}))) == rnd(roundedDec(0)) # hEth % for non_owner_four

    # Clean Up
    empty_account(gwin_protocol, account)
    empty_account(gwin_protocol, non_owner)
    empty_account(gwin_protocol, non_owner_two)
    empty_account(gwin_protocol, non_owner_three)
    empty_account(gwin_protocol, non_owner_four)

    # Ensure dust is less that $0.01
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) < 9000000000000 # total in protocol