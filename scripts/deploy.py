from abc import abstractclassmethod
from brownie import GwinToken, GwinProtocol, network, config
from scripts.helpful_scripts import deploy_mocks, get_account, get_contract, fund_with_link, LOCAL_BLOCKCHAIN_ENVIRONMENTS, TEST_BLOCKCHAIN_ENVIRONMENTS, NON_FORKED_LOCAL_BLOCKCHAIN_ENVIRONMENTS
from web3 import Web3

# NOTE: The build folder must be deleted when new chain is initialized
# this is temporary, easy to work around, and will be fixed when there is time

KEPT_BALANCE = Web3.toWei(100, "ether")

def deploy_gwin_protocol_and_gwin_token():
    print('Getting account...')
    account = get_account()
    print(f'account is: ' + account.address)
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
    eth_usd_price_feed = get_contract("eth_usd_price_feed")
    xau_usd_price_feed = get_contract("xau_usd_price_feed")
    btc_usd_price_feed = get_contract("btc_usd_price_feed")
    jpy_usd_price_feed = get_contract("jpy_usd_price_feed")
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        eth_usd_price_feed.updateAnswer(1000_00000000, {"from": account})
        xau_usd_price_feed.updateAnswer(Web3.toWei(1600, "ether"), {"from": account})
    tx1 = gwin_ERC20.transfer(gwin_protocol.address, gwin_ERC20.totalSupply() - KEPT_BALANCE, {"from": account})
    tx1.wait(1)

    # NOTE: IMPORTANT!! Change to True to deploy pools to network, change to False if running testing scripts
    
    ##@@@@@   SET THIS VARIABLE   @@@@@###
    # True - deploys pools for sandbox type testing
    # False - deploys only contract for testing scripts
    deploy_pools = False
    ##@@@@@   SET THIS VARIABLE   @@@@@###

    if deploy_pools == True:
        # Deploy initial pools for sandbox type testing

        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\  ETH/USD 2x Long Stable Pool (-100, 200)  /@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#
        pool_id = 0
        parent_id = 1
        pool_type = 0 # classic type pool
        pool_h_rate = 100_0000000000 # 2x leverage
        pool_c_rate = -100_0000000000 # stable
        print("initializing ETH 2x...")
        tx2 = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(0.1, "ether")})
        tx2.wait(1)

        print(f"eth USD price feed: " + eth_usd_price_feed.address)
        hEth_bal, cEth_bal = gwin_protocol.previewPoolBalances.call(pool_id)
        pool_id = pool_id + 1
        print("hEth Bal: ")
        print(hEth_bal)
        print("cEth Bal: ")
        print(cEth_bal)
        print("parentID: ")
        print(parent_id)
        print("type: ")
        print(pool_type)
        contract_name = "eth_usd_price_feed"
        print(f"Goerli Price Feed Address 1: " + config["networks"]["goerli"][contract_name])

        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\  ETH/USD 5x Long Stable Pool (-100, 400)  /@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#

        pool_type = 0 # classic type pool
        pool_h_rate = 400_0000000000 # 5x leverage
        pool_c_rate = -100_0000000000 # stable

        print("initializing ETH 5x...")
        tx3 = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(0.1, "ether")})
        tx3.wait(1)
        print(f"eth USD price feed: " + eth_usd_price_feed.address)
        hEth_bal, cEth_bal = gwin_protocol.previewPoolBalances.call(pool_id)
        pool_id = pool_id + 1
        print("hEth Bal: ")
        print(hEth_bal)
        print("cEth Bal: ")
        print(cEth_bal)
        print("parentID: ")
        print(parent_id)
        print("type: ")
        print(pool_type)
        contract_name = "eth_usd_price_feed"
        print(f"Goerli Price Feed Address 1: " + config["networks"]["goerli"][contract_name])

        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\  ETH/USD 10x Long Stable Pool (-100, 900)  /@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#

        pool_type = 0 # classic type pool
        pool_h_rate = 900_0000000000 # 10x leverage
        pool_c_rate = -100_0000000000 # stable

        print("initializing ETH 10x...")
        tx4 = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x455448", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(0.1, "ether")})
        tx4.wait(1)
        print(f"eth USD price feed: " + eth_usd_price_feed.address)
        hEth_bal, cEth_bal = gwin_protocol.previewPoolBalances.call(pool_id)
        pool_id = pool_id + 1
        print("hEth Bal: ")
        print(hEth_bal)
        print("cEth Bal: ")
        print(cEth_bal)
        print("parentID: ")
        print(parent_id)
        print("type: ")
        print(pool_type)
        contract_name = "eth_usd_price_feed"
        print(f"Goerli Price Feed Address 1: " + config["networks"]["goerli"][contract_name])

        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\  ETH/XAU Short Stable (-100, 100)  /@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#

        parent_id = 0
        #                                                           "ETH/USD"                               "XAU/USD"
        print("initializing ETH/XAU Short Stable...")
        tx5 = gwin_protocol.initializePool(1, parent_id, eth_usd_price_feed.address, "0x455448", xau_usd_price_feed.address, "0x584155", -100_0000000000, 100_0000000000, {"from": account, "value": Web3.toWei(0.1, "ether")})
        tx5.wait(1)
        print(f"eth USD price feed: " + eth_usd_price_feed.address)
        print(f"XAU USD price feed: " + xau_usd_price_feed.address)
        hEth_bal, cEth_bal = gwin_protocol.previewPoolBalances.call(pool_id)
        pool_id = pool_id + 1
        print("hEth Bal: ")
        print(hEth_bal)
        print("cEth Bal: ")
        print(cEth_bal)
        print("parentID: ")
        print(parent_id)
        contract_name = "eth_usd_price_feed"
        print(f"Goerli Price Feed Address 1: " + config["networks"]["goerli"][contract_name])
        contract_two_name = "xau_usd_price_feed"
        print(f"Goerli Price Feed Address 2: " + config["networks"]["goerli"][contract_two_name])

        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\  ETH/XAU Long Short (-200, 400)  /@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#
        
        parent_id = 0
        #                                                           "ETH/USD"                               "XAU/USD"
        print("initializing ETH/XAU Long Short...")
        tx6 = gwin_protocol.initializePool(1, parent_id, eth_usd_price_feed.address, "0x455448", xau_usd_price_feed.address, "0x584155", -200_0000000000, 400_0000000000, {"from": account, "value": Web3.toWei(0.1, "ether")})
        tx6.wait(1)
        print(f"eth USD price feed: " + eth_usd_price_feed.address)
        print(f"XAU USD price feed: " + xau_usd_price_feed.address)
        hEth_bal, cEth_bal = gwin_protocol.previewPoolBalances.call(pool_id)
        pool_id = pool_id + 1
        print("hEth Bal: ")
        print(hEth_bal)
        print("cEth Bal: ")
        print(cEth_bal)
        print("parentID: ")
        print(parent_id)
        contract_name = "eth_usd_price_feed"
        print(f"Goerli Price Feed Address 1: " + config["networks"]["goerli"][contract_name])
        contract_two_name = "xau_usd_price_feed"
        print(f"Goerli Price Feed Address 2: " + config["networks"]["goerli"][contract_two_name])

        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\  ETH/BTC Short Stable (-100, 100)  /@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#

        parent_id = 0
        #                                                           "ETH/USD"                               "BTC/USD"
        print("initializing ETH/BTC Short Stable...")
        tx7 = gwin_protocol.initializePool(1, parent_id, eth_usd_price_feed.address, "0x455448", btc_usd_price_feed.address, "0x4254432f555344", -100_0000000000, 100_0000000000, {"from": account, "value": Web3.toWei(0.1, "ether")})
        tx7.wait(1)
        print(f"eth USD price feed: " + eth_usd_price_feed.address)
        print(f"BTC USD price feed: " + btc_usd_price_feed.address)
        hEth_bal, cEth_bal = gwin_protocol.previewPoolBalances.call(pool_id)
        pool_id = pool_id + 1
        print("hEth Bal: ")
        print(hEth_bal)
        print("cEth Bal: ")
        print(cEth_bal)
        print("parentID: ")
        print(parent_id)
        contract_name = "eth_usd_price_feed"
        print(f"Goerli Price Feed Address 1: " + config["networks"]["goerli"][contract_name])
        contract_two_name = "btc_usd_price_feed"
        print(f"Goerli Price Feed Address 2: " + config["networks"]["goerli"][contract_two_name])

        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\  ETH/JPY Long Short (-200, 400)  /@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#
        
        parent_id = 0
        #                                                           "ETH/USD"                               "JPY/USD"
        print("initializing ETH/JPY Long Short...")
        tx8 = gwin_protocol.initializePool(1, parent_id, eth_usd_price_feed.address, "0x455448", jpy_usd_price_feed.address, "0x4a50592f555344", -200_0000000000, 400_0000000000, {"from": account, "value": Web3.toWei(0.1, "ether")})
        tx8.wait(1)
        print(f"eth USD price feed: " + eth_usd_price_feed.address)
        print(f"JPY USD price feed: " + jpy_usd_price_feed.address)
        hEth_bal, cEth_bal = gwin_protocol.previewPoolBalances.call(pool_id)
        print("hEth Bal: ")
        print(hEth_bal)
        print("cEth Bal: ")
        print(cEth_bal)
        print("parentID: ")
        print(parent_id)
        hEth_bal_settled = gwin_protocol.retrieveProtocolHEthBalance.call(pool_id)
        cEth_bal_settled = gwin_protocol.retrieveProtocolCEthBalance.call(pool_id)
        print("settled hEth Bal: ")
        print(hEth_bal_settled)
        print("settled cEth Bal: ")
        print(cEth_bal_settled)
        contract_name = "eth_usd_price_feed"
        print(f"Goerli Price Feed Address 1: " + config["networks"]["goerli"][contract_name])
        contract_two_name = "jpy_usd_price_feed"
        print(f"Goerli Price Feed Address 2: " + config["networks"]["goerli"][contract_two_name])
        pool_id = pool_id + 1

    return gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed

def main():
    deploy_gwin_protocol_and_gwin_token()
