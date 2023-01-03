from brownie import GwinProtocol, GwinToken, network, exceptions, config, web3
from pyparsing import null_debug_action
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, INITIAL_VALUE, DECIMALS, get_account, get_contract, rounded, roundedDec, extra_rounded, rnd
from scripts.deploy import deploy_gwin_protocol_and_gwin_token
from web3 import Web3
import time

# NOTE: If you start a new instance of Ganache etc., be sure to delete the previous deployments in the build folder

def main():
    # 'amount' determined by environment - i.e. the ETH you wish to distribute between all the pools
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        amount = 100
    else:
        amount = 0.6
    
    account = get_account() # Protocol 
    non_owner = get_account(index=4)
    gwin_protocol, gwin_ERC20, eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed = deploy_gwin_protocol_and_gwin_token()

    #@@@@@@@@@@@@| Create 2x ETH/USD pool with stable parent |@@@@@@@@@@@@#
    parent_id = 1 # parent ID: 1
    pool_type = 0 # classic type pool
    pool_h_rate = 100_0000000000 # 2x leverage
    pool_c_rate = -100_0000000000 # stable
    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x4554482f555344", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(amount, "ether")})
    tx.wait(1)
    pool_2x_id = 0

    #@@@@@@@@@@@@| Create 5x ETH/USD pool with stable parent |@@@@@@@@@@@@#
    pool_type = 0 # classic type pool | parent ID: 1
    pool_h_rate = 400_0000000000 # 5x leverage
    pool_c_rate = -100_0000000000 # stable
    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x4554482f555344", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(amount, "ether")})
    tx.wait(1)
    pool_5x_id = 1

    #@@@@@@@@@@@@| Create 10x ETH/USD pool with stable parent |@@@@@@@@@@@@#
    pool_type = 0 # classic type pool | parent ID: 1
    pool_h_rate = 900_0000000000 # 10x leverage
    pool_c_rate = -100_0000000000 # stable
    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x4554482f555344", "0x0000000000000000000000000000000000000000", "0x0", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(amount, "ether")})
    tx.wait(1)
    pool_10x_id = 2

    #@@@@@@@@@@@@| Create 2x long XAU / stable XAU pool |@@@@@@@@@@@@#
    pool_type = 1 # modified type pool
    parent_id = 0 # no parent pool
    pool_h_rate = 100_0000000000 # 2x leverage
    pool_c_rate = -100_0000000000 # stable
    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x4554482f555344", xau_usd_price_feed.address, "0x5841552f555344", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(amount, "ether")})
    tx.wait(1)
    pool_XAU_id = 3

    #@@@@@@@@@@@@| Create 2x long BTC / stable BTC pool |@@@@@@@@@@@@#
    pool_type = 1 # modified type pool
    parent_id = 0 # no parent pool
    pool_h_rate = 100_0000000000 # 2x leverage
    pool_c_rate = -100_0000000000 # stable
    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x4554482f555344", btc_usd_price_feed.address, "0x4254432f555344", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(amount, "ether")})
    tx.wait(1)
    pool_BTC_id = 4

    #@@@@@@@@@@@@| Create 2x long BTC / stable BTC pool |@@@@@@@@@@@@#
    pool_type = 1 # modified type pool
    parent_id = 0 # no parent pool
    pool_h_rate = 100_0000000000 # 2x leverage
    pool_c_rate = -100_0000000000 # stable
    tx = gwin_protocol.initializePool(pool_type, parent_id, eth_usd_price_feed.address, "0x4554482f555344", jpy_usd_price_feed.address, "0x4a50592f555344", pool_c_rate, pool_h_rate, {"from": account, "value": Web3.toWei(amount, "ether")})
    tx.wait(1)
    pool_JPY_id = 5

    # Print contract address
    print(f"gwin deployed to: " + gwin_protocol.address)

    # list of pool IDs
    pool_ids = [pool_10x_id, pool_XAU_id, pool_BTC_id, pool_JPY_id]
    # list of price feed instances
    price_feeds = [eth_usd_price_feed, xau_usd_price_feed, btc_usd_price_feed, jpy_usd_price_feed]

    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        updatePriceFeeds(account, non_owner, pool_ids, gwin_protocol, price_feeds)
    
        
def updatePriceFeeds(account, non_owner, pool_ids, gwin_protocol, price_feeds):
    direction = "up"
    count = 10
    amount = None
    while True:
        if count % 20 == 0:
            if direction == "down":
                direction = "up"
            else:
                direction = "down"
        if direction == "down":
            amount = -10_00000000
        else:
            amount = 10_00000000
        # retrieve the current price for the pool
        price = price_feeds[0].latestRoundData()
        # adjust the price based on the percentage change
        adj_price = price[1] + amount
        # update the price feed for the pool
        price_feeds[0].updateAnswer(adj_price, {"from": non_owner})
        print(f"New price is: ")
        print(f"Price feed address: " + str(price_feeds[0]))
        print(adj_price)
        count += 1
        # exit the loop when the block number reaches 100
        if count == 1000:
            break
        # pause the script for 20 seconds
        time.sleep(20)