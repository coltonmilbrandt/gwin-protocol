// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract GwinProtocol is Ownable {
    // // token address -> staker address -> amount
    // mapping(address => mapping(address => uint256)) public stakingBalance;
    // // staker address -> unique tokens staked
    // mapping(address => uint256) public uniqueTokensStaked;
    // // token address -> token price feed address
    // mapping(address => address) public tokenPriceFeedMapping;
    // // array of stakers
    // address[] public stakers;
    // // array of the allowed tokens
    // address[] public allowedTokens;
    uint256 lastSettledEthUsd;
    uint32 bp = 10000;
    // TEMP simulated balance
    uint256 cEthBal = 10;
    // TEMP simulated balance
    uint256 hEthBal = 10;

    // Storing the GWIN token as a global variable, IERC20 imported above, address passed into constructor
    IERC20 public gwinToken;

    // Right when we deploy this contract, we need to know the address of GWIN token
    constructor(address _gwinTokenAddress) public {
        // we pass in the address from the GwinToken.sol contract
        gwinToken = IERC20(_gwinTokenAddress);
    }

    // get Cooled ETH balance
    // get Heated ETH balance
    // get ETH/USD price

    function tempGetPrices() public {
        lastEthUsd = 1000;
        currentEthUsd = 1100;
    }

    function getProfit(uint256 _ethUSd) public view returns (uint256) {
        uint256 profit = ((_ethUSd - lastSettledEthUsd) * bps) /
            lastSettledEthUsd;
        return profit;
    }

    // TEMP returns current ETH/USD
    function getCurrentEthUsd() public returns (uint256) {
        return 1100;
    }

    // make modular function that does calculations that both tranches need
    function trancheSpecificCalcs(
        bool _isCooled,
        uint256 _ethUsdProfit,
        uint256 _currentEthUsd
    ) public returns (uint256) {
        if (_isCooled == true) {
            uint256 trancheBal = cEthBal;
            uint256 r = -0.5;
        } else {
            uint256 trancheBal = hEthBal;
            uint256 r = 0.5;
        }
        uint256 trancheChange = (trancheBal * _currentEthUsd) -
            (trancheBal * lastSettledEthUsd);
        uint256 expectedPayout = trancheChange * (1 + r);
        uint256 allocationDifference = expectedPayout - trancheChange;
        return allocationDifference;
    }

    // Interact: cEthBal, hEthBal, cEthUsdBal, hEthUsdBal, tranche, lastEthUsd, currentEthUsd
    function interact(bool _isCooled) public {
        uint256 currentEthUsd = getCurrentEthUsd();
        uint256 ethUsdProfit = getProfit(currentEthUsd);
        uint256 cooledAllocationDiff = trancheSpecificCalcs(
            true,
            ethUsdProfit,
            currentEthUsd
        );
        uint256 heatedAllocationDiff = trancheSpecificCalcs(
            false,
            ethUsdProfit,
            currentEthUsd
        );
        // calculate out min
        // both tranche are needed for the diff
        uint256 absHeatedAllocationDiff = abs(heatedAllocationDiff);
        uint256 absCooledAllocationDiff = abs(cooledAllocationDiff);
        uint256 minAbsAllocation = absCooledAllocationDiff >
            absHeatedAllocationDiff
            ? absHeatedAllocationDiff
            : absCooledAllocationDiff;
        uint256 nonNaturalDifference = absHeatedAllocationDiff +
            absCooledAllocationDiff;
        uint256 percentCooledTranche = (cEthBal * bps) / (cEthBal + hEthBal);
        uint256 nonNaturalMultiplier = ethUsdProfit > 0
            ? percentCooledTranche
            : (1 - percentCooledTranche);
        uint256 adjNonNaturalDiff = abs(nonNaturalDifference) *
            nonNaturalMultiplier;
    }

    function abs(uint x) private pure returns (int) {
        return x >= 0 ? x : -x;
    }

    // Pass in: address, tranche, amount, hotColdRatio, priceChange
}
