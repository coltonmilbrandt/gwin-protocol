from brownie import GwinProtocol, GwinToken, network, exceptions
from pyparsing import null_debug_action
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, INITIAL_PRICE_FEED_VALUE, DECIMALS, get_account, get_contract, rounded, roundedDec, extra_rounded, rnd
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
    non_owner_two = get_account(index=2)
    non_owner_three = get_account(index=3)
    gwin_protocol, gwin_ERC20 = deploy_gwin_protocol_and_gwin_token()
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

    # with pytest.raises(exceptions.VirtualMachineError):
    #     gwin_protocol.retrieveHEthPercentBalance.call(1, {"from": account}) == 0 # hEth % for non_owner

    # Act
    gwin_protocol.changeCurrentEthUsd(1200, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1200_00000000;
    # Act
    ################### tx1 ###################
    #                                     isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txOne = gwin_protocol.depositToTranche(True, False, Web3.toWei(1, "ether"), 0, {"from": non_owner, "value": Web3.toWei(1, "ether")})
    txOne.wait(1)
    # Assert
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call({"from": account})) == 10_1666666666 # cEth in protocol
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call({"from": account})) == 10_8333333333 # hEth in protocol

    assert gwin_protocol.retrieveCEthBalance.call(account.address, {"from": account}) == 9_166666666666666666 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(account.address, {"from": account}) == 90_1639344262 # cEth % for account
    assert gwin_protocol.retrieveHEthBalance.call(account.address, {"from": account}) == 10_833333333333333333 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(account.address, {"from": account}) == 100_0000000000 # hEth % for account 

    assert gwin_protocol.retrieveCEthBalance.call(non_owner.address, {"from": account}) == 1_000000000000000000 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner.address, {"from": account}) == 9_8360655737 # cEth % non_owner
    assert gwin_protocol.retrieveHEthBalance.call(non_owner.address, {"from": account}) == 0 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # hEth % for non_owner



    # Act
    gwin_protocol.changeCurrentEthUsd(1400, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1400_00000000;
    # Act
    ################### tx2 ###################
    #              DEPOSIT              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txTwo = gwin_protocol.depositToTranche(False, True, 0, Web3.toWei(1, "ether"), {"from": non_owner_two, "value": Web3.toWei(1, "ether")})
    txTwo.wait(1)
    # Assert
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call({"from": account})) == 9_4174225245 # cEth in protocol
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call({"from": account})) == 12_5825774754 # hEth in protocol

    assert rounded(gwin_protocol.retrieveCEthBalance.call(account.address, {"from": account})) == 8_4911186696 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(account.address, {"from": account}) == 90_1639344262 # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(account.address, {"from": account})) == 11_5825774754 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(account.address, {"from": account}) == 92_0525027407 # hEth % for account 

    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner.address, {"from": account})) == 9263038548 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner.address, {"from": account}) == 9_8360655737 # cEth % non_owner
    assert gwin_protocol.retrieveHEthBalance.call(non_owner.address, {"from": account}) == 0 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner_two.address, {"from": account})) == 0 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner_two.address, {"from": account}) == 0 # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner_two.address, {"from": account})) == 1_0000000000 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner_two.address, {"from": account}) == 7_9474972592 # hEth % for account 



    # Act
    gwin_protocol.changeCurrentEthUsd(1300, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1300_00000000;
    # Act
    ################### tx3 ###################
    #         WITHDRAWAL ALL         isCooled, isHeated, {from}
    txThree = gwin_protocol.withdrawAll(True, False, {"from": non_owner})
    txThree.wait(1)
    # Assert
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call({"from": account})) == 8_8804772808 # cEth in protocol
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call({"from": account})) == 12_1507433794 # hEth in protocol

    assert rounded(gwin_protocol.retrieveCEthBalance.call(account.address, {"from": account})) == 8_8804772808 # cEth for account 
    assert roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(account.address, {"from": account})) == 100_0000000000 # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(account.address, {"from": account})) == 11_1850633823 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(account.address, {"from": account}) == 92_0525027407 # hEth % for account 

    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner.address, {"from": account})) == 0 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert gwin_protocol.retrieveHEthBalance.call(non_owner.address, {"from": account}) == 0 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner_two.address, {"from": account})) == 0 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner_two.address, {"from": account}) == 0 # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner_two.address, {"from": account})) == 9656799970 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner_two.address, {"from": account}) == 7_9474972592 # hEth % for account 



    # Act
    gwin_protocol.changeCurrentEthUsd(1150, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1150_00000000;
    # Act
    ################### tx4 ###################
    #              DEPOSIT              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txFour = gwin_protocol.depositToTranche(False, True, 0, Web3.toWei(2, "ether"), {"from": non_owner_three, "value": Web3.toWei(2, "ether")})
    txFour.wait(1)
    # Assert
    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call({"from": account})) == 9_5828598866 # cEth in protocol
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call({"from": account})) == 13_4483607736 # hEth in protocol

    # Owner 
    assert rounded(gwin_protocol.retrieveCEthBalance.call(account.address, {"from": account})) == 9_5828598866 # cEth for account 
    assert roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(account.address, {"from": account})) == 100_0000000000 # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(account.address, {"from": account})) == 10_5385026149 # hEth for account
    assert gwin_protocol.retrieveHEthPercentBalance.call(account.address, {"from": account}) == 78_3627297951 # hEth % for account 

    # Alice
    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner.address, {"from": account})) == 0 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert gwin_protocol.retrieveHEthBalance.call(non_owner.address, {"from": account}) == 0 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    # Bob
    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner_two.address, {"from": account})) == 0 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner_two.address, {"from": account}) == 0 # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner_two.address, {"from": account})) == 9098581587 # hEth for account
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(non_owner_two.address, {"from": account})) == 6_7655692320 # hEth % for account     

    # Chris
    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner_three.address, {"from": account})) == 0 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner_three.address, {"from": account}) == 0 # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner_three.address, {"from": account})) == 2_0000000000 # hEth for account
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(non_owner_three.address, {"from": account})) == 14_8717009730 # hEth % for account



    # Act
    gwin_protocol.changeCurrentEthUsd(1100, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1100_00000000;
    # Act
    ################### tx5 ###################
    #              DEPOSIT              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txFive = gwin_protocol.depositToTranche(True, True, Web3.toWei(3, "ether"), Web3.toWei(1, "ether"), {"from": non_owner, "value": Web3.toWei(4, "ether")})
    txFive.wait(1)
    # Assert
    # Make sure all ETH has been accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) > 27_031220660268900000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 27_0312206602 # total in protocol

    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call({"from": account})) == 12_8519507547 # cEth in protocol 
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call({"from": account}))) == rnd(14_1792699054) # hEth in protocol

    # Owner 
    assert rounded(gwin_protocol.retrieveCEthBalance.call(account.address, {"from": account})) == 9_8519507547 # cEth for account 
    assert roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(account.address, {"from": account})) == roundedDec(76_6572401556) # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(account.address, {"from": account})) == 10_3276356650 # hEth for account
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(account.address, {"from": account})) == 72_8361596460 # hEth % for account 

    # Alice
    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner.address, {"from": account})) == 3_0000000000 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner.address, {"from": account}) == 23_3427598443 # cEth % non_owner
    assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner.address, {"from": account})) == 1_0000000000 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner.address, {"from": account}) == 7_0525492967 # hEth % for non_owner

    # Bob
    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner_two.address, {"from": account})) == 0 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner_two.address, {"from": account}) == 0 # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner_two.address, {"from": account})) == 8916526297 # hEth for account
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(non_owner_two.address, {"from": account})) == roundedDec(6_2884241267) # hEth % for account     

    # Chris
    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner_three.address, {"from": account})) == 0 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner_three.address, {"from": account}) == 0 # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner_three.address, {"from": account})) == 1_9599816107 # hEth for account
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(non_owner_three.address, {"from": account})) == roundedDec(13_8228669304) # hEth % for account



    # Act
    gwin_protocol.changeCurrentEthUsd(1000, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1000_00000000;
    # Act
    ################### tx6 ###################
    #         WITHDRAWAL ALL         isCooled, isHeated, {from}
    txSix = gwin_protocol.withdrawAll(False, True, {"from": non_owner_two})
    txSix.wait(1)
    # Assert
    # Make sure all ETH has been accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) > 26_182166438542800000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 26_1821664385 # total in protocol

    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call({"from": account})) == 13_5293606613 # cEth in protocol 
    assert rounded(gwin_protocol.retrieveProtocolHEthBalance.call({"from": account})) == 12_6528057772 # hEth in protocol

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(account.address, {"from": account}))) == rnd(10_3712344937) # cEth for account 
    assert roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(account.address, {"from": account})) == roundedDec(76_6572401556) # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(account.address, {"from": account})) == 9_8342363039 # hEth for account
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(account.address, {"from": account})) == roundedDec(77_7237592766) # hEth % for account 

    # Alice
    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner.address, {"from": account})) == 3_1581261676 # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner.address, {"from": account}) == 23_3427598443 # cEth % non_owner
    assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner.address, {"from": account})) == 9522253323 # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner.address, {"from": account}) == 7_5258037558 # hEth % for non_owner

    # Bob
    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner_two.address, {"from": account})) == 0 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner_two.address, {"from": account}) == 0 # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner_two.address, {"from": account})) == 0 # hEth for account
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(non_owner_two.address, {"from": account})) == 0 # hEth % for account     

    # Chris
    assert rounded(gwin_protocol.retrieveCEthBalance.call(non_owner_three.address, {"from": account})) == 0 # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner_three.address, {"from": account}) == 0 # cEth % for account
    assert rounded(gwin_protocol.retrieveHEthBalance.call(non_owner_three.address, {"from": account})) == 1_8663441407 # hEth for account
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(non_owner_three.address, {"from": account})) == roundedDec(14_7504369675) # hEth % for account



    # Act
    gwin_protocol.changeCurrentEthUsd(1300, {"from": account})
    # Assert
    assert gwin_protocol.retrieveCurrentEthUsd() == 1300_00000000;
    # Act
    ################### tx7 ###################
    #         WITHDRAWAL ALL         isCooled, isHeated, {from}
    txSix = gwin_protocol.withdrawAll(True, True, {"from": non_owner})
    txSix.wait(1)
    # Assert
    # Make sure all ETH sufficiently accounted for    &    dust remains in pool (true ETH balance > accounted balance)
    assert gwin_protocol.retrieveEthInContract({"from": account}) > 22_310999368436800000 # total in protocol
    assert rounded(gwin_protocol.retrieveEthInContract({"from": account})) == 22_3109993684 # total in protocol

    assert rounded(gwin_protocol.retrieveProtocolCEthBalance.call({"from": account})) == 9_2120216726 # cEth in protocol 
    assert rnd(rounded(gwin_protocol.retrieveProtocolHEthBalance.call({"from": account}))) == rnd(13_0989776957) # hEth in protocol

    # Owner 
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(account.address, {"from": account}))) == rnd(9_2120216726) # cEth for account 
    assert roundedDec(gwin_protocol.retrieveCEthPercentBalance.call(account.address, {"from": account})) == roundedDec(100_0000000000) # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(account.address, {"from": account}))) == rnd(11_0095770555) # hEth for account
    assert rnd(gwin_protocol.retrieveHEthPercentBalance.call(account.address, {"from": account})) == rnd(84_0491320102) # hEth % for account 

    # Alice
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(non_owner.address, {"from": account}))) == rnd(0) # cEth for non_owner
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # cEth % non_owner
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(non_owner.address, {"from": account}))) == rnd(0) # hEth for non_owner
    assert gwin_protocol.retrieveHEthPercentBalance.call(non_owner.address, {"from": account}) == 0 # hEth % for non_owner

    # Bob
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(non_owner_two.address, {"from": account}))) == rnd(0) # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner_two.address, {"from": account}) == 0 # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(non_owner_two.address, {"from": account}))) == rnd(0) # hEth for account
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(non_owner_two.address, {"from": account})) == 0 # hEth % for account     

    # Chris
    assert rnd(rounded(gwin_protocol.retrieveCEthBalance.call(non_owner_three.address, {"from": account}))) == rnd(0) # cEth for account 
    assert gwin_protocol.retrieveCEthPercentBalance.call(non_owner_three.address, {"from": account}) == 0 # cEth % for account
    assert rnd(rounded(gwin_protocol.retrieveHEthBalance.call(non_owner_three.address, {"from": account}))) == rnd(2_0894006402) # hEth for account
    assert roundedDec(gwin_protocol.retrieveHEthPercentBalance.call(non_owner_three.address, {"from": account})) == roundedDec(15_9508679897) # hEth % for account








    #I3 Deposit to both Tranches
    #I4 Withdrawal from both Tranches