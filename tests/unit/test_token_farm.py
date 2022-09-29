from brownie import GwinProtocol, GwinToken, network, exceptions
from parsimonious import UndefinedLabel
from pyparsing import null_debug_action
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, INITIAL_PRICE_FEED_VALUE, DECIMALS, get_account, get_contract
from scripts.deploy import deploy_gwin_protocol_and_gwin_token
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
    gwin_protocol, gwin_ERC20 = deploy_gwin_protocol_and_gwin_token()
    # Act
    price_feed_address = get_contract("eth_usd_price_feed")
    gwin_protocol.setPriceFeedContract(gwin_ERC20.address, get_contract("eth_usd_price_feed"), {"from": account})
    # Assert
    assert gwin_protocol.tokenPriceFeedMapping(gwin_ERC20.address) == price_feed_address
    with pytest.raises(exceptions.VirtualMachineError):
        gwin_protocol.setPriceFeedContract(
            gwin_ERC20.address, price_feed_address, {"from": non_owner}
        )

def test_stake_tokens(amount_staked):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20 = deploy_gwin_protocol_and_gwin_token()
    # Act
    gwin_ERC20.approve(gwin_protocol.address, amount_staked, {"from": account})
    gwin_protocol.stakeTokens(amount_staked, gwin_ERC20.address, {"from": account})
    # Assert
    assert gwin_protocol.stakingBalance(gwin_ERC20.address, account.address) == amount_staked
    assert gwin_protocol.uniqueTokensStaked(account.address) == 1
    assert gwin_protocol.stakers(0) == account.address
    return gwin_protocol, gwin_ERC20

def test_issue_tokens(amount_staked):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20 = test_stake_tokens(amount_staked)
    starting_balance = gwin_ERC20.balanceOf(account.address)
    # Act
    gwin_protocol.issueTokens({"from": account})
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
    gwin_protocol, gwin_ERC20 = test_stake_tokens(amount_staked)
    # Act
    gwin_protocol.addAllowedTokens(random_erc20.address, {"from": account})
    gwin_protocol.setPriceFeedContract(
        random_erc20.address, get_contract("eth_usd_price_feed"), {"from": account}
    )
    random_erc20_stake_amount = amount_staked * 2
    random_erc20.approve(
        gwin_protocol.address, random_erc20_stake_amount, {"from": account}
    )
    gwin_protocol.stakeTokens(
        random_erc20_stake_amount, random_erc20.address, {"from": account}
    )
    # Assert
    total_value = gwin_protocol.getUserTotalValue(account.address)
    assert total_value == INITIAL_PRICE_FEED_VALUE * 3

def test_can_get_token_value():
    account = get_account()
    gwin_protocol, gwin_ERC20 = deploy_gwin_protocol_and_gwin_token()
    assert gwin_protocol.getTokenValue(gwin_ERC20.address) == (
        INITIAL_PRICE_FEED_VALUE,
        DECIMALS,
    )

def test_can_deploy_ERC20():
    account = get_account()
    gwin_ERC20 = GwinToken.deploy({"from": account})
    assert gwin_ERC20

def test_can_add_allowed_token():
    account = get_account()
    gwin_protocol, gwin_ERC20 = deploy_gwin_protocol_and_gwin_token()
    gwin_protocol.addAllowedTokens(gwin_ERC20.address, {"from": account})
    assert gwin_protocol.allowedTokens(0) == gwin_ERC20.address

def test_only_owner_can_add_allowed_token():
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20 = deploy_gwin_protocol_and_gwin_token()
    with pytest.raises(exceptions.VirtualMachineError):
        gwin_protocol.addAllowedTokens(gwin_ERC20.address, {"from": non_owner})
    
def test_can_unstake_tokens(amount_staked):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    gwin_protocol, gwin_ERC20 = test_stake_tokens(amount_staked)
    gwin_protocol.unstakeTokens(gwin_ERC20.address, {"from": account})
    assert gwin_protocol.stakingBalance(gwin_ERC20.address, account) == 0
    assert gwin_protocol.uniqueTokensStaked(account.address) == 0

def test_token_is_allowed():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    # Act
    gwin_protocol, gwin_ERC20 = deploy_gwin_protocol_and_gwin_token()
    # Assert
    assert gwin_protocol.tokenIsAllowed(gwin_ERC20.address) == True

def test_return_addresses():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    # Act
    gwin_protocol, gwin_ERC20 = deploy_gwin_protocol_and_gwin_token()
    allowed_tokens = gwin_protocol.getAllowedTokenArray()
    # Assert
    assert allowed_tokens[0]
    assert allowed_tokens[-1] == allowed_tokens[2]