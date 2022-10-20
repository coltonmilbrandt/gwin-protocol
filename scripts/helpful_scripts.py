from brownie import (
    network,
    accounts,
    config,
    interface,
    LinkToken,
    MockV3Aggregator,
    MockWETH,
    MockDAI,
    Contract,
)
from web3 import Web3
import pytest
import math
from brownie import GwinToken, GwinProtocol
# eth_utils needs to be installed "pip3 install eth_utils"
import eth_utils

INITIAL_PRICE_FEED_VALUE = 2000_000000000000000000
DECIMALS = 18
KEPT_BALANCE = Web3.toWei(100, "ether")

NON_FORKED_LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["hardhat", "development", "ganache"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = NON_FORKED_LOCAL_BLOCKCHAIN_ENVIRONMENTS + [
    "mainnet-fork",
    "binance-fork",
    "matic-fork",
]

contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "dai_usd_price_feed": MockV3Aggregator,
    "fau_token": MockDAI,
    "weth_token": MockWETH,
}

def get_account(index=None, id=None):
    if index:
        return accounts[index]
    # if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS or network.show_active() in FORKED_LOCAL_ENVIRONMENTS:
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:    
        return accounts[0]
    if id:
        return accounts.load(id)
    return accounts.add(config["wallets"]["from_key"])

def rounded(val):
    val = val / 100000000
    val = int(val)
    return val

def short_round(val):
    val = val / 10000000000000000
    val = int(val)
    return val

def extra_rounded(val):
    val = val / 100000000000
    val = round_up(val)
    val = int(val)
    return val

def rnd(val):
    val = val / 10
    val = int(val)
    val = val / 100
    val = round_up(val)
    val = val * 1000
    val = int(val)
    return val

def roundedDec(val):
    val = val / 10
    val = round_up(val)
    val = val * 10
    val = int(val)
    return val

def round_up(n, decimals=0):
    multiplier = 10 ** decimals
    return math.ceil(n * multiplier) / multiplier

# *args allows for any number of arguments afterward
def encode_function_data(initializer=None, *args):
    """Encodes the function call so we can work with an initializer

    Args:
        initializer ([brownie.network.contract.ContractTx], optional):
        The initializer function we want to call. Example: 'box.store'.
        Defaults to None.

        args (Any, options):
        The arguments to pass to the inititalizer function

        Returns:
        [bytes]: Return the encoded bytes.
    
    """
    #  we are encoding "initializer=box.store, 1" into bytes so that our smart contracts know
    #  which function to call. If there is no initializer or it's blank, we return an empty hex
    #  string and our smart contract will know it is blank.
    if len(args) == 0 or not initializer:
        return eth_utils.to_bytes(hexstr="0x")
    return initializer.encode_input(*args)

# This function covers all the different way you might call an upgrade to your smart contract
def upgrade(
    account, 
    proxy, # This is the proxy contract, it directs the actions to the right contract
    new_implementation_address, # This is the new implementation
    proxy_admin_contract=None, # If there is an admin contract
    initializer=None, # like box.store
    *args # this could be many arguments, or it could be none
):
    # Checks for a proxy contract
    if proxy_admin_contract:
        # Checks for an initializer
        if initializer:
            # Encode the function data
            encoded_function_call = encode_function_data(initializer, *args)
            # Takes the proxy_admin_contract and uses the proxyAdmin.sol to call upgrade
            transaction = proxy_admin_contract.upgradeAndCall(
                proxy.address,
                new_implementation_address,
                encoded_function_call,
                {"from": account}
            )
        # If they don't have an initializer, we don't need to encode a function call
        else:
            # This simply upgrades it, but doesn't call
            transaction = proxy_admin_contract.upgrade(
                proxy.address, new_implementation_address, {"from": account}
            )
    # If it doesn't have a proxy admin
    else:
        # Check for an inititializer
        if initializer:
            # If there is an initializer, then we have to encode that function call
            encoded_function_call = encode_function_data(initializer, *args)
            # This is without the proxy_admin
            transaction = proxy.upgradeToAndCall(
                new_implementation_address, encoded_function_call, {"from":account}
            )
        # No proxy_admin and no initializer to encode a function call for
        else: 
            transaction = proxy.upgradeTo(new_implementation_address, {"from": account})
    return transaction

