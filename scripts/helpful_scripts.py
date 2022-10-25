from brownie import (
    network,
    accounts,
    config,
    LinkToken,
    MockV3Aggregator,
    MockOracle,
    GwinProtocol,
    GwinToken,
    Contract,
    web3,
)
import time
import math
import pytest

NON_FORKED_LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["hardhat", "development", "ganache"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = NON_FORKED_LOCAL_BLOCKCHAIN_ENVIRONMENTS + [
    "mainnet-fork",
    "binance-fork",
    "matic-fork",
]

# Etherscan usually takes a few blocks to register the contract has been deployed
BLOCK_CONFIRMATIONS_FOR_VERIFICATION = (
    1 if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS else 6
)

contract_to_mock = {
    "link_token": LinkToken,
    "eth_usd_price_feed": MockV3Aggregator,
    "oracle": MockOracle,
}

DECIMALS = 18
INITIAL_VALUE = 1000_00000000
BASE_FEE = 100000000000000000  # The premium
GAS_PRICE_LINK = 1e9  # Some value calculated depending on the Layer 1 cost and Link
# TEMP??
KEPT_BALANCE = web3.toWei(100, "ether")


def is_verifiable_contract() -> bool:
    return config["networks"][network.show_active()].get("verify", False)


def get_account(index=None, id=None):
    if index:
        return accounts[index]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        return accounts[0]
    if id:
        return accounts.load(id)
    return accounts.add(config["wallets"]["from_key"])


def get_contract(contract_name):
    """If you want to use this function, go to the brownie config and add a new entry for
    the contract that you want to be able to 'get'. Then add an entry in the variable 'contract_to_mock'.
    You'll see examples like the 'link_token'.
        This script will then either:
            - Get a address from the config
            - Or deploy a mock to use for a network that doesn't have it
        Args:
            contract_name (string): This is the name that is referred to in the
            brownie config and 'contract_to_mock' variable.
        Returns:
            brownie.network.contract.ProjectContract: The most recently deployed
            Contract of the type specificed by the dictionary. This could be either
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
    ### Keep this line to show how it could be done without deploying a mock
    # tx = interface.LinkTokenInterface(link_token.address).transfer(
    #     contract_address, amount, {"from": account}
    # )
    tx = link_token.transfer(contract_address, amount, {"from": account})
    print("Funded {}".format(contract_address))
    return tx


def deploy_mocks(decimals=DECIMALS, initial_value=INITIAL_VALUE):
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
    
    # print("Deploying Mock VRFCoordinator...")
    # mock_vrf_coordinator = VRFCoordinatorV2Mock.deploy(
    #     BASE_FEE, GAS_PRICE_LINK, {"from": account}
    # )
    # print(f"Deployed to {mock_vrf_coordinator.address}")

    # print("Deploying Mock Oracle...")
    # mock_oracle = MockOracle.deploy(link_token.address, {"from": account})
    # print(f"Deployed to {mock_oracle.address}")

    # print("Deploying Mock Operator...")
    # mock_operator = MockOperator.deploy(link_token.address, account, {"from": account})
    # print(f"Deployed to {mock_operator.address}")

    print("Mocks Deployed!")


def listen_for_event(brownie_contract, event, timeout=200, poll_interval=2):
    """Listen for an event to be fired from a contract.
    We are waiting for the event to return, so this function is blocking.
    Args:
        brownie_contract ([brownie.network.contract.ProjectContract]):
        A brownie contract of some kind.
        event ([string]): The event you'd like to listen for.
        timeout (int, optional): The max amount in seconds you'd like to
        wait for that event to fire. Defaults to 200 seconds.
        poll_interval ([int]): How often to call your node to check for events.
        Defaults to 2 seconds.
    """
    web3_contract = web3.eth.contract(
        address=brownie_contract.address, abi=brownie_contract.abi
    )
    start_time = time.time()
    current_time = time.time()
    event_filter = web3_contract.events[event].createFilter(fromBlock="latest")
    while current_time - start_time < timeout:
        for event_response in event_filter.get_new_entries():
            if event in event_response.event:
                print("Found event!")
                return event_response
        time.sleep(poll_interval)
        current_time = time.time()
    print("Timeout reached, no event found.")
    return {"event": None}


def get_verify_status():
    verify = (
        config["networks"][network.show_active()]["verify"]
        if config["networks"][network.show_active()].get("verify")
        else False
    )
    return verify

# def transfer_tokens(token, amount):
#     tx = gwin_ERC20.transfer(gwin_protocol.address, gwin_ERC20.totalSupply() - KEPT_BALANCE, {"from": account})
#     tx.wait(1)

def deploy_mock_protocol_in_use():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    gwin_ERC20 = GwinToken.deploy({"from": account})
    gwin_protocol = GwinProtocol.deploy(
        gwin_ERC20.address, 
        get_contract("eth_usd_price_feed").address, 
        get_contract("link_token").address, 
        {"from": account}, 
        publish_source=config["networks"][network.show_active()]["verify"]
    )
    eth_usd_price_feed = get_contract("eth_usd_price_feed")
    eth_usd_price_feed.updateAnswer(1000_00000000, {"from": account})
    tx = gwin_ERC20.transfer(gwin_protocol.address, gwin_ERC20.totalSupply() - KEPT_BALANCE, {"from": account})
    tx.wait(1)
    non_owner = get_account(index=1) # Alice
    non_owner_two = get_account(index=2) # Bob
    non_owner_three = get_account(index=3) # Chris
    non_owner_four = get_account(index=4) # Dan
    tx = gwin_protocol.initializeProtocol({"from": account, "value": web3.toWei(20, "ether")})
    tx.wait(1)

    ################### tx1 ###################
    eth_usd_price_feed.updateAnswer(1200_00000000, {"from": account})
    #                                     isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txOne = gwin_protocol.depositToTranche(True, False, web3.toWei(1, "ether"), 0, {"from": non_owner, "value": web3.toWei(1, "ether")})
    txOne.wait(1)

    ################### tx2 ###################
    eth_usd_price_feed.updateAnswer(1400_00000000, {"from": account})
    #              DEPOSIT              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txTwo = gwin_protocol.depositToTranche(False, True, 0, web3.toWei(1, "ether"), {"from": non_owner_two, "value": web3.toWei(1, "ether")})
    txTwo.wait(1)
    ################### tx3 ###################
    eth_usd_price_feed.updateAnswer(1300_00000000, {"from": account})
    #              WITHDRAWAL              isCooled, isHeated, cAmount, hAmount {from, msg.value}
    txThree = gwin_protocol.withdrawFromTranche(True, False, 0, 0, True, {"from": non_owner})
    txThree.wait(1)

    return gwin_protocol, gwin_ERC20, eth_usd_price_feed

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