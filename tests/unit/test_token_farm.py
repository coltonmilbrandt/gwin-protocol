from random import random
from brownie import TokenFarm, GwinToken, network, exceptions
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, INITIAL_PRICE_FEED_VALUE, DECIMALS, get_account, get_contract
from scripts.deploy import deploy_token_farm_and_gwin_token
from web3 import Web3
import pytest

def test_get_account():
    account = get_account()
    assert account

def test_set_price_feed_contract():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    token_farm, gwin_ERC20 = deploy_token_farm_and_gwin_token()
    # Act
    price_feed_address = get_contract("eth_usd_price_feed")
    token_farm.setPriceFeedContract(gwin_ERC20.address, get_contract("eth_usd_price_feed"), {"from": account})
    # Assert
    assert token_farm.tokenPriceFeedMapping(gwin_ERC20.address) == price_feed_address
    with pytest.raises(exceptions.VirtualMachineError):
        token_farm.setPriceFeedContract(
            gwin_ERC20.address, price_feed_address, {"from": non_owner}
        )

def test_stake_tokens(amount_staked):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    token_farm, gwin_ERC20 = deploy_token_farm_and_gwin_token()
    # Act
    gwin_ERC20.approve(token_farm.address, amount_staked, {"from": account})
    token_farm.stakeTokens(amount_staked, gwin_ERC20.address, {"from": account})
    # Assert
    assert token_farm.stakingBalance(gwin_ERC20.address, account.address) == amount_staked
    assert token_farm.uniqueTokensStaked(account.address) == 1
    assert token_farm.stakers(0) == account.address
    return token_farm, gwin_ERC20

def test_issue_tokens(amount_staked):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    token_farm, gwin_ERC20 = test_stake_tokens(amount_staked)
    starting_balance = gwin_ERC20.balanceOf(account.address)
    # Act
    token_farm.issueTokens({"from": account})
    # Assert
    assert (
        gwin_ERC20.balanceOf(account.address) == starting_balance + INITIAL_PRICE_FEED_VALUE
    )

def test_get_user_total_value_with_different_tokens(amount_staked, random_erc20):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    token_farm, gwin_ERC20 = test_stake_tokens(amount_staked)
    # Act
    token_farm.addAllowedTokens(random_erc20.address, {"from": account})
    token_farm.setPriceFeedContract(
        random_erc20.address, get_contract("eth_usd_price_feed"), {"from": account}
    )
    random_erc20_stake_amount = amount_staked * 2
    random_erc20.approve(
        token_farm.address, random_erc20_stake_amount, {"from": account}
    )
    token_farm.stakeTokens(
        random_erc20_stake_amount, random_erc20.address, {"from": account}
    )
    # Assert
    total_value = token_farm.getUserTotalValue(account.address)
    assert total_value == INITIAL_PRICE_FEED_VALUE * 3

def test_can_get_token_value():
    account = get_account()
    token_farm, gwin_ERC20 = deploy_token_farm_and_gwin_token()
    assert token_farm.getTokenValue(gwin_ERC20.address) == (
        INITIAL_PRICE_FEED_VALUE,
        DECIMALS,
    )

def test_can_deploy_ERC20():
    account = get_account()
    gwin_ERC20 = GwinToken.deploy({"from": account})
    assert gwin_ERC20

def test_can_add_allowed_token():
    account = get_account()
    token_farm, gwin_ERC20 = deploy_token_farm_and_gwin_token()
    token_farm.addAllowedTokens(gwin_ERC20.address, {"from": account})
    assert token_farm.allowedTokens(0) == gwin_ERC20.address

def test_only_owner_can_add_allowed_token():
    account = get_account()
    non_owner = get_account(index=1)
    token_farm, gwin_ERC20 = deploy_token_farm_and_gwin_token()
    with pytest.raises(exceptions.VirtualMachineError):
        token_farm.addAllowedTokens(gwin_ERC20.address, {"from": non_owner})
    

    