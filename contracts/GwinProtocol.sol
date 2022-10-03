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
    uint256 lastSettledEthUsd = 1000;
    uint256 decimals = 10**18;
    uint256 bps = 10**4;
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

    function getProfit(uint256 _ethUSd) public view returns (int256) {
        int256 profit = ((int(_ethUSd) - int(lastSettledEthUsd)) *
            int(decimals)) / int(lastSettledEthUsd);
        return profit;
    }

    // TEMP returns current ETH/USD
    function getCurrentEthUsd() public returns (uint256) {
        return 1100;
    }

    // make modular function that does calculations that both tranches need
    function trancheSpecificCalcs(
        bool _isCooled,
        int256 _ethUsdProfit,
        uint256 _currentEthUsd
    ) private returns (int256) {
        require(
            cEthBal > 0 && hEthBal > 0,
            "Protocol must have funds in order to settle."
        );
        uint256 trancheBal;
        int256 r;
        if (_isCooled == true) {
            trancheBal = cEthBal;
            r = -5000;
        } else {
            trancheBal = hEthBal;
            r = 5000;
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
        return allocationDifference;
    }

    function deposit() public {
        interact();
    }

    struct CalcInfo {
        uint256 currentEthUsd;
        int256 ethUsdProfit;
        int256 cooledAllocationDiff;
        int256 heatedAllocationDiff;
        int256 absHeatedAllocationDiff;
        int256 absCooledAllocationDiff;
        int256 minAbsAllocation;
        int256 nonNaturalDifference;
        uint256 percentCooledTranche;
        uint256 nonNaturalMultiplier;
        uint256 adjNonNaturalDiff;
        uint256 absAllocationTotal;
        int256 cooledAllocation;
        int256 heatedAllocation;
        uint256 totalLockedUsd;
    }

    // Interact: cEthBal, hEthBal, cEthUsdBal, hEthUsdBal, tranche, lastEthUsd, currentEthUsd
    function interact() internal returns (uint256) {
        CalcInfo memory calc;
        calc.currentEthUsd = getCurrentEthUsd();
        calc.ethUsdProfit = getProfit(calc.currentEthUsd);
        calc.cooledAllocationDiff = trancheSpecificCalcs(
            true,
            calc.ethUsdProfit,
            calc.currentEthUsd
        );
        calc.heatedAllocationDiff = trancheSpecificCalcs(
            false,
            calc.ethUsdProfit,
            calc.currentEthUsd
        );
        calc.absHeatedAllocationDiff = abs(calc.heatedAllocationDiff);
        calc.absCooledAllocationDiff = abs(calc.cooledAllocationDiff);
        calc.minAbsAllocation = calc.absCooledAllocationDiff >
            calc.absHeatedAllocationDiff
            ? calc.absHeatedAllocationDiff
            : calc.absCooledAllocationDiff;
        calc.nonNaturalDifference =
            calc.heatedAllocationDiff +
            calc.cooledAllocationDiff;
        calc.percentCooledTranche = ((cEthBal * bps) / (cEthBal + hEthBal));
        calc.nonNaturalMultiplier = calc.ethUsdProfit > 0
            ? calc.percentCooledTranche
            : ((1 * bps) - calc.percentCooledTranche);
        calc.adjNonNaturalDiff =
            uint(abs(calc.nonNaturalDifference)) *
            calc.nonNaturalMultiplier;
        calc.absAllocationTotal =
            uint(calc.minAbsAllocation) +
            calc.adjNonNaturalDiff;
        calc.cooledAllocation;
        calc.heatedAllocation;
        if (calc.cooledAllocationDiff < 0) {
            if ((cEthBal * calc.currentEthUsd) - calc.absAllocationTotal > 0) {
                calc.cooledAllocation = -int(calc.absAllocationTotal);
            } else {
                calc.cooledAllocation = int(cEthBal * calc.currentEthUsd);
            }
        } else {
            if ((hEthBal * calc.currentEthUsd) - calc.absAllocationTotal > 0) {
                calc.cooledAllocation = int(calc.absAllocationTotal);
            } else {
                calc.cooledAllocation = int(hEthBal * calc.currentEthUsd);
            }
        }
        calc.heatedAllocation = -calc.cooledAllocation;
        calc.totalLockedUsd = (cEthBal + hEthBal) * calc.currentEthUsd;
        uint256 cooledBalAfterAllocation = calc.totalLockedUsd -
            (cEthBal * calc.currentEthUsd);
        return cooledBalAfterAllocation;
    }

    function abs(int x) private pure returns (int) {
        return x >= 0 ? x : -x;
    }

    // Pass in: address, tranche, amount, hotColdRatio, priceChange
}
