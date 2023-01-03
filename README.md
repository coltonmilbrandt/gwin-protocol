           @@@@@@@@@@@@@@@                                        @@@@@@
        @@@@@@@@@@@@@@@@@@@@                                       @@@@
      @@@@@@,
     @@@@@@                      @@@          @@@          &@@%    %@@@      @@@@   @@@@@@@
     @@@@@                      *@@@@        @@@@@(       @@@@@    @@@@%     @@@@@@@@@@@@@@@@%
     @@@@@        @@@@@@@@@@     #@@@@      @@@@@@@      @@@@@     @@@@%     @@@@@       @@@@@
     @@@@@         @@@@@@@@@      &@@@@    @@@@ @@@@    %@@@@      @@@@%     @@@@*       #@@@@
     @@@@@@             @@@@       @@@@@  @@@@   @@@@  *@@@@       @@@@%     @@@@,       #@@@@
      @@@@@@            @@@@        @@@@@@@@@.    @@@@ @@@@        @@@@%     @@@@,       #@@@@
        @@@@@@@@@@&@@@@@@@@@         @@@@@@@%      @@@@@@@         @@@@%     @@@@,       #@@@@
           @@@@@@@@@@@@@@@@#          @@@@@@        @@@@@          @@@@.     @@@@         @@@@

# Gwin Protocol

### Launch and Trade Markets with Any Price Feed

Inspired by how the best DeFi projects work at small scale and large, Gwin allows you to launch a working market with just a price feed and then let that market grow organically as interest increases. The platform algorithmically ensures best performance available, even in markets with limited liquidity. This allows you to create and confidently trade in even the most obscure and growing markets, knowing that your transactions will be executed at their best potential, without concerns about exit liquidity or costly exposure in a lopsided trade.

Gwin has a great [front-end](https://github.com/coltonmilbrandt/gwin-app) that can be used along with this smart contract.

> Check out a [live deployment of the Gwin Dapp](https://gwin-app.vercel.app/) on the Goerli test net

### Want to learn more?

Check out the [full documentation.](https://coltonmilbrandt.gitbook.io/gwin/)

Look through [the FAQs](https://coltonmilbrandt.gitbook.io/gwin/faqs)

## Key Features

-   Launch markets quickly with any price feed
-   Trade efficiently in any market, even low-interest ones
-   Act as a market maker and earn profits by maintaining balance in the protocol
-   Avoid systemic risk with a unique approach to settlement and market making
-   Connect to the platform via a simple front end and MetaMask

## Sections

-   [Gwin Protocol](https://github.com/coltonmilbrandt/gwin-protocol#gwin-protocol)
    -   [Prerequisites](https://github.com/coltonmilbrandt/gwin-protocol#prerequisites)
    -   [Installation](https://github.com/coltonmilbrandt/gwin-protocol#installation)
    -   [Local Development](https://github.com/coltonmilbrandt/gwin-protocol#local-development)
    -   [Running Scripts and Deployment Locally](https://github.com/coltonmilbrandt/gwin-protocol#running-scripts-and-deployment-locally)
        -   [Basic Local Deployment](https://github.com/coltonmilbrandt/gwin-protocol#basic-local-deployment)
        -   [Local Pool Deployment with Front-End and Metamask](https://github.com/coltonmilbrandt/gwin-protocol#local-pool-deployment-with-front-end-and-metamask)
    -   [Running Scripts and Deployment on Goerli Test Net](https://github.com/coltonmilbrandt/gwin-protocol#running-scripts-and-deployment-on-goerli-test-net)
        -   [Basic Goerli Test Net Deployment](https://github.com/coltonmilbrandt/gwin-protocol#basic-goerli-test-net-deployment)
        -   [Goerli Test Net Pool Deployment with Front-End and Metamask](https://github.com/coltonmilbrandt/gwin-protocol#goerli-test-net-pool-deployment-with-front-end-and-metamask)
    -   [Testing with Ganache](https://github.com/coltonmilbrandt/gwin-protocol#testing-with-ganache)
        -   [Unit Tests](https://github.com/coltonmilbrandt/gwin-protocol#unit-tests)
        -   [Integration Tests](https://github.com/coltonmilbrandt/gwin-protocol#integration-tests)
        -   [Parent Pool Test](https://github.com/coltonmilbrandt/gwin-protocol#parent-pool-test)
    -   [Status](https://github.com/coltonmilbrandt/gwin-protocol#status)
    -   [Contributing](https://github.com/coltonmilbrandt/gwin-protocol#contributing)
    -   [Contact Me](https://github.com/coltonmilbrandt/gwin-protocol#contact-me)
    -   [Learn More About Gwin](https://github.com/coltonmilbrandt/gwin-protocol#learn-more-about-gwin)

## Prerequisites

Please install or have the following installed:

-   [nodejs v16.15.0](https://nodejs.org/en/download/)
-   [python](https://www.python.org/downloads/)
-   [Yarn](https://yarnpkg.com/cli/install)
    `npm install --global yarn`

## Installation

### Install Brownie, if you haven't already. Here is a simple way to install brownie.

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
# restart your terminal
pipx install eth-brownie
```

Or, if that doesn't work, try pip

```bash
pip install eth-brownie
Download the mix and install dependencies.
```

## Cloning the project

Use Git to clone the Gwin repository:

```bash
git clone https://github.com/coltonmilbrandt/gwin-protocol.git
cd gwin-protocol
```

## Local Development

For local testing install [ganache-cli](https://www.npmjs.com/package/ganache-cli)

```bash
npm install -g ganache-cli
```

or

```bash
yarn add global ganache-cli
```

All the scripts are designed to work locally or on a testnet.

## Running Scripts and Deployment Locally

### Basic Local Deployment

This will deploy the Gwin smart contract to your local chain with ganache.

1. Compile the contract

```bash
brownie compile
```

2. Start ganache and take note of private keys as needed

```bash
ganache
```

> Note: You may need to clear the build folder between deployments and testing, particulary when you restart ganache. You can safely delete the build folder so that the proper contract is referenced.

3. Run deploy script with ganache network flag

```bash
brownie run scripts/deploy.py --network ganache
```

### Local Pool Deployment with Front-End and Metamask

This will deploy the Gwin smart contract with multiple pools to your local chain with ganache and then allow you to trade.

> The deploy_pools.py script will repeatedly change the price feeds up in 1% increments to 10% higher than the original price and then down in 1% increments to 10% lower than the original price, changing multiple times per minute, so that you can experience price movements quickly and predictably. Eventually, the while loop doing this will terminate.

1. Compile the contract

```bash
brownie compile
```

2. Start ganache and take note of private keys

```bash
ganache
```

> Note: You may need to clear the build folder between deployments and testing, particulary when you restart ganache. You can safely delete the build folder so that the proper contract is referenced.

3. Run deploy script with ganache network flag and copy contract address from logs

```bash
brownie run scripts/deploy_pools.py --network ganache
```

Copy the log output contract address for your newly deployed Gwin contract, for example...

```bash
gwin deployed to: 0xExAmpLe00c0nTr4ct00N0t00R34L00e3052d323a
```

Copy any price feed addresses you'd like to use to create pools, for example...

```bash
deploying: eth_usd_price_feed
# ...
Deployed mock price feed to 0xExAmpLe00c0nTr4ct00N0t00R34L00e3052d323a
```

4. Clone and launch [front-end](https://github.com/coltonmilbrandt/gwin-app.git).

5. Insert contract address of your local Gwin smart contract on ganache (from step 3) into the code for the front-end as described in the [front end docs](https://github.com/coltonmilbrandt/gwin-app.git).

6. Copy the private key for Account (1), and use it to 'Import Account' on MetaMask. Accounts (1-3) are generally your best choice as Account (0) initially funds the pools and Account (4) updates the price feeds.

7. Launch front-end with `yarn dev` and connect your MetaMask via Localhost 8545.

8. Now you can Deposit and Withdraw to pools. To take advantage of the predictable price movement for testing, go long when ETH/USD is around $900 and withdraw, short, or go stable when ETH/USD is around $1,100 ([see how trading works](https://coltonmilbrandt.gitbook.io/gwin/features/trade)). Keep in mind that without market forces at work, it's easy to create interesting scenarios that otherwise wouldn't naturally arise with other traders participating and taking advantage of underweight (high health) pools. Read more about this in [the documentation](https://coltonmilbrandt.gitbook.io/gwin/technical-details/how-pools-are-settled). Also note that you can create pools as well. Read about that [right here](https://coltonmilbrandt.gitbook.io/gwin/technical-details/creating-a-new-market), just make sure that you use price feed addresses from the logs in Step 3.

## Running Scripts and Deployment on Goerli Test Net

### Basic Goerli Test Net Deployment

This will deploy the Gwin smart contract to Goerli.

1. Compile the contract

```bash
brownie compile
```

> Note: You may need to clear the build folder between deployments and testing, particulary when you change networks. You can safely delete the build folder so that the proper contract is referenced.

2. Run deploy script with goerli network flag

```bash
brownie run scripts/deploy.py --network goerli
```

After this, if you set it up properly for Etherscan, you can interact with the verified contract via their interface.

### Goerli Test Net Pool Deployment with Front-End and Metamask

This will deploy the Gwin smart contract with multiple pools to the Goerli Test Net and then allow you to trade. The deploy_pools.py script will create multiple pools to start you off.

1. Make sure you [grab some test net ETH](https://goerlifaucet.com/) if you need it.

2. Compile the contract

```bash
brownie compile
```

3. Set up your private key (use a test wallet!) and run deploy script with goerli network flag and copy contract address from logs.

> Note: You may need to clear the build folder between deployments and testing, particulary when you restart ganache or change networks. You can safely delete the build folder so that the proper contract is referenced.

> Note: Make sure you have enough test ETH. Change the amount in the deploy_pools.py script if needed, and make sure you have enough left for gas.

```bash
brownie run scripts/deploy_pools.py --network goerli
```

Copy the log output contract address for your newly deployed Gwin contract, for example...

```bash
gwin deployed to: 0xExAmpLe00c0nTr4ct00N0t00R34L00e3052d323a
```

Price feeds will be determined by the established Goerli addresses, so no need to worry about copying them. However, you can get the price feeds you need for creating pools on Goerli [here](https://docs.chain.link/data-feeds/price-feeds/addresses#Goerli%20Testnet).

4. Clone and launch [front-end](https://github.com/coltonmilbrandt/gwin-app.git).

5. Insert contract address of the Goerli Gwin smart contract (from step 3) into the code for the front-end as described in the [front end docs](https://github.com/coltonmilbrandt/gwin-app.git).

6. Launch front-end with `yarn dev` and connect your MetaMask wallet with the same keys that you used to deploy the contract (that way you can get your test ETH back, if you want).

7. Now you can Deposit and Withdraw to pools ([see how trading works](https://coltonmilbrandt.gitbook.io/gwin/features/trade)). Keep in mind that without market forces at work, it's easy to create interesting scenarios that otherwise wouldn't naturally arise with other traders participating and taking advantage of underweight (high health) pools. Read more about this in [the documentation](https://coltonmilbrandt.gitbook.io/gwin/technical-details/how-pools-are-settled). Also note that you can create pools as well. Read about that [right here](https://coltonmilbrandt.gitbook.io/gwin/technical-details/creating-a-new-market).

## Testing with Ganache

### Unit Tests

Unit tests include tests for:

-   Initializing a Pool
-   Basic Deposit
-   Basic Withdrawal
-   Deposit Exploit Guard
-   Liquidation
-   Getting Accounts
-   Balance Estimate Accuracy
-   Zero Amount Deposits
-   Withdrawal Greater than Balance
-   And More...

Run these tests with:

```
brownie test tests/unit/gwin_unit.py --network ganache
```

> Note: You may need to clear the build folder between deployments and testing, particulary when you restart ganache or change networks. You can safely delete the build folder so that the proper contract is referenced.

### Integration Tests

This broad integration test includes a robust script that compares the underlying math model's expected values with what the protocol calculates, verifying accuracy with extensive testing of a wide range of accumulating activity:

-   Initializing Pools
-   Varying Types of Pools
-   A Variety of Deposits
-   A Variety of Withdrawals

Run this test with:

```bash
brownie test tests/integration/gwin_int.py --network ganache
```

> Note: You may need to clear the build folder between deployments and testing, particulary when you restart ganache or change networks. You can safely delete the build folder so that the proper contract is referenced.

### Parent Pool Test

Like the previous broad integration test, but this script tests parent pool type transactions to verify accuracy with extensive testing of a wide range of accumulating activity:

-   Initializing Pools
-   A Variety of Deposits
-   A Variety of Withdrawals

Run this test with:

```bash
brownie test tests/integration/gwin_parent_int.py --network ganache
```

> Note: You may need to clear the build folder between deployments and testing, particulary when you restart ganache or change networks. You can safely delete the build folder so that the proper contract is referenced.

## Status

Gwin is currently in alpha and is undergoing active development. While it is functional, there may be some bugs and issues that have not yet been addressed.

The smart contracts for Gwin have not yet been formally audited and should not be used for main net applications at this time.

If you encounter any issues or have any questions about Gwin, please don't hesitate to [contact me](#contact-me).

## Contributing

We welcome contributions to Gwin! Here are a few ways you can help:

-   Report bugs and suggest features by opening an issue on GitHub.
-   Contribute code by opening a pull request on GitHub.
-   Help to improve the documentation by submitting updates and corrections.

## License

Gwin is licensed under the [MIT License](LICENSE).

# Contact Me

-   Have questions?
-   Need some help setting up?
-   Want to contribute?

### Email me at coltonmilbrandt@gmail.com!

### Check out my website [www.coltonmilbrandt.com](https://coltonmilbrandt.com/)

## Learn More About Gwin

Read the [full docs](https://coltonmilbrandt.gitbook.io/gwin/) to learn more.
