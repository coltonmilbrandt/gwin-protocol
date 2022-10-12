from abc import abstractclassmethod
from brownie import GwinToken, GwinProtocol, network, config
from scripts.helpful_scripts import get_account, get_contract
from web3 import Web3

KEPT_BALANCE = Web3.toWei(100, "ether")

def deploy_gwin_protocol_and_gwin_token():
    account = get_account()
    gwin_ERC20 = GwinToken.deploy({"from": account})
    gwin_protocol = GwinProtocol.deploy(gwin_ERC20.address, {"from": account}, publish_source=config["networks"][network.show_active()]["verify"])
    tx = gwin_ERC20.transfer(gwin_protocol.address, gwin_ERC20.totalSupply() - KEPT_BALANCE, {"from": account})
    tx.wait(1)
    # adds the tokens we are allowing to be staked
    # we will allow GWIN, WETH, FAU (i.e. DAI)
    weth_token = get_contract("weth_token")
    fau_token = get_contract("fau_token")
    non_owner = get_account(index=1)
    
    # txTwo = gwin_protocol.initializeProtocol({"from": account, "value": Web3.toWei(20, "ether")})
    # txTwo.wait(1)
    # gwin_protocol.changeCurrentEthUsd(1200, {"from": account})
    # txThree = gwin_protocol.depositToTranche(True, {"from": non_owner, "value": Web3.toWei(1, "ether")})
    # txThree.wait(1)

    # txTwo = gwin_protocol.initializeProtocol({"from": account, "value": Web3.toWei(20, "ether")})
    # txTwo.wait(1)
    # x = gwin_protocol.retrieveBalance.call({"from": account})
    # print(x)
    # print(gwin_protocol.balance())
    # gwin_protocol.depositToTranche(True, {"from": account, "value": Web3.toWei(1, "ether")})
    # print(gwin_protocol.retrieveProtocolCEthBalance.call({"from": account}))
    # print(gwin_protocol.retrieveProtocolHEthBalance.call({"from": account}))
    # print(gwin_protocol.balance())
    # # user 0 perc bal
    # print(gwin_protocol.retrieveCEthBalance.call(0, {"from": account}))
    # print(gwin_protocol.retrieveCEthPercentBalance.call(0, {"from": account}))
    # print(gwin_protocol.retrieveCEthBalance.call(1, {"from": account}))
    # print(gwin_protocol.retrieveCEthPercentBalance.call(1, {"from": account}))
    
    return gwin_protocol, gwin_ERC20

def main():
    deploy_gwin_protocol_and_gwin_token()
