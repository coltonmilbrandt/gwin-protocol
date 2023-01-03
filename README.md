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

### Launch and Trade Markets with Any Price Feed!

Inspired by how the best DeFi projects work at small scale and large, Gwin allows you to launch a working market with just a price feed and then let that market grow organically as interest increases. The platform algorithmically ensures best performance available, even in markets with limited liquidity. This allows you to create and confidently trade in even the most obscure and growing markets, knowing that your trades will be executed at their best potential, without concerns about exit liquidity or costly exposure in a lopsided trade.

Want to learn more? Check out the [full documentation.](https://coltonmilbrandt.gitbook.io/gwin/)

## Prerequisites

Please install or have installed the following:

-   [nodejs v16.15.0](https://nodejs.org/en/download/)
-   [python](https://www.python.org/downloads/)
-   [Yarn](https://yarnpkg.com/cli/install)
    `npm install --global yarn`

## Installation

### Install Brownie, if you haven't already. Here is a simple way to install brownie.

```
python3 -m pip install --user pipx
python3 -m pipx ensurepath
# restart your terminal
pipx install eth-brownie
```

Or, if that doesn't work, via pip

```
pip install eth-brownie
Download the mix and install dependencies.
```

## Cloning the project

Use Git to clone the Gwin repository:

```
git clone https://github.com/coltonmilbrandt/gwin-protocol.git
cd gwin-protocol
```

## Local Development

For local testing install [ganache-cli](https://www.npmjs.com/package/ganache-cli)

```
npm install -g ganache-cli
```

or

```
yarn add global ganache-cli
```

All the scripts are designed to work locally or on a testnet.

## Running Scripts and Deployment

### Basic Deployment

This will deploy the Gwin smart contract to your local chain with ganache.

1. Compile the contract

```
brownie compile
```

2. Start ganache and take note of private keys as needed

```
ganache
```

3. Run deploy script with ganache network flag

```
brownie run scripts/deploy.py --network ganache
```

> Note: You may need to clear the build folder between deployments and testing, particulary when you restart ganache. You can safely delete the build folder so that the proper contract is referenced.

### Pool Deployment, Test with Metamask

This will deploy the Gwin smart contract with multiple pools to your local chain with ganache.

1. Compile the contract

```
brownie compile
```

2. Start ganache and take note of private keys

```
ganache
```

3. Run deploy script with ganache network flag and copy contract address from logs

```
brownie run scripts/deploy_pools.py --network ganache
```

copy the log output contract address for your newly deployed Gwin contract, for example...

```
gwin deployed to: 0xExAmpLe00c0nTr4ct00N0t00R34L00e3052d323a
```

copy any price feed addresses you'd like to use to create pools, for example...

```
deploying: eth_usd_price_feed
# ...
Deployed mock price feed to 0xExAmpLe00c0nTr4ct00N0t00R34L00e3052d323a
```

4. Clone and launch Front-End [right here](https://github.com/coltonmilbrandt/gwin-app.git)

5. Insert contract address of your local Gwin smart contract on ganache (from step 3) into the code for the front-end as described in the front end docs [here](https://github.com/coltonmilbrandt/gwin-app.git).

6. Copy the private key for Account (1), and use it to 'Import Account' on MetaMask.

7. Launch front-end with `yarn dev` and connect your MetaMask via Localhost 8545.
