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

    // // user address -> user balances struct
    // mapping(address => Bal) public ethStakedBalance;

    // pool ID -> user address -> user balances struct
    mapping(uint => mapping(address => Bal)) public ethStakedBalance;

    // token address -> staker address -> amount
    mapping(address => mapping(address => uint256)) public stakingBalance;
    // staker address -> unique tokens staked
    mapping(address => uint256) public uniquePositions;
    // pool ID    ->   address  ->  isUnique
    mapping(uint => mapping(address => bool)) public isUniqueEthStaker;

    //    pool ID --> struct
    mapping(uint => Pool) public pool;

    // pool ID --> array of ETH stakers
    mapping(uint => address[]) public ethStakers;
    // array of stakers
    address[] public stakers;
    // array of the allowed tokens
    address[] public allowedTokens;
    // array of pool IDs
    uint[] public poolIds;

    AggregatorV3Interface internal ethUsdPriceFeed;

    // ********* Decimal Values *********
    uint256 decimals = 10**18;
    uint256 usdDecimals = 10**8;
    uint256 bps = 10**12;

    // ************* Values *************
    uint newPoolId = 0;

    struct Pool {
        uint256 lastSettledUsdPrice; // change to last settled price
        uint256 currentUsdPrice; // change to current price
        // add price feed address, may need extra work to get from commodities to USD to ETH
        uint256 hEthBal;
        uint256 cEthBal;
        uint256 hRate;
        uint256 cRate;
        uint8 poolType; // as in classic or modified
        // may need protocol state added
    }

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
        ethUsdPriceFeed = AggregatorV3Interface(_priceFeedAddress);
    }

    /// INITIALIZE-PROTOCOL /// - this deposits an equal amount to each tranche to initialize the protocol
    function initializeProtocol(uint8 _type) external payable returns (uint) {
        // ADD require that pool ID is not taken
        poolIds.push(newPoolId);
        pool[newPoolId].poolType = _type;
        require(
            pool[newPoolId].cEthBal == 0 && pool[newPoolId].hEthBal == 0,
            "The Protocol already has funds deposited."
        );
        if (isUniqueEthStaker[newPoolId][msg.sender] == false) {
            ethStakers[newPoolId].push(msg.sender);
            isUniqueEthStaker[newPoolId][msg.sender] = true;
        }
        uint splitAmount = msg.value / 2;
        ethStakedBalance[newPoolId][msg.sender].cBal += splitAmount;
        ethStakedBalance[newPoolId][msg.sender].cPercent = bps;
        pool[newPoolId].cEthBal = splitAmount;
        ethStakedBalance[newPoolId][msg.sender].hBal += splitAmount;
        ethStakedBalance[newPoolId][msg.sender].hPercent = bps;
        pool[newPoolId].hEthBal = splitAmount;
        pool[newPoolId].currentUsdPrice = retrieveCurrentUsdPrice(newPoolId);
        pool[newPoolId].lastSettledUsdPrice = pool[newPoolId].currentUsdPrice;
        newPoolId++;
        return newPoolId - 1;
    }

    /// DEPOSIT /// - used to deposit to cooled or heated tranche, or both
    function depositToTranche(
        uint _poolId,
        bool _isCooled,
        bool _isHeated,
        uint _cAmount,
        uint _hAmount
    ) external payable {
        require(msg.value > 0, "Amount must be greater than zero.");
        require(_isCooled == true || _isHeated == true);
        require(_cAmount + _hAmount <= msg.value);

        // Interact to rebalance Tranches with new USD price
        interact(_poolId);
        // Re-adjust to update balances after price change
        reAdjust(_poolId, true, _isCooled, _isHeated);
        // Deposit ETH
        if (_isCooled == true && _isHeated == false) {
            ethStakedBalance[_poolId][msg.sender].cBal += msg.value;
            pool[_poolId].cEthBal += msg.value;
        } else if (_isCooled == false && _isHeated == true) {
            ethStakedBalance[_poolId][msg.sender].hBal += msg.value;
            pool[_poolId].hEthBal += msg.value;
        } else if (_isCooled == true && _isHeated == true) {
            ethStakedBalance[_poolId][msg.sender].cBal += _cAmount;
            pool[_poolId].cEthBal += _cAmount;
            ethStakedBalance[_poolId][msg.sender].hBal += _hAmount;
            pool[_poolId].hEthBal += _hAmount;
        }
        if (isUniqueEthStaker[_poolId][msg.sender] == false) {
            ethStakers[_poolId].push(msg.sender);
            isUniqueEthStaker[_poolId][msg.sender] = true;
        }
        // Re-Adjust user percentages
        reAdjust(_poolId, false, _isCooled, _isHeated);

        // TEMP until price feed is implemented, don't want to get price again, rather use price from interact()
        pool[_poolId].lastSettledUsdPrice = pool[_poolId].currentUsdPrice;
    }

    // /// PREVIEW-USER-BALANCE /// - preview balance at the current ETH/USD price
    // function previewUserBalance() public view returns (uint, uint) {
    //     uint heatedBalance;
    //     uint cooledBalance;
    //     (heatedBalance, cooledBalance) = simulateInteract(
    //         retrieveCurrentUsdPrice(_poolId)
    //     );
    //     uint userHeatedBalance = (heatedBalance *
    //         ethStakedBalance[_poolId][msg.sender].hPercent) / bps;
    //     uint userCooledBalance = (cooledBalance *
    //         ethStakedBalance[_poolId][msg.sender].cPercent) / bps;
    //     return (userHeatedBalance, userCooledBalance);
    // }

    /// WITHDRAW /// - used to withdraw from cooled or heated tranche, or both
    function withdrawFromTranche(
        uint _poolId,
        bool _isCooled,
        bool _isHeated,
        uint _cAmount,
        uint _hAmount,
        bool _isAll
    ) external nonReentrant {
        // TEMP ||
        require(
            pool[_poolId].cEthBal > 0 || pool[_poolId].hEthBal > 0,
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
        interact(_poolId);
        // Re-adjust the user balances based on price change
        reAdjust(_poolId, true, _isCooled, _isHeated);

        if (_isAll == true) {
            if (_isCooled == true) {
                _cAmount = ethStakedBalance[_poolId][msg.sender].cBal;
            }
            if (_isHeated == true) {
                _hAmount = ethStakedBalance[_poolId][msg.sender].hBal;
            }
        }

        require(
            _cAmount <= ethStakedBalance[_poolId][msg.sender].cBal &&
                _hAmount <= ethStakedBalance[_poolId][msg.sender].hBal,
            "The amount to withdrawal is greater than the available balance."
        );

        // Withdraw ETH
        if (_cAmount > 0 && _hAmount > 0) {
            // Cooled and Heated
            ethStakedBalance[_poolId][msg.sender].cBal -= _cAmount;
            pool[_poolId].cEthBal -= _cAmount;
            ethStakedBalance[_poolId][msg.sender].hBal -= _hAmount;
            pool[_poolId].hEthBal -= _hAmount;
            payable(msg.sender).transfer(_cAmount + _hAmount);
        } else {
            if (_cAmount > 0 && _hAmount == 0) {
                // Cooled, No Heated
                ethStakedBalance[_poolId][msg.sender].cBal -= _cAmount;
                pool[_poolId].cEthBal -= _cAmount;
                payable(msg.sender).transfer(_cAmount);
            } else if (_cAmount == 0 && _hAmount > 0) {
                // Heated, No Cooled
                ethStakedBalance[_poolId][msg.sender].hBal -= _hAmount;
                pool[_poolId].hEthBal -= _hAmount;
                payable(msg.sender).transfer(_hAmount);
            }
        }

        // Re-Adjust user percentages
        reAdjust(_poolId, false, _isCooled, _isHeated);

        // TEMP until price feed is implemented, don't want to get price again, rather use price from interact()
        pool[_poolId].lastSettledUsdPrice = pool[_poolId].currentUsdPrice;
    }

    /// REMOVE-FROM-ARRAY /// - removes the staker from the array of ETH stakers
    function removeFromArray(uint _poolId, uint index) private {
        ethStakers[_poolId][index] = ethStakers[_poolId][
            ethStakers[_poolId].length - 1
        ];
        ethStakers[_poolId].pop();
    }

    // RE-ADJUST /// - adjusts affected tranche percentages and balances
    function reAdjust(
        uint _poolId,
        bool _beforeTx,
        bool _isCooled,
        bool _isHeated
    ) private {
        if (_beforeTx == true) {
            // BEFORE deposit, only balances are affected based on percentages
            liquidateIfZero(_poolId);
            // ISSUE stakers need removed if they get liquidated (as of now, only one is removed)
            // ISSUE this could likely be optimized to avoid performing the for loops twice when liquidated
            for (
                uint256 ethStakersIndex = 0;
                ethStakersIndex < ethStakers[_poolId].length;
                ethStakersIndex++
            ) {
                address addrC = ethStakers[_poolId][ethStakersIndex];
                ethStakedBalance[_poolId][addrC].cBal =
                    (pool[_poolId].cEthBal *
                        ethStakedBalance[_poolId][addrC].cPercent) /
                    bps;
                ethStakedBalance[_poolId][addrC].hBal =
                    (pool[_poolId].hEthBal *
                        ethStakedBalance[_poolId][addrC].hPercent) /
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
                    ethStakersIndex < ethStakers[_poolId].length;
                    ethStakersIndex++
                ) {
                    address addrC = ethStakers[_poolId][ethStakersIndex];
                    ethStakedBalance[_poolId][addrC].cPercent =
                        (ethStakedBalance[_poolId][addrC].cBal * bps) /
                        pool[_poolId].cEthBal;
                    // Flags index and stores for removal AFTER calculations are finished
                    if (
                        ethStakedBalance[_poolId][addrC].cBal <= 0 &&
                        ethStakedBalance[_poolId][addrC].hBal <= 0
                    ) {
                        indexNeedsRemoved = true;
                        indexToRemove = ethStakersIndex;
                    }
                }
            } else if (_isCooled == false && _isHeated == true) {
                // only Heated tranche percentage numbers are affected by heated tx
                for (
                    uint256 ethStakersIndex = 0;
                    ethStakersIndex < ethStakers[_poolId].length;
                    ethStakersIndex++
                ) {
                    address addrC = ethStakers[_poolId][ethStakersIndex];
                    ethStakedBalance[_poolId][addrC].hPercent =
                        (ethStakedBalance[_poolId][addrC].hBal * bps) /
                        pool[_poolId].hEthBal;
                    // Flags index and stores for removal AFTER calculations are finished
                    if (
                        ethStakedBalance[_poolId][addrC].cBal <= 0 &&
                        ethStakedBalance[_poolId][addrC].hBal <= 0
                    ) {
                        indexNeedsRemoved = true;
                        indexToRemove = ethStakersIndex;
                    }
                }
            } else {
                // Cooled and Heated tranche percentage numbers are affected by tx
                for (
                    uint256 ethStakersIndex = 0;
                    ethStakersIndex < ethStakers[_poolId].length;
                    ethStakersIndex++
                ) {
                    address addrC = ethStakers[_poolId][ethStakersIndex];
                    ethStakedBalance[_poolId][addrC].cPercent =
                        (ethStakedBalance[_poolId][addrC].cBal * bps) /
                        pool[_poolId].cEthBal;
                    ethStakedBalance[_poolId][addrC].hPercent =
                        (ethStakedBalance[_poolId][addrC].hBal * bps) /
                        pool[_poolId].hEthBal;
                    // Flags index and stores for removal AFTER calculations are finished
                    if (
                        ethStakedBalance[_poolId][addrC].cBal <= 0 &&
                        ethStakedBalance[_poolId][addrC].hBal <= 0
                    ) {
                        indexNeedsRemoved = true;
                        indexToRemove = ethStakersIndex;
                    }
                }
            }
            // Remove user if balances are empty, done after calculation so array indexes are not disrupted
            if (indexNeedsRemoved == true) {
                removeFromArray(_poolId, indexToRemove);
            }
        }
    }

    /// LIQUIDATE-IF-ZERO /// - liquidates every user in a zero balance tranche
    function liquidateIfZero(uint _poolId) private {
        for (
            uint256 ethStakersIndex = 0;
            ethStakersIndex < ethStakers[_poolId].length;
            ethStakersIndex++
        ) {
            address addrC = ethStakers[_poolId][ethStakersIndex];
            if (pool[_poolId].cEthBal == 0) {
                // if tranche is liquidated, reset user to zero
                ethStakedBalance[_poolId][addrC].cPercent = 0;
                ethStakedBalance[_poolId][addrC].cBal = 0;
            }
            if (pool[_poolId].hEthBal == 0) {
                // if tranche is liquidated, reset user to zero
                ethStakedBalance[_poolId][addrC].hBal = 0;
                ethStakedBalance[_poolId][addrC].hPercent = 0;
            }
        }
    }

    /// VIEW-BALANCE-FUNCTIONS /// - check balances

    function retrieveCurrentUsdPrice(uint _poolId) public view returns (uint) {
        (, int256 price, , , ) = ethUsdPriceFeed.latestRoundData();
        return uint(price);
    }

    function retrieveEthInContract() public view returns (uint) {
        return address(this).balance;
    }

    function retrieveCEthPercentBalance(uint _poolId, address _user)
        public
        view
        returns (uint)
    {
        return ethStakedBalance[_poolId][_user].cPercent;
    }

    function retrieveHEthPercentBalance(uint _poolId, address _user)
        public
        view
        returns (uint)
    {
        return ethStakedBalance[_poolId][_user].hPercent;
    }

    function retrieveCEthBalance(uint _poolId, address _user)
        public
        view
        returns (uint)
    {
        return ethStakedBalance[_poolId][_user].cBal;
    }

    function retrieveHEthBalance(uint _poolId, address _user)
        public
        view
        returns (uint)
    {
        return ethStakedBalance[_poolId][_user].hBal;
    }

    function retrieveAddressAtIndex(uint _poolId, uint _index)
        public
        view
        returns (address)
    {
        return ethStakers[_poolId][_index];
    }

    function retrieveProtocolCEthBalance(uint _poolId)
        public
        view
        returns (uint)
    {
        return pool[_poolId].cEthBal;
    }

    function retrieveProtocolHEthBalance(uint _poolId)
        public
        view
        returns (uint)
    {
        return pool[_poolId].hEthBal;
    }

    function retrieveProtocolEthPrice(
        uint _poolId //FIX
    ) public view returns (uint, uint) {
        return (
            pool[_poolId].currentUsdPrice,
            pool[_poolId].lastSettledUsdPrice
        );
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
    //     pool[_poolId].hEthBal = _hEthAll * decimals;
    //     pool[_poolId].cEthBal = _cEthAll * decimals;
    //     pEthBal = (_hEthAll + _cEthAll) * decimals;
    //     pool[_poolId].lastSettledUsdPrice = _startPrice * usdDecimals;
    //     pool[_poolId].currentUsdPrice = _endPrice * usdDecimals;
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
    function getProfit(uint _poolId, uint256 _currentUsdPrice)
        public
        view
        returns (int256)
    {
        int256 profit = ((int(_currentUsdPrice) -
            int(pool[_poolId].lastSettledUsdPrice)) * int(bps)) /
            int(pool[_poolId].lastSettledUsdPrice);
        return profit;
    }

    /// TRANCHE SPECIFIC CALCS /// - calculates allocation difference for a tranche (also avoids 'stack too deep' error)
    function trancheSpecificCalcs(
        uint _poolId,
        bool _isCooled,
        int256 _assetUsdProfit,
        uint256 _currentAssetUsd
    ) private view returns (int256, int256) {
        // TEMP
        // require(
        //     pool[_poolId].cEthBal > 0 || pool[_poolId].hEthBal > 0, // in Wei
        //     "Protocol must have funds in order to settle."
        // );
        uint256 trancheBal;
        int256 r;
        // get tranche balance and basis points for expected return
        if (_isCooled == true) {
            trancheBal = pool[_poolId].cEthBal; // in Wei
            // CHANGE to variable
            r = -50_0000000000; // basis points
        } else {
            trancheBal = pool[_poolId].hEthBal; // in Wei
            // CHANGE to variable
            r = 50_0000000000; // basis points
        }
        // TEMP
        // require(trancheBal > 0, "Tranche must have a balance.");
        require(
            // CHANGE to variable
            r == -50_0000000000 || r == 50_0000000000,
            "Tranche must have a valid multiplier value."
        );
        int256 trancheChange = (int(trancheBal) * int(_currentAssetUsd)) -
            (int(trancheBal) * int(pool[_poolId].lastSettledUsdPrice));
        // CHANGE to variable
        int256 expectedPayout = (trancheChange * ((1 * int(bps)) + r)) /
            int(bps);
        int256 allocationDifference = expectedPayout - trancheChange;
        allocationDifference = allocationDifference / int(decimals);
        return (allocationDifference, trancheChange);
    }

    /// INTERACT /// - rebalances the cooled and heated tranches
    function interact(uint _poolId) private {
        uint256 currentAssetUsd = retrieveCurrentUsdPrice(_poolId);
        pool[_poolId].currentUsdPrice = currentAssetUsd;
        int256 assetUsdProfit = getProfit(_poolId, currentAssetUsd); // returns ETH/USD profit in terms of basis points
        // find expected return and use it to calculate allocation difference for each tranche
        (
            int256 cooledAllocationDiff,
            int256 cooledChange
        ) = trancheSpecificCalcs(
                _poolId,
                true,
                assetUsdProfit,
                currentAssetUsd
            );
        (
            int256 heatedAllocationDiff,
            int256 heatedChange
        ) = trancheSpecificCalcs(
                _poolId,
                false,
                assetUsdProfit,
                currentAssetUsd
            );
        // CHECK moved this, make sure it still works
        uint256 percentCooledTranche = ((pool[_poolId].cEthBal * bps) /
            (pool[_poolId].cEthBal + pool[_poolId].hEthBal));
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
            uint256 nonNaturalMultiplier = assetUsdProfit > 0
                ? percentCooledTranche
                : ((1 * bps) - percentCooledTranche);
            uint256 adjNonNaturalDiff = (uint(abs(nonNaturalDifference)) *
                nonNaturalMultiplier) / bps;
            absAllocationTotal = uint(minAbsAllocation) + adjNonNaturalDiff;
        }
        // calculate the actual allocation for the cooled tranche
        int256 cooledAllocation;
        if (cooledAllocationDiff < 0) {
            if (
                // the cEthBal USD value - absAllocation (in usdDecimals)
                int((pool[_poolId].cEthBal * currentAssetUsd) / decimals) -
                    int(absAllocationTotal) >
                0
            ) {
                cooledAllocation = -int(absAllocationTotal);
            } else {
                cooledAllocation = int(
                    (pool[_poolId].cEthBal * currentAssetUsd) / decimals
                ); // the cEthBal USD value (in UsDecimals * Decimals)
            }
        } else {
            if (
                int((pool[_poolId].hEthBal * currentAssetUsd) / decimals) -
                    int(absAllocationTotal) >
                0
            ) {
                cooledAllocation = int(absAllocationTotal); // absolute allocation in UsDecimals
            } else {
                cooledAllocation = int(
                    (pool[_poolId].hEthBal * currentAssetUsd) / decimals
                );
            }
        }
        // needed variables: currentAssetUsd, cooledChange, cooledAllocation
        // heated allocation is the inverse of the cooled allocation

        reallocate(_poolId, currentAssetUsd, cooledChange, cooledAllocation); // reallocate the protocol ETH according to price movement
    }

    /// REALLOCATE /// - uses the USD values to calculate ETH balances of tranches
    function reallocate(
        uint _poolId,
        uint256 _currentAssetUsd, // in usdDecimal form
        int _cooledChange,
        int _cooledAllocation
    ) private {
        uint256 totalLockedUsd = ((pool[_poolId].cEthBal +
            pool[_poolId].hEthBal) * _currentAssetUsd) / decimals; // USD balance of protocol in usdDecimal terms
        int256 cooledBalAfterAllocation = ((int(
            pool[_poolId].cEthBal * pool[_poolId].lastSettledUsdPrice
        ) + _cooledChange) / int(decimals)) + _cooledAllocation;
        int256 heatedBalAfterAllocation = int(totalLockedUsd) - // heated USD balance in usdDecimal terms
            cooledBalAfterAllocation;
        pool[_poolId].cEthBal =
            (uint(cooledBalAfterAllocation) * decimals) /
            _currentAssetUsd; // new cEth Balance in Wei
        pool[_poolId].hEthBal =
            (uint(heatedBalAfterAllocation) * decimals) /
            _currentAssetUsd; // new hEth Balance in Wei
    }

    /// ABSOLUTE-VALUE /// - returns the absolute value of an int
    function abs(int x) private pure returns (int) {
        return x >= 0 ? x : -x;
    }

    // /// SIMULATE INTERACT /// - view only of simulated rebalance of the cooled and heated tranches
    function simulateInteract(uint _poolId, uint _simAssetUsd)
        public
        view
        returns (uint, uint)
    {
        int256 assetUsdProfit = getProfit(_poolId, _simAssetUsd); // returns ETH/USD profit in terms of basis points
        // find expected return and use it to calculate allocation difference for each tranche
        (
            int256 cooledAllocationDiff,
            int256 cooledChange
        ) = trancheSpecificCalcs(_poolId, true, assetUsdProfit, _simAssetUsd);
        (
            int256 heatedAllocationDiff,
            int256 heatedChange
        ) = trancheSpecificCalcs(_poolId, false, assetUsdProfit, _simAssetUsd);
        // CHECK moved this, make sure it still works
        uint256 percentCooledTranche = ((pool[_poolId].cEthBal * bps) /
            (pool[_poolId].cEthBal + pool[_poolId].hEthBal));
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
            uint256 nonNaturalMultiplier = assetUsdProfit > 0
                ? percentCooledTranche
                : ((1 * bps) - percentCooledTranche);
            uint256 adjNonNaturalDiff = (uint(abs(nonNaturalDifference)) *
                nonNaturalMultiplier) / bps;
            absAllocationTotal = uint(minAbsAllocation) + adjNonNaturalDiff;
        }

        // needed variables: _simAssetUsd, cooledChange, cooledAllocation
        // heated allocation is the inverse of the cooled allocation

        return
            simulateReallocate(
                _poolId,
                _simAssetUsd,
                cooledChange,
                cooledAllocationDiff,
                absAllocationTotal
            ); // reallocate the protocol ETH according to price movement
    }

    /// REALLOCATE /// - uses the USD values to calculate ETH balances of tranches
    function simulateReallocate(
        uint _poolId,
        uint256 _simAssetUsd, // in usdDecimal form
        int _cooledChange,
        int _cooledAllocationDiff,
        uint _absAllocationTotal
    ) private view returns (uint, uint) {
        // calculate the actual allocation for the cooled tranche
        int256 cooledAllocation;
        if (_cooledAllocationDiff < 0) {
            if (
                // the cEthBal USD value - absAllocation (in usdDecimals)
                int((pool[_poolId].cEthBal * _simAssetUsd) / decimals) -
                    int(_absAllocationTotal) >
                0
            ) {
                cooledAllocation = -int(_absAllocationTotal);
            } else {
                cooledAllocation = int(
                    (pool[_poolId].cEthBal * _simAssetUsd) / decimals
                ); // the cEthBal USD value (in UsDecimals * Decimals)
            }
        } else {
            if (
                int((pool[_poolId].hEthBal * _simAssetUsd) / decimals) -
                    int(_absAllocationTotal) >
                0
            ) {
                cooledAllocation = int(_absAllocationTotal); // absolute allocation in UsDecimals
            } else {
                cooledAllocation = int(
                    (pool[_poolId].hEthBal * _simAssetUsd) / decimals
                );
            }
        }
        uint256 totalLockedUsd = ((pool[_poolId].cEthBal +
            pool[_poolId].hEthBal) * _simAssetUsd) / decimals; // USD balance of protocol in usdDecimal terms
        int256 cooledBalAfterAllocation = ((int(
            pool[_poolId].cEthBal * pool[_poolId].lastSettledUsdPrice
        ) + _cooledChange) / int(decimals)) + cooledAllocation;
        int256 heatedBalAfterAllocation = int(totalLockedUsd) - // heated USD balance in usdDecimal terms
            cooledBalAfterAllocation;
        uint cEthSimBal = (uint(cooledBalAfterAllocation) * decimals) /
            _simAssetUsd; // new cEth Balance in Wei
        uint hEthSimBal = (uint(heatedBalAfterAllocation) * decimals) /
            _simAssetUsd; // new hEth Balance in Wei
        return (hEthSimBal, cEthSimBal);
    }

    // function getRangeOfReturns(
    //     uint _poolId,
    //     address _address,
    //     bool _isCooled,
    //     bool _isHeated,
    //     bool _isAll
    // ) public view returns (int[] memory) {
    //     uint assetUsdPrice = retrieveCurrentUsdPrice(_poolId);
    //     int currentPercent = -50_0000000000;
    //     int assetUsdAtIndex;
    //     int[] memory estBals = new int[](11);
    //     for (uint index = 0; index < 11; index++) {
    //         assetUsdAtIndex =
    //             (int(assetUsdPrice) * (int(bps) + currentPercent)) /
    //             int(bps);
    //         uint hBalEst;
    //         uint cBalEst;
    //         uint data = (_poolId * decimals) + assetUsdPrice; // storing multiple values in a uint
    //         (hBalEst, cBalEst) = simulateInteract(data);
    //         uint balanceRequested;
    //         if (_isHeated == true || _isAll == true) {
    //             balanceRequested =
    //                 (hBalEst * ethStakedBalance[_poolId][_address].hPercent) /
    //                 bps;
    //         }
    //         if (_isCooled == true || _isAll == true) {
    //             balanceRequested +=
    //                 (cBalEst * ethStakedBalance[_poolId][_address].cPercent) /
    //                 bps;
    //         }
    //         estBals[index] = int(balanceRequested);
    //         currentPercent += 10_0000000000;
    //     }

    //     return (estBals);
    // }
}
