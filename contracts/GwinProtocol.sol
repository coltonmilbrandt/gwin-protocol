// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract GwinProtocol is Ownable, ReentrancyGuard {
    struct Bal {
        uint cBal;
        uint cPercent;
        uint hBal;
        uint hPercent;
    }

    // user address -> user balances struct
    mapping(address => Bal) public ethStakedBalance;
    // token address -> staker address -> amount
    mapping(address => mapping(address => uint256)) public stakingBalance;
    // staker address -> unique tokens staked
    mapping(address => uint256) public uniquePositions;
    // address -> isUnique
    mapping(address => bool) public isUniqueEthStaker;
    // array of ETH stakers
    address[] public ethStakers;
    // array of stakers
    address[] public stakers;
    // array of the allowed tokens
    address[] public allowedTokens;

    AggregatorV3Interface internal ethUsdPriceFeed;

    enum PROTOCOL_STATE {
        OPEN, //1
        CLOSED, //2
        CALCULATING //3
    }

    PROTOCOL_STATE public protocol_state;

    // ********* Decimal Values *********
    uint256 decimals = 10**18;
    uint256 usdDecimals = 10**8;
    uint256 bps = 10**12;

    // ************* Values *************
    uint256 lastSettledEthUsd;
    uint256 ethUsd;
    uint256 hEthBal;
    uint256 cEthBal;
    // Potential ISSUE if these can be changed, but I doubt that's the case

    // // *********  Test Values   *********
    // uint256 pEthBal;

    // Storing the GWIN token as a global variable, IERC20 imported above, address passed into constructor
    IERC20 public gwinToken;

    // Right when we deploy this contract, we need to know the address of GWIN token
    constructor(
        address _gwinTokenAddress,
        address _priceFeedAddress,
        address _link
    ) public {
        // pass in the address from the GwinToken.sol contract
        gwinToken = IERC20(_gwinTokenAddress);
        protocol_state = PROTOCOL_STATE.CLOSED;
        ethUsdPriceFeed = AggregatorV3Interface(_priceFeedAddress);
    }

    /// INITIALIZE-PROTOCOL /// - this deposits an equal amount to each tranche to initialize the protocol
    function initializeProtocol() external payable {
        require(
            protocol_state == PROTOCOL_STATE.CLOSED,
            "The Protocol is already initialized."
        );
        require(
            cEthBal == 0 && hEthBal == 0,
            "The Protocol already has funds deposited."
        );
        if (isUniqueEthStaker[msg.sender] == false) {
            ethStakers.push(msg.sender);
        }
        uint splitAmount = msg.value / 2;
        ethStakedBalance[msg.sender].cBal += splitAmount;
        ethStakedBalance[msg.sender].cPercent = bps;
        cEthBal = splitAmount;
        ethStakedBalance[msg.sender].hBal += splitAmount;
        ethStakedBalance[msg.sender].hPercent = bps;
        hEthBal = splitAmount;
        protocol_state = PROTOCOL_STATE.OPEN;
        ethUsd = retrieveCurrentEthUsd();
        lastSettledEthUsd = ethUsd;
    }

    /// DEPOSIT /// - used to deposit to cooled or heated tranche, or both
    function depositToTranche(
        bool _isCooled,
        bool _isHeated,
        uint _cAmount,
        uint _hAmount
    ) external payable {
        require(
            protocol_state == PROTOCOL_STATE.OPEN,
            "The Protocol has not been initialized yet."
        );
        require(msg.value > 0, "Amount must be greater than zero.");
        require(_isCooled == true || _isHeated == true);
        require(_cAmount + _hAmount <= msg.value);

        // Interact to rebalance Tranches with new USD price
        interact();
        // Re-adjust to update balances after price change
        reAdjust(true, _isCooled, _isHeated);
        // Deposit ETH
        if (_isCooled == true && _isHeated == false) {
            ethStakedBalance[msg.sender].cBal += msg.value;
            cEthBal += msg.value;
        } else if (_isCooled == false && _isHeated == true) {
            ethStakedBalance[msg.sender].hBal += msg.value;
            hEthBal += msg.value;
        } else if (_isCooled == true && _isHeated == true) {
            ethStakedBalance[msg.sender].cBal += _cAmount;
            cEthBal += _cAmount;
            ethStakedBalance[msg.sender].hBal += _hAmount;
            hEthBal += _hAmount;
        }
        if (isUniqueEthStaker[msg.sender] == false) {
            ethStakers.push(msg.sender);
        }
        // Re-Adjust user percentages
        reAdjust(false, _isCooled, _isHeated);

        // TEMP until price feed is implemented, don't want to get price again, rather use price from interact()
        lastSettledEthUsd = ethUsd;
    }

    // /// PREVIEW-USER-BALANCE /// - preview balance at the current ETH/USD price
    // function previewUserBalance() public view returns (uint, uint) {
    //     uint heatedBalance;
    //     uint cooledBalance;
    //     (heatedBalance, cooledBalance) = simulateInteract(
    //         retrieveCurrentEthUsd()
    //     );
    //     uint userHeatedBalance = (heatedBalance *
    //         ethStakedBalance[msg.sender].hPercent) / bps;
    //     uint userCooledBalance = (cooledBalance *
    //         ethStakedBalance[msg.sender].cPercent) / bps;
    //     return (userHeatedBalance, userCooledBalance);
    // }

    /// WITHDRAW /// - used to withdraw from cooled or heated tranche, or both
    function withdrawFromTranche(
        bool _isCooled,
        bool _isHeated,
        uint _cAmount,
        uint _hAmount,
        bool _isAll
    ) external nonReentrant {
        require(
            protocol_state == PROTOCOL_STATE.OPEN,
            "The Protocol has not been initialized yet."
        );
        // TEMP ||
        require(
            cEthBal > 0 || hEthBal > 0,
            "The Protocol needs initial funds deposited."
        );
        if (_isAll == false) {
            require(
                _cAmount > 0 || _hAmount > 0,
                "Amount must be greater than zero."
            );
        }
        require(_isCooled == true || _isHeated == true);

        // Interact to rebalance Tranches with new USD price
        interact();
        // Re-adjust the user balances based on price change
        reAdjust(true, _isCooled, _isHeated);

        if (_isAll == true) {
            if (_isCooled == true) {
                _cAmount = ethStakedBalance[msg.sender].cBal;
            }
            if (_isHeated == true) {
                _hAmount = ethStakedBalance[msg.sender].hBal;
            }
        }

        require(
            _cAmount <= ethStakedBalance[msg.sender].cBal &&
                _hAmount <= ethStakedBalance[msg.sender].hBal,
            "The amount to withdrawal is greater than the available balance."
        );

        // Withdraw ETH
        if (_cAmount > 0 && _hAmount > 0) {
            // Cooled and Heated
            ethStakedBalance[msg.sender].cBal -= _cAmount;
            cEthBal -= _cAmount;
            ethStakedBalance[msg.sender].hBal -= _hAmount;
            hEthBal -= _hAmount;
            payable(msg.sender).transfer(_cAmount + _hAmount);
        } else {
            if (_cAmount > 0 && _hAmount == 0) {
                // Cooled, No Heated
                ethStakedBalance[msg.sender].cBal -= _cAmount;
                cEthBal -= _cAmount;
                payable(msg.sender).transfer(_cAmount);
            } else if (_cAmount == 0 && _hAmount > 0) {
                // Heated, No Cooled
                ethStakedBalance[msg.sender].hBal -= _hAmount;
                hEthBal -= _hAmount;
                payable(msg.sender).transfer(_hAmount);
            }
        }

        // Re-Adjust user percentages
        reAdjust(false, _isCooled, _isHeated);

        // TEMP until price feed is implemented, don't want to get price again, rather use price from interact()
        lastSettledEthUsd = ethUsd;
    }

    /// REMOVE-FROM-ARRAY /// - removes the staker from the array of ETH stakers
    function removeFromArray(uint index) private {
        ethStakers[index] = ethStakers[ethStakers.length - 1];
        ethStakers.pop();
    }

    // RE-ADJUST /// - adjusts affected tranche percentages and balances
    function reAdjust(
        bool _beforeTx,
        bool _isCooled,
        bool _isHeated
    ) private {
        if (_beforeTx == true) {
            // BEFORE deposit, only balances are affected based on percentages
            liquidateIfZero();
            // ISSUE stakers need removed if they get liquidated (as of now, only one is removed)
            // ISSUE this could likely be optimized to avoid performing the for loops twice when liquidated
            for (
                uint256 ethStakersIndex = 0;
                ethStakersIndex < ethStakers.length;
                ethStakersIndex++
            ) {
                address addrC = ethStakers[ethStakersIndex];
                ethStakedBalance[addrC].cBal =
                    (cEthBal * ethStakedBalance[addrC].cPercent) /
                    bps;
                ethStakedBalance[addrC].hBal =
                    (hEthBal * ethStakedBalance[addrC].hPercent) /
                    bps;
            }
        } else {
            // AFTER tx, only affected tranche percentages change
            uint indexToRemove; // to track index of user in ethStakers array if account emptied
            bool indexNeedsRemoved; // to differentiate indexToRemove == 0 from default ethStakers[0]
            if (_isCooled == true && _isHeated == false) {
                // only Cooled tranche percentage numbers are affected by cooled tx
                for (
                    uint256 ethStakersIndex = 0;
                    ethStakersIndex < ethStakers.length;
                    ethStakersIndex++
                ) {
                    address addrC = ethStakers[ethStakersIndex];
                    ethStakedBalance[addrC].cPercent =
                        (ethStakedBalance[addrC].cBal * bps) /
                        cEthBal;
                    // Flags index and stores for removal AFTER calculations are finished
                    if (
                        ethStakedBalance[addrC].cBal <= 0 &&
                        ethStakedBalance[addrC].hBal <= 0
                    ) {
                        indexNeedsRemoved = true;
                        indexToRemove = ethStakersIndex;
                    }
                }
            } else if (_isCooled == false && _isHeated == true) {
                // only Heated tranche percentage numbers are affected by heated tx
                for (
                    uint256 ethStakersIndex = 0;
                    ethStakersIndex < ethStakers.length;
                    ethStakersIndex++
                ) {
                    address addrC = ethStakers[ethStakersIndex];
                    ethStakedBalance[addrC].hPercent =
                        (ethStakedBalance[addrC].hBal * bps) /
                        hEthBal;
                    // Flags index and stores for removal AFTER calculations are finished
                    if (
                        ethStakedBalance[addrC].cBal <= 0 &&
                        ethStakedBalance[addrC].hBal <= 0
                    ) {
                        indexNeedsRemoved = true;
                        indexToRemove = ethStakersIndex;
                    }
                }
            } else {
                // Cooled and Heated tranche percentage numbers are affected by tx
                for (
                    uint256 ethStakersIndex = 0;
                    ethStakersIndex < ethStakers.length;
                    ethStakersIndex++
                ) {
                    address addrC = ethStakers[ethStakersIndex];
                    ethStakedBalance[addrC].cPercent =
                        (ethStakedBalance[addrC].cBal * bps) /
                        cEthBal;
                    ethStakedBalance[addrC].hPercent =
                        (ethStakedBalance[addrC].hBal * bps) /
                        hEthBal;
                    // Flags index and stores for removal AFTER calculations are finished
                    if (
                        ethStakedBalance[addrC].cBal <= 0 &&
                        ethStakedBalance[addrC].hBal <= 0
                    ) {
                        indexNeedsRemoved = true;
                        indexToRemove = ethStakersIndex;
                    }
                }
            }
            // Remove user if balances are empty, done after calculation so array indexes are not disrupted
            if (indexNeedsRemoved == true) {
                removeFromArray(indexToRemove);
            }
        }
    }

    /// LIQUIDATE-IF-ZERO /// - liquidates every user in a zero balance tranche
    function liquidateIfZero() private {
        for (
            uint256 ethStakersIndex = 0;
            ethStakersIndex < ethStakers.length;
            ethStakersIndex++
        ) {
            address addrC = ethStakers[ethStakersIndex];
            if (cEthBal == 0) {
                // if tranche is liquidated, reset user to zero
                ethStakedBalance[addrC].cPercent = 0;
                ethStakedBalance[addrC].cBal = 0;
            }
            if (hEthBal == 0) {
                // if tranche is liquidated, reset user to zero
                ethStakedBalance[addrC].hBal = 0;
                ethStakedBalance[addrC].hPercent = 0;
            }
        }
    }

    /// VIEW-BALANCE-FUNCTIONS /// - check balances

    function retrieveCurrentEthUsd() public view returns (uint) {
        (, int256 price, , , ) = ethUsdPriceFeed.latestRoundData();
        return uint(price);
    }

    function retrieveEthInContract() public view returns (uint) {
        return address(this).balance;
    }

    function retrieveCEthPercentBalance(address _user)
        public
        view
        returns (uint)
    {
        return ethStakedBalance[_user].cPercent;
    }

    function retrieveHEthPercentBalance(address _user)
        public
        view
        returns (uint)
    {
        return ethStakedBalance[_user].hPercent;
    }

    function retrieveCEthBalance(address _user) public view returns (uint) {
        return ethStakedBalance[_user].cBal;
    }

    function retrieveHEthBalance(address _user) public view returns (uint) {
        return ethStakedBalance[_user].hBal;
    }

    function retrieveAddressAtIndex(uint _index) public view returns (address) {
        return ethStakers[_index];
    }

    function retrieveProtocolCEthBalance() public view returns (uint) {
        return cEthBal;
    }

    function retrieveProtocolHEthBalance() public view returns (uint) {
        return hEthBal;
    }

    function retrieveProtocolEthPrice() public view returns (uint, uint) {
        return (ethUsd, lastSettledEthUsd);
    }

    // // ****** TEMPORARY TESTING ******
    // function test(
    //     uint _startPrice,
    //     uint _endPrice,
    //     uint _hEthAll,
    //     uint _cEthAll
    // )
    //     public
    //     returns (
    //         uint,
    //         uint,
    //         uint
    //     )
    // {
    //     hEthBal = _hEthAll * decimals;
    //     cEthBal = _cEthAll * decimals;
    //     pEthBal = (_hEthAll + _cEthAll) * decimals;
    //     lastSettledEthUsd = _startPrice * usdDecimals;
    //     ethUsd = _endPrice * usdDecimals;
    //     uint hEthVal;
    //     uint cEthVal;
    //     (hEthVal, cEthVal) = interact();
    //     return (hEthVal, cEthVal, pEthBal);
    // }

    /// STAKE-TOKENS /// - for future use with ERC-20s
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

    /// UPDATE-UNIQUE-POSITIONS /// - updates the mapping of user to tokens staked
    function updateUniquePositions(address _user, address _token) internal {
        // NOTES: I feel like it should be '>=' below instead

        // If the staking balance of the staker is less that or equal to 0 then...
        if (stakingBalance[_token][_user] <= 0) {
            // add 1 to the number of unique tokens staked
            uniquePositions[_user] = uniquePositions[_user] + 1;
        }
    }

    /// STAKE-TOKENS /// - add a token address to allowed tokens for staking, only owner can call
    function addAllowedTokens(address _token) public onlyOwner {
        // add token address to allowedTokens[] array
        allowedTokens.push(_token);
    }

    /// TOKEN-IS-ALLOWED /// - returns whether token is allowed
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

    /// GET PROFIT /// - returns profit percentage in terms of basis points
    function getProfit(uint256 _ethUsd) public view returns (int256) {
        int256 profit = ((int(_ethUsd) - int(lastSettledEthUsd)) * int(bps)) /
            int(lastSettledEthUsd);
        return profit;
    }

    /// TRANCHE SPECIFIC CALCS /// - calculates allocation difference for a tranche (also avoids 'stack too deep' error)
    function trancheSpecificCalcs(
        bool _isCooled,
        int256 _ethUsdProfit,
        uint256 _currentEthUsd
    ) private view returns (int256, int256) {
        // TEMP
        // require(
        //     cEthBal > 0 || hEthBal > 0, // in Wei
        //     "Protocol must have funds in order to settle."
        // );
        uint256 trancheBal;
        int256 r;
        // get tranche balance and basis points for expected return
        if (_isCooled == true) {
            trancheBal = cEthBal; // in Wei
            r = -50_0000000000; // basis points
        } else {
            trancheBal = hEthBal; // in Wei
            r = 50_0000000000; // basis points
        }
        // TEMP
        // require(trancheBal > 0, "Tranche must have a balance.");
        require(
            r == -50_0000000000 || r == 50_0000000000,
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

    /// INTERACT /// - rebalances the cooled and heated tranches
    function interact() private returns (uint, uint) {
        uint256 currentEthUsd = retrieveCurrentEthUsd();
        ethUsd = currentEthUsd;
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
            if (
                // the cEthBal USD value - absAllocation (in usdDecimals)
                int((cEthBal * currentEthUsd) / decimals) -
                    int(absAllocationTotal) >
                0
            ) {
                cooledAllocation = -int(absAllocationTotal);
            } else {
                cooledAllocation = int((cEthBal * currentEthUsd) / decimals); // the cEthBal USD value (in UsDecimals * Decimals)
            }
        } else {
            if (
                int((hEthBal * currentEthUsd) / decimals) -
                    int(absAllocationTotal) >
                0
            ) {
                cooledAllocation = int(absAllocationTotal); // absolute allocation in UsDecimals
            } else {
                cooledAllocation = int((hEthBal * currentEthUsd) / decimals);
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

    /// REALLOCATE /// - uses the USD values to calculate ETH balances of tranches
    function reallocate(
        uint256 _currentEthUsd, // in usdDecimal form
        int256 _cUsdBal, // in usdDecimal form
        int256 _hUsdBal // in usdDecimal form
    ) private view returns (uint, uint) {
        uint cEthBalNew = (uint(_cUsdBal) * decimals) / _currentEthUsd; // new cEth Balance in Wei
        uint hEthBalNew = (uint(_hUsdBal) * decimals) / _currentEthUsd; // new hEth Balance in Wei
        return (hEthBalNew, cEthBalNew);
    }

    /// ABSOLUTE-VALUE /// - returns the absolute value of an int
    function abs(int x) private pure returns (int) {
        return x >= 0 ? x : -x;
    }

    /// SIMULATE INTERACT /// - view only of simulated rebalance of the cooled and heated tranches
    function simulateInteract(uint _ethUsd) public view returns (uint, uint) {
        uint256 currentEthUsd = _ethUsd;
        int256 ethUsdProfit = getProfit(currentEthUsd); // returns ETH/USD profit in terms of basis points // 1000
        // find expected return and use it to calculate allocation difference for each tranche
        (
            int256 cooledAllocationDiff,
            int256 cooledChange
        ) = trancheSpecificCalcs(true, ethUsdProfit, currentEthUsd);
        // return cooledAllocationDiff;
        (
            int256 heatedAllocationDiff,
            int256 heatedChange
        ) = trancheSpecificCalcs(false, ethUsdProfit, currentEthUsd);
        // return heatedAllocationDiff;
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
            if (
                // the cEthBal USD value - absAllocation (in usdDecimals)
                int((cEthBal * currentEthUsd) / decimals) -
                    int(absAllocationTotal) >
                0
            ) {
                cooledAllocation = -int(absAllocationTotal);
            } else {
                cooledAllocation = int((cEthBal * currentEthUsd) / decimals); // the cEthBal USD value (in UsDecimals * Decimals)
            }
        } else {
            if (
                int((hEthBal * currentEthUsd) / decimals) -
                    int(absAllocationTotal) >
                0
            ) {
                cooledAllocation = int(absAllocationTotal); // absolute allocation in UsDecimals
            } else {
                cooledAllocation = int((hEthBal * currentEthUsd) / decimals);
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
        uint hEthBalSim;
        uint cEthBalSim;
        (hEthBalSim, cEthBalSim) = reallocate( // reallocate the protocol ETH according to price movement
            currentEthUsd,
            cooledBalAfterAllocation,
            heatedBalAfterAllocation
        );
        return (hEthBalSim, cEthBalSim);
    }

    function getRangeOfReturns(
        address _address,
        bool _isCooled,
        bool _isHeated,
        bool _isAll
    ) public view returns (int[] memory) {
        uint ethUsdPrice = retrieveCurrentEthUsd();
        int currentPercent = -50_0000000000;
        int ethUsdAtIndex;
        int[] memory estBals = new int[](11);
        for (uint index = 0; index < 11; index++) {
            ethUsdAtIndex =
                (int(ethUsdPrice) * (int(bps) + currentPercent)) /
                int(bps);
            uint hBalEst;
            uint cBalEst;
            (hBalEst, cBalEst) = simulateInteract(uint(ethUsdAtIndex));
            uint balanceRequested;
            if (_isHeated == true || _isAll == true) {
                balanceRequested =
                    (hBalEst * ethStakedBalance[_address].hPercent) /
                    bps;
            }
            if (_isCooled == true || _isAll == true) {
                balanceRequested +=
                    (cBalEst * ethStakedBalance[_address].cPercent) /
                    bps;
            }
            estBals[index] = int(balanceRequested);
            currentPercent += 10_0000000000;
        }

        return (estBals);
    }
}
