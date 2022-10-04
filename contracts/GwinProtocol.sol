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
    uint256 ethUsd = 1100 * usdDecimals;
    uint256 bps = 10**4;
    // TEMP simulated balance
    uint256 cEthBal = 10 * decimals;
    // TEMP simulated balance
    uint256 hEthBal = 10 * decimals;
    uint256 pEthBal = cEthBal + hEthBal;

    // ****** TEMPORARY TESTING ******

    function test(
        uint _startPrice,
        uint _endPrice,
        uint _hEthAll,
        uint _cEthAll
    )
        public
        returns (
            uint,
            uint,
            uint
        )
    {
        hEthBal = _hEthAll * decimals;
        cEthBal = _cEthAll * decimals;
        lastSettledEthUsd = _startPrice * usdDecimals;
        ethUsd = _endPrice * usdDecimals;
        uint hEthVal;
        uint cEthVal;
        (hEthVal, cEthVal) = interact();
        return (hEthVal, cEthVal, pEthBal);
    }

    // Storing the GWIN token as a global variable, IERC20 imported above, address passed into constructor
    IERC20 public gwinToken;

    // Right when we deploy this contract, we need to know the address of GWIN token
    constructor(address _gwinTokenAddress) public {
        // pass in the address from the GwinToken.sol contract
        gwinToken = IERC20(_gwinTokenAddress);
    }

    // Get profit percent in basis points
    function getProfit(uint256 _ethUsd) public view returns (int256) {
        int256 profit = ((int(_ethUsd) - int(lastSettledEthUsd)) * int(bps)) /
            int(lastSettledEthUsd);
        return profit;
    }

    // TEMP returns current ETH/USD
    function getCurrentEthUsd() public returns (uint256) {
        return ethUsd;
    }

    // calculates allocation difference for a tranche
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

    function interact() public returns (uint, uint) {
        uint256 currentEthUsd = getCurrentEthUsd(); // current ETH/USD in terms of usdDecimals
        int256 ethUsdProfit = getProfit(currentEthUsd); // returns ETH/USD profit in terms of basis points // 1000
        // find expected return and use it to calculate allocation difference for each tranche
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
        // use allocation differences to figure the absolute allocation total
        uint256 absAllocationTotal;
        {
            // scope to avoid stack too deep error
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
        // calculate the actual allocation for the cooled tranche
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
        // heated allocation is the inverse of the cooled allocation
        heatedAllocation = -cooledAllocation; // USD allocation in usdDecimal terms
        uint256 totalLockedUsd = ((cEthBal + hEthBal) * currentEthUsd) / // USD balance of protocol in usdDecimal terms
            decimals;
        int256 cooledBalAfterAllocation = int(totalLockedUsd) - // cooled USD balance in usdDecimal terms
            (int((cEthBal * currentEthUsd)) / int(decimals)) +
            cooledAllocation;
        int256 heatedBalAfterAllocation = int(totalLockedUsd) - // heated USD balance in usdDecimal terms
            cooledBalAfterAllocation;
        (hEthBal, cEthBal) = reallocate( // reallocate the protocol ETH according to price movement
            currentEthUsd,
            cooledBalAfterAllocation,
            heatedBalAfterAllocation
        );
        return (hEthBal, cEthBal);
    }

    function reallocate(
        uint256 _currentEthUsd, // in usdDecimal form
        int256 _cUsdBal, // in usdDecimal form
        int256 _hUsdBal // in usdDecimal form
    ) private returns (uint, uint) {
        uint cEthBalNew = (uint(_cUsdBal) * decimals) / _currentEthUsd; // new cEth Balance in Wei
        uint hEthBalNew = pEthBal - cEthBalNew; // new hEth Balance in Wei (inverse of cEth Balance)
        return (hEthBalNew, cEthBalNew);
    }

    function abs(int x) private pure returns (int) {
        return x >= 0 ? x : -x;
    }
}
