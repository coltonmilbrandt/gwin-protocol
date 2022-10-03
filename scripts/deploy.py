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
    value = gwin_protocol.deposit.call({"from": account})
    print(value)
    
    return gwin_protocol, gwin_ERC20

def main():
    deploy_gwin_protocol_and_gwin_token()