def get_contract(contract_name):
    """If you want to use this function, go to the brownie config and add a new entry for
    the contract that you want to be able to 'get'. Then add an entry in the in the variable 'contract_to_mock'.
    You'll see examples like the 'link_token'.
        This script will then either:
            - Get a address from the config
            - Or deploy a mock to use for a network that doesn't have it
        Args:
            contract_name (string): This is the name that is refered to in the
            brownie config and 'contract_to_mock' variable.
        Returns:
            brownie.network.contract.ProjectContract: The most recently deployed
            Contract of the type specificed by the dictonary. This could be either
            a mock or the 'real' contract on a live network.
    """
    contract_type = contract_to_mock[contract_name]
    if network.show_active() in NON_FORKED_LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        if len(contract_type) <= 0:
            deploy_mocks()
        contract = contract_type[-1]
    else:
        try:
            contract_address = config["networks"][network.show_active()][contract_name]
            contract = Contract.from_abi(
                contract_type._name, contract_address, contract_type.abi
            )
        except KeyError:
            print(
                f"{network.show_active()} address not found, perhaps you should add it to the config or deploy mocks?"
            )
            print(
                f"brownie run scripts/deploy_mocks.py --network {network.show_active()}"
            )
    return contract


def fund_with_link(
    contract_address, account=None, link_token=None, amount=1000000000000000000
):
    account = account if account else get_account()
    link_token = link_token if link_token else get_contract("link_token")
    tx = interface.LinkTokenInterface(link_token).transfer(
        contract_address, amount, {"from": account}
    )
    print("Funded {}".format(contract_address))
    return tx


def get_verify_status():
    verify = (
        config["networks"][network.show_active()]["verify"]
        if config["networks"][network.show_active()].get("verify")
        else False
    )
    return verify

def deploy_mocks(decimals=DECIMALS, initial_value=INITIAL_PRICE_FEED_VALUE):
    """
    Use this script if you want to deploy mocks to a testnet
    """
    print(f"The active network is {network.show_active()}")
    print("Deploying Mocks...")
    account = get_account()
    print("Deploying Mock Link Token...")
    link_token = LinkToken.deploy({"from": account})
    print("Deploying Mock Price Feed...")
    mock_price_feed = MockV3Aggregator.deploy(
        decimals, initial_value, {"from": account}
    )
    print(f"Deployed to {mock_price_feed.address}")
    print("Deploying Mock DAI...")
    dai_token = MockDAI.deploy({"from": account})
    print(f"Deployed to {dai_token.address}")
    print("Deploying Mock WETH")
    weth_token = MockWETH.deploy({"from": account})
    print(f"Deployed to {weth_token.address}")

# def transfer_tokens(token, amount):
#     tx = gwin_ERC20.transfer(gwin_protocol.address, gwin_ERC20.totalSupply() - KEPT_BALANCE, {"from": account})
#     tx.wait(1)

def deploy_mock_protocol_in_use():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    gwin_ERC20 = GwinToken.deploy({"from": account})
    gwin_protocol = GwinProtocol.deploy(gwin_ERC20.address, {"from": account}, publish_source=config["networks"][network.show_active()]["verify"])
    tx = gwin_ERC20.transfer(gwin_protocol.address, gwin_ERC20.totalSupply() - KEPT_BALANCE, {"from": account})
    tx.wait(1)
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    tx = gwin_protocol.initializeProtocol({"from": account, "value": Web3.toWei(20, "ether")})
    tx.wait(1)

    ################### tx1 ###################
    gwin_protocol.changeCurrentEthUsd(1200, {"from": account})
    #                                     isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txOne = gwin_protocol.depositToTranche(True, False, Web3.toWei(1, "ether"), 0, {"from": non_owner, "value": Web3.toWei(1, "ether")})
    txOne.wait(1)

    ################### tx2 ###################
    gwin_protocol.changeCurrentEthUsd(1400, {"from": account})
    #              DEPOSIT              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txTwo = gwin_protocol.depositToTranche(False, True, 0, Web3.toWei(1, "ether"), {"from": non_owner_two, "value": Web3.toWei(1, "ether")})
    txTwo.wait(1)
    ################### tx3 ###################
    gwin_protocol.changeCurrentEthUsd(1300, {"from": account})
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txThree = gwin_protocol.withdrawFromTranche(True, False, 0, 0, True, {"from": non_owner})
    txThree.wait(1)

    return gwin_protocol, gwin_ERC20