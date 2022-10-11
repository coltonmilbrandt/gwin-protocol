// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract GwinProtocol is Ownable {
    struct Bal {
        uint balance;
        uint percent;
    }

    //    isCooled -> depositor address -> amount
    // mapping(bool => mapping(address => Bal)) public ethBalance;
    mapping(address => Bal) public cooledEthBalance;
    mapping(address => Bal) public heatedEthBalance;
    // token address -> staker address -> amount
    mapping(address => mapping(address => uint256)) public stakingBalance;
    // staker address -> unique tokens staked
    mapping(address => uint256) public uniquePositions;
    // // token address -> token price feed address
    // mapping(address => address) public tokenPriceFeedMapping;
    mapping(address => bool) public isUniqueCooledStaker;
    mapping(address => bool) public isUniqueHeatedStaker;
    address[] public cooledStakers;
    address[] public heatedStakers;
    // array of stakers
    address[] public stakers;
    // array of the allowed tokens
    address[] public allowedTokens;

    enum PROTOCOL_STATE {
        OPEN, //1
        CLOSED, //2
        CALCULATING //3
    }
    PROTOCOL_STATE public protocol_state;

    // ********* Decimal Values *********
    uint256 decimals = 10**18;
    uint256 usdDecimals = 10**8;
    uint256 bps = 10**4;

    // *********  Test Values   *********
    uint256 lastSettledEthUsd = 1000 * usdDecimals;
    uint256 ethUsd = 1200 * usdDecimals;
    // TEMP simulated balance
    uint256 hEthBal;
    // TEMP simulated balance
    uint256 cEthBal;
    uint256 pEthBal = cEthBal + hEthBal;

    // Storing the GWIN token as a global variable, IERC20 imported above, address passed into constructor
    IERC20 public gwinToken;

    // Right when we deploy this contract, we need to know the address of GWIN token
    constructor(address _gwinTokenAddress) public {
        // pass in the address from the GwinToken.sol contract
        gwinToken = IERC20(_gwinTokenAddress);
        protocol_state = PROTOCOL_STATE.CLOSED;
    }

    function initializeProtocol() public payable {
        require(
            protocol_state == PROTOCOL_STATE.CLOSED,
            "The Protocol is already initialized."
        );
        require(
            cEthBal == 0 && hEthBal == 0,
            "The Protocol already has funds deposited."
        );
        uint splitAmount = msg.value / 2;
        cooledEthBalance[msg.sender].balance += splitAmount;
        cooledEthBalance[msg.sender].percent = 10000;
        cEthBal = splitAmount;
        heatedEthBalance[msg.sender].balance += splitAmount;
        heatedEthBalance[msg.sender].percent = 10000;
        hEthBal = splitAmount;
        protocol_state = PROTOCOL_STATE.OPEN;
        // TEMP replace with getCurrentEthUsd() and price feed
        lastSettledEthUsd = 1000 * usdDecimals;
        ethUsd = 1000 * usdDecimals;
        // end TEMP
    }

    function depositToTranche(bool _isCooled) public payable returns (bool) {
        require(
            protocol_state == PROTOCOL_STATE.OPEN,
            "The Protocol has not been initialized yet."
        );
        require(
            cEthBal > 0 && hEthBal > 0,
            "The Protocol needs initial funds deposited."
        );

        // Set ETH/USD prices (last settled and current)
        // Interact to rebalance Tranches with new USD price
        interact();
        // // Deposit ETH
        // if (_isCooled == true) {
        //     cooledEthBalance[msg.sender].balance += msg.value;
        //     cEthBal += msg.value;
        //     // add to cooledStakers array if absent
        //     if (isUniqueCooledStaker[msg.sender] == false) {
        //         cooledStakers.push(msg.sender);
        //     }
        // } else {
        //     heatedEthBalance[msg.sender].balance += msg.value;
        //     hEthBal += msg.value;
        //     // add to heatedStakers array if absent
        //     if (isUniqueHeatedStaker[msg.sender] == false) {
        //         heatedStakers.push(msg.sender);
        //     }
        // }
        // // Re-Adjust user percentages for affected Tranche
        // reAdjust();
        // lastSettledEthUsd = getCurrentEthUsd();
    }

    function retrieveBalance() public view returns (uint) {
        return cooledEthBalance[msg.sender].balance;
    }

    function retrieveProtocolBalance() public view returns (uint) {
        return cEthBal;
    }

    // Adjust affected tranche percentages
    function reAdjust() public {
        // select the affected tranche
        // loop through stakers[] to get addresses (have heatedStakers[] and cooledStakers[]?)
        //      use addresses as key to Bal mappings
        //      use new ETH balance to determine percent ownership (can a value be used instead of writing?)
    }

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
        pEthBal = (_hEthAll + _cEthAll) * decimals;
        lastSettledEthUsd = _startPrice * usdDecimals;
        ethUsd = _endPrice * usdDecimals;
        uint hEthVal;
        uint cEthVal;
        (hEthVal, cEthVal) = interact();
        return (hEthVal, cEthVal, pEthBal);
    }

    function stakeTokens(uint256 _amount, address _token) public {
        // Make sure that the amount to stake is more than 0
        require(_amount > 0, "Amount must be more than 0");
        // Check whether token is allowed by passing it to tokenIsAllowed()
        require(tokenIsAllowed(_token), "Token is not currently allowed.");

        // NOTES: transferFrom  --  ERC20s have transfer and transfer from.
        // Transfer only works if you call it from the wallet that owns the token

        // Transfer _amount of _token to the contract address
        IERC20(_token).transferFrom(msg.sender, address(this), _amount);
        // Set the _token as one of the unique tokens staked by the staker
        updateUniquePositions(msg.sender, _token);
        // Update the staking balance for the staker
        stakingBalance[_token][msg.sender] =
            stakingBalance[_token][msg.sender] +
            _amount;
        // If after this, the staker has just 1 token staked, then add the staker to stakers[] array
        if (uniquePositions[msg.sender] == 1) {
            stakers.push(msg.sender);
        }
    }

    // updates the mapping of user to tokens staked, could be called INCREMENT
    function updateUniquePositions(address _user, address _token) internal {
        // NOTES: I feel like it should be '>=' below instead

        // If the staking balance of the staker is less that or equal to 0 then...
        if (stakingBalance[_token][_user] <= 0) {
            // add 1 to the number of unique tokens staked
            uniquePositions[_user] = uniquePositions[_user] + 1;
        }
    }

    // add a token address to allowed tokens for staking, only owner can call
    function addAllowedTokens(address _token) public onlyOwner {
        // add token address to allowedTokens[] array
        allowedTokens.push(_token);
    }

    // returns whether token is allowed
    function tokenIsAllowed(address _token) public view returns (bool) {
        // Loops through the array of allowedTokens[] for length of array
        for (
            uint256 allowedTokensIndex = 0;
            allowedTokensIndex < allowedTokens.length;
            allowedTokensIndex++
        ) {
            // If token at index matched the passed in token, return true
            if (allowedTokens[allowedTokensIndex] == _token) {
                return true;
            }
        }
        return false;
    }

    // Get profit percent in basis points
    function getProfit(uint256 _ethUsd) public view returns (int256) {
        int256 profit = ((int(_ethUsd) - int(lastSettledEthUsd)) * int(bps)) /
            int(lastSettledEthUsd);
        return profit;
    }

    // TEMP returns current ETH/USD change to view later
    function getCurrentEthUsd() public returns (uint256) {
        ethUsd = 1200 * usdDecimals;
        return ethUsd;
    }

    // calculates allocation difference for a tranche
    function trancheSpecificCalcs(
        bool _isCooled,
        int256 _ethUsdProfit,
        uint256 _currentEthUsd
    ) private view returns (int256, int256) {
        require(
            cEthBal > 0 && hEthBal > 0, // in Wei
            "Protocol must have funds in order to settle."
        );
        uint256 trancheBal;
        int256 r;
        // get tranche balance and basis points for expected return
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
        return (allocationDifference, trancheChange);
    }

    // change to private down the line?
    function interact() public returns (uint, uint) {
        uint256 currentEthUsd = getCurrentEthUsd(); // current ETH/USD in terms of usdDecimals
        int256 ethUsdProfit = getProfit(currentEthUsd); // returns ETH/USD profit in terms of basis points // 1000
        // find expected return and use it to calculate allocation difference for each tranche
        (
            int256 cooledAllocationDiff,
            int256 cooledChange
        ) = trancheSpecificCalcs(true, ethUsdProfit, currentEthUsd);
        (
            int256 heatedAllocationDiff,
            int256 heatedChange
        ) = trancheSpecificCalcs(false, ethUsdProfit, currentEthUsd);
        // use allocation differences to figure the absolute allocation total
        uint256 absAllocationTotal;
        {
            // scope to avoid 'stack too deep' error
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
            uint256 adjNonNaturalDiff = (uint(abs(nonNaturalDifference)) *
                nonNaturalMultiplier) / bps;
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
        int256 cooledBalAfterAllocation = ((int(cEthBal * lastSettledEthUsd) +
            cooledChange) / int(decimals)) + cooledAllocation;
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
    ) private view returns (uint, uint) {
        uint cEthBalNew = (uint(_cUsdBal) * decimals) / _currentEthUsd; // new cEth Balance in Wei
        uint hEthBalNew = pEthBal - cEthBalNew; // new hEth Balance in Wei (inverse of cEth Balance)
        return (hEthBalNew, cEthBalNew);
    }

    function abs(int x) private pure returns (int) {
        return x >= 0 ? x : -x;
    }
}
