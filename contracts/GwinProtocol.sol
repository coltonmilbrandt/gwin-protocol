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

    // TEMP temporary value for testing
    uint256 decimals = 10**18;
    uint256 usdDecimals = 10**8;
    uint256 lastSettledEthUsd = 1000 * usdDecimals;
    uint256 bps = 10**4;
    // TEMP simulated balance
    uint256 cEthBal = 10 * decimals;
    // TEMP simulated balance
    uint256 hEthBal = 10 * decimals;

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

    function getProfit(uint256 _ethUsd) public view returns (int256) {
        int256 profit = ((int(_ethUsd) - int(lastSettledEthUsd)) * int(bps)) /
            int(lastSettledEthUsd);
        return profit;
    }

    // TEMP returns current ETH/USD
    function getCurrentEthUsd() public returns (uint256) {
        return 1100 * usdDecimals;
    }

    // make modular function that does calculations that both tranches need
    function trancheSpecificCalcs(
        bool _isCooled,
        int256 _ethUsdProfit,
        uint256 _currentEthUsd
    ) private returns (int256) {
        require(
            cEthBal > 0 && hEthBal > 0, // in Wei
            "Protocol must have funds in order to settle."
        );
        uint256 trancheBal;
        int256 r;
        if (_isCooled == true) {
            trancheBal = cEthBal; // in Wei
            r = -5000; // basis points
        } else {
            trancheBal = hEthBal; // in Wei
            r = 5000; // basis points
        }
        require(trancheBal > 0, "Tranche must have a balance.");
        require(
            r == -5000 || r == 5000,
            "Tranche must have a valid multiplier value."
        );
        int256 trancheChange = (int(trancheBal) * int(_currentEthUsd)) -
            (int(trancheBal) * int(lastSettledEthUsd));
        int256 expectedPayout = (trancheChange * ((1 * int(bps)) + r)) /
            int(bps);
        int256 allocationDifference = expectedPayout - trancheChange;
        allocationDifference = allocationDifference / int(decimals);
        return allocationDifference;
    }

    function deposit() public {
        interact();
    }

    // Interact: cEthBal, hEthBal, cEthUsdBal, hEthUsdBal, tranche, lastEthUsd, currentEthUsd
    function interact() public returns (int256) {
        uint256 currentEthUsd = getCurrentEthUsd();
        int256 ethUsdProfit = getProfit(currentEthUsd); // returns ETH/USD profit in terms of basis points // 1000
        int256 cooledAllocationDiff = trancheSpecificCalcs(
            true,
            ethUsdProfit,
            currentEthUsd
        );
        int256 heatedAllocationDiff = trancheSpecificCalcs(
            false,
            ethUsdProfit,
            currentEthUsd
        );
        uint256 absAllocationTotal;
        {
            // to avoid stack too deep error
            int256 absHeatedAllocationDiff = abs(heatedAllocationDiff);
            int256 absCooledAllocationDiff = abs(cooledAllocationDiff);
            int256 minAbsAllocation = absCooledAllocationDiff >
                absHeatedAllocationDiff
                ? absHeatedAllocationDiff
                : absCooledAllocationDiff;
            int256 nonNaturalDifference = heatedAllocationDiff +
                cooledAllocationDiff;
            uint256 percentCooledTranche = ((cEthBal * bps) /
                (cEthBal + hEthBal));
            uint256 nonNaturalMultiplier = ethUsdProfit > 0
                ? percentCooledTranche
                : ((1 * bps) - percentCooledTranche);
            uint256 adjNonNaturalDiff = uint(abs(nonNaturalDifference)) *
                nonNaturalMultiplier;
            absAllocationTotal = uint(minAbsAllocation) + adjNonNaturalDiff;
        }
        int256 cooledAllocation;
        int256 heatedAllocation;
        if (cooledAllocationDiff < 0) {
            if ((cEthBal * currentEthUsd) - absAllocationTotal > 0) {
                cooledAllocation = -int(absAllocationTotal);
            } else {
                cooledAllocation = int(cEthBal * currentEthUsd);
            }
        } else {
            if ((hEthBal * currentEthUsd) - absAllocationTotal > 0) {
                cooledAllocation = int(absAllocationTotal);
            } else {
                cooledAllocation = int(hEthBal * currentEthUsd);
            }
        }
        heatedAllocation = -cooledAllocation; // USD allocation in usdDecimal terms
        uint256 totalLockedUsd = ((cEthBal + hEthBal) * currentEthUsd) / // USD balance in usdDecimal terms
            decimals;
        int256 cooledBalAfterAllocation = int(totalLockedUsd) - // USD cooled balance in usdDecimal terms
            (int((cEthBal * currentEthUsd)) / int(decimals)) +
            cooledAllocation;
        int256 heatedBalAfterAllocation = int(totalLockedUsd) -
            cooledBalAfterAllocation;
        // reallocate(
        //     currentEthUsd,
        //     cooledBalAfterAllocation,
        //     heatedBalAfterAllocation
        // );
    }

    // function reallocate(
    //     uint256 _currentEthUsd,
    //     int256 _cUsdBal,
    //     int256 _hUsdBal
    // ) private returns (uint, uint) {
    //     cEthBal = (_cUsdBal * decimals) / _currentEthUsd;
    //     hEthBal = (_hUsdBal * decimals) / _currentEthUsd;

    // }

    function abs(int x) private pure returns (int) {
        return x >= 0 ? x : -x;
    }

    // Pass in: address, tranche, amount, hotColdRatio, priceChange
}
