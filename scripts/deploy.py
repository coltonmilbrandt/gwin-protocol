from abc import abstractclassmethod
from brownie import GwinToken, GwinProtocol, network, config
from scripts.helpful_scripts import deploy_mocks, get_account, get_contract, fund_with_link, LOCAL_BLOCKCHAIN_ENVIRONMENTS
from web3 import Web3

KEPT_BALANCE = Web3.toWei(100, "ether")

def deploy_gwin_protocol_and_gwin_token():
    print('Getting account...')
    account = get_account()
    print(f'account is: ' + account.address)
    # account = get_account(id="freecodecamp-account")
    print('Gwin ERC20 deploying...')
    gwin_ERC20 = GwinToken.deploy({"from": account})
    print('Gwin ERC20 is deployed.')
    print('Gwin Protocol is deploying...')
    gwin_protocol = GwinProtocol.deploy(
        gwin_ERC20.address,
        get_contract("link_token").address,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    print('Gwin Protocol is deployed!')
    # We could do get_contract().address possibly. The entire contract may not be necessary
    print('Getting eth_usd_price_feed...')
    eth_usd_price_feed = get_contract("eth_usd_price_feed")
    xau_usd_price_feed = get_contract("xau_usd_price_feed")
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        eth_usd_price_feed.updateAnswer(1000_00000000, {"from": account})
        xau_usd_price_feed.updateAnswer(Web3.toWei(1600, "ether"), {"from": account})
    tx = gwin_ERC20.transfer(gwin_protocol.address, gwin_ERC20.totalSupply() - KEPT_BALANCE, {"from": account})
    tx.wait(1)
    # adds the tokens we are allowing to be staked
    # we will allow GWIN, WETH, FAU (i.e. DAI)
    # weth_token = get_contract("weth_token")
    # fau_token = get_contract("fau_token")
    
    return gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed

def main():
    deploy_gwin_protocol_and_gwin_token()
