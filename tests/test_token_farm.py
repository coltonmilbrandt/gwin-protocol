from brownie import TokenFarm, GwinToken
from scripts.helpful_scripts import get_account
from web3 import Web3

def test_get_account():
    account = get_account()
    token_farm = TokenFarm.deploy({"from": account})
    assert account

def test_can_deploy_ERC20():
    account = get_account()
    gwin_ERC20 = GwinToken.deploy({"from": account})
    assert gwin_ERC20

def test_can_add_allowed_token():
    account = get_account()
    gwin_ERC20 = GwinToken.deploy({"from": account})
    token_farm = TokenFarm.deploy({"from": account})
    token_farm.addAllowedTokens(gwin_ERC20.address, {"from": account})
    assert token_farm.allowedTokens[0]
    
def test_can_stake_tokens():
    account = get_account()
    gwin_ERC20 = GwinToken.deploy({"from": account})
    token_farm = TokenFarm.deploy({"from": account})
    token_farm.addAllowedTokens(gwin_ERC20.address, {"from": account})
    token_farm.stakeTokens(Web3.toWei(1, "ether"), gwin_ERC20.address, {"from": account})
    assert token_farm.balanceOf == Web3.toWei(1, "ether")
    