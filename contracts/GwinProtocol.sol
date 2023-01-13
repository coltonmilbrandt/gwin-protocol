// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

/// @author Colton Milbrandt
/// @title Gwin, Risk-Tranche AMM
contract GwinProtocol is Ownable, ReentrancyGuard {
    // pool ID -> user address -> user balances struct
    mapping(uint256 => mapping(address => Bal)) public ethStakedBalance;
    // parentID -> user adddress -> user balances struct
    mapping(uint256 => mapping(address => ParentBal))
        public ethStakedWithParent;
    // token address -> staker address -> amount
    mapping(address => mapping(address => uint256)) public stakingBalance;
    // staker address -> unique tokens staked
    mapping(address => uint256) public uniquePositions;
    // pool ID    ->   address  ->  isUnique
    mapping(uint256 => mapping(address => bool)) public isUniqueEthStaker;
    // aggregator key -> aggregator
    mapping(bytes32 => AggregatorV3Interface) public aggregators;
    // aggreagator key -> feed decimals
    mapping(bytes32 => uint8) public currencyKeyDecimals;
    // List of aggregator keys for convenient iteration
    bytes32[] public aggregatorKeys;
    //    pool ID --> struct
    mapping(uint256 => Pool) public pool;
    //    pool ID --> parent pool
    mapping(uint256 => ParentPoolBal) public parentPoolBal;
    //    pool ID -> parent pool ID
    mapping(uint256 => uint256) public parentPoolId;
    // parent pool ID -> child pool IDs
    mapping(uint256 => Pool) public parentPoolChildren;
    // pool ID --> array of ETH stakers
    mapping(uint256 => address[]) public ethStakers;
    // array of stakers
    address[] public stakers;
    // array of the allowed tokens
    address[] public allowedTokens;
    // array of pool IDs
    uint256[] public poolIds;

    // ********* Decimal Values *********
    uint256 decimals = 10**18;
    uint8 usdDecimalsUint = 8;
    uint256 usdDecimals = 10**usdDecimalsUint;
    uint256 bps = 10**12;

    // ************* Values *************
    uint256 newPoolId = 0;

    // ************* Structs *************
    struct Pool {
        uint256 id;
        uint256 parentId;
        uint256 lastSettledUsdPrice;
        uint256 currentUsdPrice;
        bytes32 basePriceFeedKey;
        bytes32 quotePriceFeedKey;
        uint256 hEthBal;
        uint256 cEthBal;
        int256 hRate;
        int256 cRate;
        uint8 poolType; // as in classic (0) or modified (1)
    }

    struct PoolWithBalances {
        uint256 id;
        uint256 parentId;
        uint256 lastSettledUsdPrice;
        uint256 currentPrice;
        bytes32 basePriceFeedKey;
        bytes32 quotePriceFeedKey;
        uint256 hEthBal;
        uint256 cEthBal;
        int256 hRate;
        int256 cRate;
        uint256 hHealth;
        uint256 cHealth;
        uint8 poolType;
        uint256 cBalancePreview;
        uint256 hBalancePreview;
        uint256 userCEthBalPreview;
        uint256 userHEthBalPreview;
    }

    struct ParentPoolBal {
        uint256 cEthBal;
        uint256 hEthBal;
        uint256[] childPoolIds;
    }

    struct Bal {
        uint256 cBal;
        uint256 cPercent;
        uint256 hBal;
        uint256 hPercent;
    }

    struct ParentBal {
        uint256 cBal;
        uint256 cPercent;
    }

    IERC20 public gwinToken;

    constructor(address _gwinTokenAddress, address _link) public {
        gwinToken = IERC20(_gwinTokenAddress);
    }

    /// @notice Initialize a pool pair or initialize a pool connected to a parent
    /// @dev This function auto balances the pools, but in the future, allowing flexibility makes more sense
    /// @param _type The type of pool, 0 for classic, 1 for modified
    /// @param _parentId The ID of the parent pool you are connecting with, or 0 for none
    /// @param _basePriceFeedAddress The contract address of the base price feed
    /// @param _baseCurrencyKey A base32 value that represents the price feed's pair, i.e. "ETH/USD"
    /// @param _quotePriceFeedAddress The contract address of the quote price feed
    /// @param _quoteCurrencyKey A base32 value that represents the price feed's pair, i.e. "XAU/USD"
    /// @param _cRate A negative percent value followed by 10 decimals, i.e. -100_0000000000
    /// @param _hRate A positive percent value followed by 10 decimals, i.e. 100_0000000000
    function initializePool(
        uint8 _type,
        uint8 _parentId,
        address _basePriceFeedAddress,
        bytes32 _baseCurrencyKey,
        address _quotePriceFeedAddress,
        bytes32 _quoteCurrencyKey,
        int256 _cRate,
        int256 _hRate
    ) external payable returns (uint256) {
        poolIds.push(newPoolId);
        pool[newPoolId].id = newPoolId;
        pool[newPoolId].poolType = _type;
        require(
            pool[newPoolId].cEthBal == 0 && pool[newPoolId].hEthBal == 0,
            "The Protocol already has funds deposited."
        );
        require(_cRate < 0 && _hRate > 0, "Rates_Must_Oppose"); // rates should be opposite to function
        // add depositor to ethStakers[]
        if (isUniqueEthStaker[newPoolId][msg.sender] == false) {
            ethStakers[newPoolId].push(msg.sender);
            isUniqueEthStaker[newPoolId][msg.sender] = true;
        }
        // set cooled rate and heated rate (leverage)
        pool[newPoolId].cRate = _cRate;
        pool[newPoolId].hRate = _hRate;
        // set bytes32 keys/labels for price feeds
        pool[newPoolId].basePriceFeedKey = _baseCurrencyKey;
        pool[newPoolId].quotePriceFeedKey = _quoteCurrencyKey;
        // set deposit amounts according to pool weight or split for type "0"
        uint256 hDepositAmount;
        uint256 cDepositAmount;
        // if modified type (i.e. "1")
        if (_type != 0) {
            cDepositAmount = msg.value / 2;
            hDepositAmount = msg.value / 2;
        } else {
            // if classic type (i.e. "0")
            int256 cEthPercent = (abs(_hRate) * int256(bps)) /
                (abs(_hRate) + abs(_cRate));
            cDepositAmount = (msg.value * uint256(cEthPercent)) / bps;
            hDepositAmount = msg.value - cDepositAmount;
        }
        // track deposit amounts and set weight
        ethStakedBalance[newPoolId][msg.sender].hBal += hDepositAmount;
        ethStakedBalance[newPoolId][msg.sender].hPercent = bps;
        pool[newPoolId].hEthBal = hDepositAmount;
        pool[newPoolId].cEthBal = cDepositAmount;
        pool[newPoolId].parentId = _parentId;
        parentPoolId[newPoolId] = _parentId;
        // add price feed(s)
        addAggregator(_baseCurrencyKey, _basePriceFeedAddress);
        if (_quotePriceFeedAddress != address(0x0)) {
            addAggregator(_quoteCurrencyKey, _quotePriceFeedAddress);
        }
        // initialize current price and last price values
        pool[newPoolId].currentUsdPrice = retrieveCurrentPrice(newPoolId);
        pool[newPoolId].lastSettledUsdPrice = pool[newPoolId].currentUsdPrice;
        if (_parentId != 0) {
            // set parent pool balances and weights
            parentPoolBal[_parentId].childPoolIds.push(newPoolId);
            parentPoolBal[_parentId].cEthBal += cDepositAmount;
            parentPoolBal[_parentId].hEthBal += hDepositAmount;
            ethStakedWithParent[_parentId][msg.sender].cBal += cDepositAmount;
            ethStakedWithParent[_parentId][msg.sender].cPercent =
                (ethStakedWithParent[_parentId][msg.sender].cBal * bps) /
                parentPoolBal[_parentId].cEthBal;
            if (parentPoolBal[_parentId].childPoolIds.length > 1) {
                // Re-Adjust user percentages
                reAdjust(newPoolId, false, true, false);
                // Balance allocations optimally to child pools
                reAdjustChildPools(newPoolId);
            }
        } else {
            // if not using a cooled parent pool, track cooled balances for each pool
            ethStakedBalance[newPoolId][msg.sender].cBal += cDepositAmount;
            ethStakedBalance[newPoolId][msg.sender].cPercent = bps;
        }
        newPoolId++;
        return newPoolId - 1;
    }

    /// @notice Deposit to cooled or heated tranche, or both
    /// @param _poolId The ID of the target pool
    /// @param _isCooled Bool value representing whether it's a cooled deposit
    /// @param _isHeated Bool value representing whether it's a heated deposit
    /// @param _cAmount Cooled deposit amount in Wei
    /// @param _hAmount Heated deposit amount in Wei
    function depositToTranche(
        uint256 _poolId,
        bool _isCooled,
        bool _isHeated,
        uint256 _cAmount,
        uint256 _hAmount
    ) external payable {
        require(
            pool[_poolId].basePriceFeedKey != 0x0,
            "Pool_Is_Not_Initialized"
        );
        require(msg.value > 0, "Amount must be greater than zero.");
        require(_isCooled == true || _isHeated == true);
        require(_cAmount + _hAmount <= msg.value);
        uint256 parentId = parentPoolId[_poolId];

        // Interact to rebalance Tranches with new price feed value
        interactByPool(_poolId);
        // Re-adjust to update user balances after price change
        reAdjust(_poolId, true, _isCooled, _isHeated);
        // Deposit ETH
        if (_isCooled == true && _isHeated == false) {
            pool[_poolId].cEthBal += msg.value;
            if (parentPoolId[_poolId] != 0) {
                // add to parent balance
                ethStakedWithParent[parentId][msg.sender].cBal += msg.value;
                parentPoolBal[parentId].cEthBal += msg.value;
            } else {
                ethStakedBalance[_poolId][msg.sender].cBal += msg.value;
            }
        } else if (_isCooled == false && _isHeated == true) {
            pool[_poolId].hEthBal += msg.value;
            ethStakedBalance[_poolId][msg.sender].hBal += msg.value;
            if (parentPoolId[_poolId] != 0) {
                // add to parent balance
                parentPoolBal[parentId].hEthBal += msg.value;
            }
        } else if (_isCooled == true && _isHeated == true) {
            pool[_poolId].cEthBal += _cAmount;
            if (parentPoolId[_poolId] != 0) {
                // add to parent balance
                ethStakedWithParent[parentId][msg.sender].cBal += _cAmount;
                parentPoolBal[parentId].cEthBal += _cAmount;
            } else {
                ethStakedBalance[_poolId][msg.sender].cBal += _cAmount;
            }
            ethStakedBalance[_poolId][msg.sender].hBal += _hAmount;
            pool[_poolId].hEthBal += _hAmount;
            if (parentPoolId[_poolId] != 0) {
                // add to parent balance
                parentPoolBal[parentId].hEthBal += _hAmount;
            }
        }
        if (isUniqueEthStaker[_poolId][msg.sender] == false) {
            ethStakers[_poolId].push(msg.sender);
            isUniqueEthStaker[_poolId][msg.sender] = true;
        }
        // Re-Adjust user percentages
        reAdjust(_poolId, false, _isCooled, _isHeated);
        // Re-Adjust all cooled child pool weights optimally
        reAdjustChildPools(_poolId);
    }

    /// @notice Withdraw from cooled or heated tranche, or both
    /// @dev Further testing on withdraw all would be prudent
    /// @param _poolId The ID of the target pool
    /// @param _isCooled Bool value representing whether it's a cooled withdrawal
    /// @param _isHeated Bool value representing whether it's a heated withdrawal
    /// @param _cAmount Cooled withdrawal amount in Wei
    /// @param _hAmount Heated withdrawal amount in Wei
    /// @param _isAll Bool value representing whether all funds are withdrawn
    function withdrawFromTranche(
        uint256 _poolId,
        bool _isCooled,
        bool _isHeated,
        uint256 _cAmount,
        uint256 _hAmount,
        bool _isAll
    ) external nonReentrant {
        if (_isAll == false) {
            require(_cAmount > 0 || _hAmount > 0, "Zero_Withdrawal_Amount");
        }
        require(_isCooled == true || _isHeated == true);
        uint256 parentId = parentPoolId[_poolId];

        // Interact to rebalance Tranches with new price feed value
        interactByPool(_poolId);
        // Re-adjust the user balances based on price change
        reAdjust(_poolId, true, _isCooled, _isHeated);

        // if withdrawing all, set amount according to pool or parent pool user balance
        if (_isAll == true) {
            if (_isCooled == true) {
                if (parentPoolId[_poolId] != 0) {
                    _cAmount = ethStakedWithParent[parentId][msg.sender].cBal;
                    require(
                        _cAmount <=
                            ethStakedWithParent[parentId][msg.sender].cBal,
                        "Insufficient_User_Funds"
                    );
                } else {
                    _cAmount = ethStakedBalance[_poolId][msg.sender].cBal;
                    require(
                        _cAmount <= ethStakedBalance[_poolId][msg.sender].cBal,
                        "Insufficient_User_Funds"
                    );
                }
            }
            if (_isHeated == true) {
                _hAmount = ethStakedBalance[_poolId][msg.sender].hBal;
                require(
                    _hAmount <= ethStakedBalance[_poolId][msg.sender].hBal,
                    "Insufficient_User_Funds"
                );
            }
        }
        // Withdraw ETH
        if (_cAmount > 0 && _hAmount > 0) {
            // Cooled and Heated
            pool[_poolId].cEthBal -= _cAmount;
            if (parentPoolId[_poolId] != 0) {
                // deduct from parent balance
                ethStakedWithParent[parentId][msg.sender].cBal -= _cAmount;
                parentPoolBal[parentId].cEthBal -= _cAmount;
            } else {
                ethStakedBalance[_poolId][msg.sender].cBal -= _cAmount;
            }
            ethStakedBalance[_poolId][msg.sender].hBal -= _hAmount;
            if (parentPoolId[_poolId] != 0) {
                parentPoolBal[parentId].hEthBal -= _hAmount;
            }
            pool[_poolId].hEthBal -= _hAmount;
            payable(msg.sender).transfer(_cAmount + _hAmount);
        } else {
            if (_cAmount > 0 && _hAmount == 0) {
                // Cooled, No Heated
                if (parentPoolId[_poolId] != 0) {
                    // deduct from user's parent balance
                    ethStakedWithParent[parentId][msg.sender].cBal -= _cAmount;
                    // deduct from parent balance
                    parentPoolBal[parentId].cEthBal -= _cAmount;
                } else {
                    // deduct from user's pool balance
                    ethStakedBalance[_poolId][msg.sender].cBal -= _cAmount;
                    // adjust singular pool cEth bal ONLY IF not part of parent pool
                    pool[_poolId].cEthBal -= _cAmount;
                }
                payable(msg.sender).transfer(_cAmount);
            } else if (_cAmount == 0 && _hAmount > 0) {
                // Heated, No Cooled
                ethStakedBalance[_poolId][msg.sender].hBal -= _hAmount;
                if (parentPoolId[_poolId] != 0) {
                    parentPoolBal[parentId].hEthBal -= _hAmount;
                }
                pool[_poolId].hEthBal -= _hAmount;
                payable(msg.sender).transfer(_hAmount);
            }
        }

        // Re-Adjust user percentages
        reAdjust(_poolId, false, _isCooled, _isHeated);
        // Re-Adjust all cooled child pool weights optimally
        reAdjustChildPools(_poolId);
    }

    // Public functions

    /// @notice Preview user balance of a pool at the current price
    /// @param _poolId The ID of the target pool
    /// @return uint256 Preview of user heated balance at current price
    /// @return uint256 Preview of user cooled balance at current price
    function previewUserBalance(uint256 _poolId)
        public
        view
        returns (uint256, uint256)
    {
        uint256 heatedBalance;
        uint256 cooledBalance;
        // simulate interaction to preview heated and cooled balances at current price
        (heatedBalance, cooledBalance) = simulateInteract(
            _poolId,
            retrieveCurrentPrice(_poolId)
        );
        // derive user balance by percent pool ownership
        uint256 userHeatedBalance = (heatedBalance *
            ethStakedBalance[_poolId][msg.sender].hPercent) / bps;
        uint256 userCooledBalance = (cooledBalance *
            ethStakedBalance[_poolId][msg.sender].cPercent) / bps;
        return (userHeatedBalance, userCooledBalance);
    }

    /// @notice Get the current price from feed
    /// @param _poolId The ID of the target pool
    /// @return uint256 Current price from Chainlink price feed
    function retrieveCurrentPrice(uint256 _poolId)
        public
        view
        returns (uint256)
    {
        // pool's priceFeedAddress is fed into the AggregatorV3Interface
        require(
            pool[_poolId].basePriceFeedKey != 0x0,
            "Pool_Is_Not_Initialized"
        );
        int256 price;
        if (pool[_poolId].quotePriceFeedKey == 0x0) {
            bytes32 aggregatorKey = pool[_poolId].basePriceFeedKey;
            address aggregatorAddress = address(aggregators[aggregatorKey]);
            AggregatorV3Interface priceFeed = AggregatorV3Interface(
                aggregatorAddress
            );
            (
                ,
                /*uint80 roundID*/
                price, /*uint startedAt*/ /*uint timeStamp*/ /*uint80 answeredInRound*/
                ,
                ,

            ) = priceFeed.latestRoundData();
            // set number of decimals for token value
            uint256 priceFeedDecimals = 10**priceFeed.decimals();
            uint256 decimalDifference;
            if (priceFeedDecimals > usdDecimals) {
                // convert to native decimals for math
                decimalDifference = priceFeedDecimals / usdDecimals;
                price = price / int256(decimalDifference);
            } else if (priceFeedDecimals < usdDecimals) {
                decimalDifference = usdDecimals / priceFeedDecimals;
                price = price * int256(decimalDifference);
            }
            // return token price
            return uint256(price);
        } else {
            price = getDerivedPrice(
                address(aggregators[pool[_poolId].basePriceFeedKey]),
                address(aggregators[pool[_poolId].quotePriceFeedKey]),
                uint8(usdDecimalsUint)
            );
            return uint256(price);
        }
    }

    /// @notice Get derived price based on dual price feeds
    /// @param _base The base price feed contract address
    /// @param _quote The quote price feed contract address
    /// @param _decimals The number of decimals for value
    /// @return int256 Derived price feed value
    function getDerivedPrice(
        address _base,
        address _quote,
        uint8 _decimals
    ) public view returns (int256) {
        // use two price feeds to derive a new feed
        require(
            _decimals > uint8(0) && _decimals <= uint8(18),
            "Invalid _decimals"
        );
        int256 feedDecimals = int256(10**uint256(_decimals));
        (, int256 basePrice, , , ) = AggregatorV3Interface(_base)
            .latestRoundData();
        uint8 baseDecimals = AggregatorV3Interface(_base).decimals();
        basePrice = scalePrice(basePrice, baseDecimals, _decimals);

        (, int256 quotePrice, , , ) = AggregatorV3Interface(_quote)
            .latestRoundData();
        uint8 quoteDecimals = AggregatorV3Interface(_quote).decimals();
        quotePrice = scalePrice(quotePrice, quoteDecimals, _decimals);

        return (basePrice * feedDecimals) / quotePrice; //
    }

    /// @notice Get last settled value of ETH in contract
    /// @return uint256 Amount of ETH in contract
    function retrieveEthInContract() public view returns (uint256) {
        return address(this).balance;
    }

    /// @notice Get user last settled percent of single cEth pool
    /// @return uint256 User percent ownership of cEth pool
    function retrieveCEthPercentBalance(uint256 _poolId, address _user)
        public
        view
        returns (uint256)
    {
        return ethStakedBalance[_poolId][_user].cPercent;
    }

    /// @notice Get user last settled percent of single hEth pool
    /// @return uint256 User percent ownership of hEth pool
    function retrieveHEthPercentBalance(uint256 _poolId, address _user)
        public
        view
        returns (uint256)
    {
        return ethStakedBalance[_poolId][_user].hPercent;
    }

    /// @notice Get user last settled balance in single cEth pool
    /// @return uint256 User balance in cEth pool
    function retrieveCEthBalance(uint256 _poolId, address _user)
        public
        view
        returns (uint256)
    {
        return ethStakedBalance[_poolId][_user].cBal;
    }

    /// @notice Get user last settled balance in single hEth pool
    /// @return uint256 User balance in hEth pool
    function retrieveHEthBalance(uint256 _poolId, address _user)
        public
        view
        returns (uint256)
    {
        // derive balance by percent
        uint256 perc = retrieveHEthPercentBalance(_poolId, _user);
        uint256 bal = retrieveProtocolHEthBalance(_poolId);
        return (bal * perc) / bps;
    }

    // USER - address at index of stakers array
    /// @notice Get address at index of stakers array
    /// @param _poolId The pool ID target
    /// @param _index The index of the array
    /// @return address address at index of stakers array
    function retrieveAddressAtIndex(uint256 _poolId, uint256 _index)
        public
        view
        returns (address)
    {
        return ethStakers[_poolId][_index];
    }

    /// @notice Get balance of cEth pool
    /// @param _poolId The pool ID
    /// @return uint256 The balance of cEth pool
    function retrieveProtocolCEthBalance(uint256 _poolId)
        public
        view
        returns (uint256)
    {
        return pool[_poolId].cEthBal;
    }

    /// @notice Get user balance in parent cEth pool
    /// @param _poolId The pool ID
    /// @param _user The address of the user
    /// @return uint256 The user balance in the parent cEth pool
    function getParentUserCEthBalance(uint256 _poolId, address _user)
        public
        view
        returns (uint256)
    {
        uint256 perc = getParentUserCEthPercent(_poolId, _user);
        uint256 bal = getParentPoolCEthBalance(_poolId);
        return (bal * perc) / bps;
    }

    /// @notice Get user percent ownership of parent pool
    /// @param _poolId The pool ID
    /// @param _user The address of the user
    /// @return uint256 The user percent ownership of parent pool
    function getParentUserCEthPercent(uint256 _poolId, address _user)
        public
        view
        returns (uint256)
    {
        uint256 parentId = parentPoolId[_poolId];
        return ethStakedWithParent[parentId][_user].cPercent;
    }

    /// @notice Get cEth balance in parent pool
    /// @param _poolId The pool ID
    /// @return uint256 The overall cEth balance in parent pool
    function getParentPoolCEthBalance(uint256 _poolId)
        public
        view
        returns (uint256)
    {
        uint256 parentId = parentPoolId[_poolId];
        return parentPoolBal[parentId].cEthBal;
    }

    /// @notice Get hEth balance in parent pool
    /// @param _poolId The pool ID
    /// @return uint256 The overall hEth balance in parent pool
    function getParentPoolHEthBalance(uint256 _poolId)
        public
        view
        returns (uint256)
    {
        uint256 parentId = parentPoolId[_poolId];
        return parentPoolBal[parentId].hEthBal;
    }

    /// @notice Get hEth balance in pool
    /// @param _poolId The pool ID
    /// @return uint256 The overall hEth balance in pool
    function retrieveProtocolHEthBalance(uint256 _poolId)
        public
        view
        returns (uint256)
    {
        return pool[_poolId].hEthBal;
    }

    /// @notice Get current and last settled prices for pool
    /// @param _poolId The pool ID
    /// @return uint256 The current price recorded
    /// @return uint256 The last settled price recorded
    function retrieveProtocolEthPrice(uint256 _poolId)
        public
        view
        returns (uint256, uint256)
    {
        return (
            pool[_poolId].currentUsdPrice,
            pool[_poolId].lastSettledUsdPrice
        );
    }

    /// @notice Get user cEth balance preview at current price
    /// @param _poolId The pool ID
    /// @param _user The user's address
    /// @return uint256 The user's cEth balance preview
    function previewUserCEthBalance(uint256 _poolId, address _user)
        public
        view
        returns (uint256)
    {
        uint256 userCooledBal;
        userCooledBal = previewUserCEthBalanceAtPrice(
            _poolId,
            retrieveCurrentPrice(_poolId),
            _user
        );
        return userCooledBal;
    }

    /// @notice Get user cETH balance preview at selected price
    /// @param _poolId The pool ID
    /// @param _price The price you want to use to estimate balance
    /// @param _user The user's address
    /// @return uint256 The user's cEth balance preview at selected price
    function previewUserCEthBalanceAtPrice(
        uint256 _poolId,
        uint256 _price,
        address _user
    ) public view returns (uint256) {
        uint256 hEthBalEst;
        uint256 cEthBalEst;
        (hEthBalEst, cEthBalEst) = previewPoolBalancesAtPrice(_poolId, _price);
        // Percents provide accurate balance
        uint256 perc = retrieveCEthPercentBalance(_poolId, _user);
        uint256 bal = cEthBalEst;
        return (bal * perc) / bps;
    }

    /// @notice Get user hEth balance preview at current price
    /// @param _poolId The pool ID
    /// @param _user The user's address
    /// @return uint256 The user hEth balance preview at current price
    function previewUserHEthBalance(uint256 _poolId, address _user)
        public
        view
        returns (uint256)
    {
        uint256 userHeatedBal;
        userHeatedBal = previewUserHEthBalanceAtPrice(
            _poolId,
            retrieveCurrentPrice(_poolId),
            _user
        );
        return userHeatedBal;
    }

    /// @notice Get user cEth balance preview at current price
    /// @param _poolId The pool ID
    /// @param _user The user's address
    /// @return uint256 The user cEth balance preview at current price
    function previewParentUserCEthBalance(uint256 _poolId, address _user)
        public
        view
        returns (uint256)
    {
        uint256 userCooledBal;
        userCooledBal = previewParentUserCEthBalanceAtPrice(
            _poolId,
            retrieveCurrentPrice(_poolId),
            _user
        );
        return userCooledBal;
    }

    /// @notice Get user hEth balance preview at selected price
    /// @param _poolId The pool ID
    /// @param _price The price you want to use to estimate balance
    /// @param _user The user's address
    /// @return uint256 The user hEth balance preview at selected price
    function previewUserHEthBalanceAtPrice(
        uint256 _poolId,
        uint256 _price,
        address _user
    ) public view returns (uint256) {
        uint256 hEthBalEst;
        uint256 cEthBalEst;
        (hEthBalEst, cEthBalEst) = previewPoolBalancesAtPrice(_poolId, _price);
        // Percents provide accurate balance
        uint256 perc = retrieveHEthPercentBalance(_poolId, _user);
        uint256 bal = hEthBalEst;
        return (bal * perc) / bps;
    }

    /// @notice Get user cEth balance preview at selected price
    /// @param _poolId The pool ID
    /// @param _price The price you want to use to estimate balance
    /// @param _user The user's address
    /// @return uint256 The user cEth balance preview at selected price
    function previewParentUserCEthBalanceAtPrice(
        uint256 _poolId,
        uint256 _price,
        address _user
    ) public view returns (uint256) {
        uint256 perc = getParentUserCEthPercent(_poolId, _user);
        uint256 bal = getEstCEthInParentPool(_poolId, _price);
        return (bal * perc) / bps;
    }

    /// @notice Get user's parent pool cEth Bal
    /// @param _poolId The pool ID
    /// @param _user The user's address
    /// @return uint256 The user's parent pool cEth Bal
    function seeUserParentPoolBal(uint256 _poolId, address _user)
        public
        view
        returns (uint256)
    {
        uint256 parentId = parentPoolId[_poolId];
        return ethStakedWithParent[parentId][_user].cBal;
    }

    /// @notice Get pool cEth balance preview
    /// @param _poolId The pool ID
    /// @param _price The price you want to use to estimate balance
    /// @return uint256 The pool cEth balance preview
    function getEstCEthInParentPool(uint256 _poolId, uint256 _price)
        public
        view
        returns (uint256)
    {
        uint256 parentId = parentPoolId[_poolId];
        uint256 cEthInChildPoolsEst;
        for (
            uint256 i = 0;
            i < parentPoolBal[parentId].childPoolIds.length;
            i++
        ) {
            uint256 poolIdIndex = parentPoolBal[parentId].childPoolIds[i];
            uint256 hEthBalEst;
            uint256 cEthBalEst;
            (hEthBalEst, cEthBalEst) = simulateInteract(poolIdIndex, _price);
            cEthInChildPoolsEst += cEthBalEst; // add to total cEth in child pools
        }
        return cEthInChildPoolsEst;
    }

    /// @notice Get pool hEth/cEth balance preview at current price
    /// @param _poolId The pool ID
    /// @return uint256 The pool hEth balance preview
    /// @return uint256 The pool cEth balance preview
    function previewPoolBalances(uint256 _poolId)
        public
        view
        returns (uint256, uint256)
    {
        uint256 hEthBalEst;
        uint256 cEthBalEst;
        (hEthBalEst, cEthBalEst) = previewPoolBalancesAtPrice(
            _poolId,
            retrieveCurrentPrice(_poolId)
        );
        return (hEthBalEst, cEthBalEst);
    }

    /// @notice Get pool hEth/cEth balance preview at selected price
    /// @param _poolId The pool ID
    /// @param _price The price you want to use to estimate balance
    /// @return uint256 The pool hEth balance preview at selected price
    /// @return uint256 The pool cEth balance preview at selected price
    function previewPoolBalancesAtPrice(uint256 _poolId, uint256 _price)
        public
        view
        returns (uint256, uint256)
    {
        uint256 hEthBalEst;
        uint256 cEthBalEst;
        (hEthBalEst, cEthBalEst) = simulateInteract(_poolId, _price);
        return (hEthBalEst, cEthBalEst);
    }

    /// @notice Get current pool health
    /// @param _poolId The pool ID
    /// @param _isCooled Bool value representing whether getting cooled or heated health
    /// @return uint256 The current pool health
    function getPoolHealth(uint256 _poolId, bool _isCooled)
        public
        view
        returns (uint256)
    {
        uint256 health;
        // get the hEthBal and cEthBal previews for the pool
        (uint256 hEthBalPreview, uint256 cEthBalPreview) = previewPoolBalances(
            _poolId
        );
        if (cEthBalPreview == 0 || hEthBalPreview == 0) {
            return 0;
        }
        // calculate expected cEth percent of paired pools
        int256 cEthPercent = (abs(pool[_poolId].hRate) * int256(bps)) /
            (abs(pool[_poolId].hRate) + abs(pool[_poolId].cRate));
        // calculate actual cEth percent of paired pools
        uint256 cooledRatio = ((cEthBalPreview * bps) /
            (cEthBalPreview + hEthBalPreview));
        if (_isCooled == true) {
            //            expected         actual
            health = (uint256(cEthPercent) * 100) / cooledRatio;
        } else {
            //          actual          expected
            health = (cooledRatio * 100) / uint256(cEthPercent);
        }
        return health;
    }

    /// @notice Get an array of all the Pool structs that exist
    /// @return Pool[] memory array of all the pools
    function getAllPools() public view returns (Pool[] memory) {
        Pool[] memory pools = new Pool[](poolIds.length);
        for (uint256 i = 0; i < poolIds.length; i++) {
            pools[i] = pool[poolIds[i]];
        }
        return pools;
    }

    /// @notice GET BALANCE PREVIEWS FOR ALL POOLS - get an array of Pool structs that include
    ///         the current value in the pools, as well as the preview, i.e. if settled
    ///         via a deposit or withdraw, which is the really the actual value.
    function getAllPoolsWithBalances(address _user)
        public
        view
        returns (PoolWithBalances[] memory poolsWithBalances)
    {
        Pool[] memory pools = getAllPools();
        poolsWithBalances = new PoolWithBalances[](pools.length);
        for (uint256 i = 0; i < pools.length; i++) {
            // get the hEthBal and cEthBal previews for the pool[i]
            (
                uint256 hEthBalPreview,
                uint256 cEthBalPreview
            ) = previewPoolBalances(pools[i].id);
            poolsWithBalances[i].id = pools[i].id;
            poolsWithBalances[i].parentId = pools[i].parentId;
            poolsWithBalances[i].lastSettledUsdPrice = pools[i]
                .lastSettledUsdPrice;
            poolsWithBalances[i].currentPrice = retrieveCurrentPrice(
                pools[i].id
            );
            poolsWithBalances[i].basePriceFeedKey = pools[i].basePriceFeedKey;
            poolsWithBalances[i].quotePriceFeedKey = pools[i].quotePriceFeedKey;
            poolsWithBalances[i].hEthBal = pools[i].hEthBal;
            poolsWithBalances[i].cEthBal = pools[i].cEthBal;
            poolsWithBalances[i].hRate = pools[i].hRate;
            poolsWithBalances[i].cRate = pools[i].cRate;
            poolsWithBalances[i].hHealth = getPoolHealth(pools[i].id, false);
            poolsWithBalances[i].cHealth = getPoolHealth(pools[i].id, true);
            poolsWithBalances[i].poolType = pools[i].poolType;
            poolsWithBalances[i].cBalancePreview = cEthBalPreview;
            poolsWithBalances[i].hBalancePreview = hEthBalPreview;
            if (pools[i].parentId != 0) {
                // if pool has a parent pool, get cEth balance for user in parent pool (sum of all children)
                poolsWithBalances[i]
                    .userCEthBalPreview = previewParentUserCEthBalance(
                    pools[i].id,
                    _user
                );
            } else {
                // if pool has no parent pool, get cEth balance for user in single pool
                poolsWithBalances[i]
                    .userCEthBalPreview = previewUserCEthBalance(
                    pools[i].id,
                    _user
                );
            }
            poolsWithBalances[i].userHEthBalPreview = previewUserHEthBalance(
                pools[i].id,
                _user
            );
        }
        return poolsWithBalances;
    }

    /// @notice Get profit percentage in terms of basis points
    /// @dev The price feed name should be updated, it's not always USD
    /// @param _poolId The pool ID
    /// @param _currentUsdPrice The value from the price feed
    /// @return int256 profit percent
    function getProfit(uint256 _poolId, uint256 _currentUsdPrice)
        public
        view
        returns (int256)
    {
        int256 profit = ((int256(_currentUsdPrice) -
            int256(pool[_poolId].lastSettledUsdPrice)) * int256(bps)) /
            int256(pool[_poolId].lastSettledUsdPrice);
        return profit;
    }

    //@@  SIMULATE INTERACT  @@// - view only of simulated rebalance of the cooled and heated tranches
    function simulateInteract(uint256 _poolId, uint256 _simAssetUsd)
        public
        view
        returns (uint256, uint256)
    {
        int256 assetUsdProfit = getProfit(_poolId, _simAssetUsd); // returns ETH/USD profit in terms of basis points
        if (assetUsdProfit == 0) {
            // if price hasn't changed, balances have not changed
            return (pool[_poolId].hEthBal, pool[_poolId].cEthBal);
        }
        if (bothPoolsHaveBalance(_poolId) == false) {
            // skip if there is not opposing balances to settle
            return (pool[_poolId].hEthBal, pool[_poolId].cEthBal);
        }

        // find expected return and use it to calculate allocation difference for each tranche
        (
            int256 cooledAllocationDiff,
            int256 cooledChange,
            uint256 nonNaturalMultiplier
        ) = trancheSpecificCalcs(_poolId, true, assetUsdProfit, _simAssetUsd);
        (
            int256 heatedAllocationDiff,
            int256 heatedChange,

        ) = trancheSpecificCalcs(_poolId, false, assetUsdProfit, _simAssetUsd);
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

            uint256 adjNonNaturalDiff = (uint256(abs(nonNaturalDifference)) *
                nonNaturalMultiplier) / bps;
            absAllocationTotal = uint256(minAbsAllocation) + adjNonNaturalDiff;
        }

        return
            simulateReallocate(
                _poolId,
                _simAssetUsd,
                cooledChange,
                cooledAllocationDiff,
                absAllocationTotal
            ); // reallocate the protocol ETH according to price movement
    }

    /// @notice Shows the estimated price movement of a position
    /// @param _poolId The pool ID
    /// @param _address The address to get the user balance estimates of
    /// @param _isCooled Boolean value if getting cooled value
    /// @param _isAll Boolean value of whether getting the entire value
    /// @return int256[] range of estimated returns at intervals
    function getRangeOfReturns(
        uint256 _poolId,
        address _address,
        bool _isCooled,
        bool _isAll
    ) public view returns (int256[] memory) {
        uint256 assetUsdPrice = retrieveCurrentPrice(_poolId);
        // set bottom range of percents
        int256 currentPercent = -50_0000000000;
        int256 assetUsdAtIndex;
        // create array to record values at different prices
        int256[] memory estBals = new int256[](11);
        for (uint256 index = 0; index < 11; index++) {
            // use percent change to get simulated price feed value at index
            assetUsdAtIndex =
                (int256(assetUsdPrice) * (int256(bps) + currentPercent)) /
                int256(bps);
            // simulate interact to preview settled balances
            uint256 hBalEst;
            uint256 cBalEst;
            (hBalEst, cBalEst) = simulateInteract(
                _poolId,
                uint256(assetUsdAtIndex)
            );
            // calculate estimated balance at price feed value
            uint256 balanceRequested;
            if (_isCooled == false || _isAll == true) {
                balanceRequested =
                    (hBalEst * ethStakedBalance[_poolId][_address].hPercent) /
                    bps;
            }
            if (_isCooled == true || _isAll == true) {
                balanceRequested +=
                    (cBalEst * ethStakedBalance[_poolId][_address].cPercent) /
                    bps;
            }
            // record estimated balance at price
            estBals[index] = int256(balanceRequested);
            // increment percent by 10%
            currentPercent += 10_0000000000;
        }
        // return array of estimated balance at different prices
        return (estBals);
    }

    // Internal functions

    function scalePrice(
        int256 _price,
        uint8 _priceDecimals,
        uint8 _decimals
    ) internal pure returns (int256) {
        if (_priceDecimals < _decimals) {
            return _price * int256(10**uint256(_decimals - _priceDecimals));
        } else if (_priceDecimals > _decimals) {
            return _price / int256(10**uint256(_priceDecimals - _decimals));
        }
        return _price;
    }

    // Private functions

    //@@  INTERACT  @@// - rebalances the cooled and heated tranches/pools
    function interact(uint256 _poolId) private {
        // get current price to determine profit
        uint256 currentAssetUsd = retrieveCurrentPrice(_poolId);
        pool[_poolId].currentUsdPrice = currentAssetUsd;
        int256 assetUsdProfit = getProfit(_poolId, currentAssetUsd); // returns ETH/USD profit in terms of basis points
        if (assetUsdProfit == 0) {
            // if price hasn't changed, balances have not changed
            return;
        }
        if (bothPoolsHaveBalance(_poolId) == false) {
            // skip if there is not opposing balances to settle
            return;
        }

        // find expected return and use it to calculate allocation difference for each tranche
        (
            int256 cooledAllocationDiff,
            int256 cooledChange,
            uint256 nonNaturalMultiplier
        ) = trancheSpecificCalcs(
                _poolId,
                true,
                assetUsdProfit,
                currentAssetUsd
            );
        (
            int256 heatedAllocationDiff,
            int256 heatedChange, // nonNaturalMultiplier excluded

        ) = trancheSpecificCalcs(
                _poolId,
                false,
                assetUsdProfit,
                currentAssetUsd
            );
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

            uint256 adjNonNaturalDiff = (uint256(abs(nonNaturalDifference)) *
                nonNaturalMultiplier) / bps;
            absAllocationTotal = uint256(minAbsAllocation) + adjNonNaturalDiff;
        }
        // calculate the actual allocation for the cooled tranche
        int256 cooledAllocation;
        if (cooledAllocationDiff < 0) {
            if (
                // the cEthBal USD value - absAllocation (in usdDecimals)
                int256((pool[_poolId].cEthBal * currentAssetUsd) / decimals) -
                    int256(absAllocationTotal) >
                0
            ) {
                cooledAllocation = -int256(absAllocationTotal);
            } else {
                cooledAllocation = -int256(
                    (pool[_poolId].cEthBal * currentAssetUsd) / decimals
                ); // the cEthBal USD value (in UsDecimals * Decimals)
            }
        } else {
            if (
                int256((pool[_poolId].hEthBal * currentAssetUsd) / decimals) -
                    int256(absAllocationTotal) >
                0
            ) {
                cooledAllocation = int256(absAllocationTotal); // absolute allocation in UsDecimals
            } else {
                cooledAllocation = int256(
                    (pool[_poolId].hEthBal * currentAssetUsd) / decimals
                );
            }
        }
        // reallocate the protocol ETH according to price movement
        reallocate(_poolId, currentAssetUsd, cooledChange, cooledAllocation);
    }

    //@@  REALLOCATE  @@// - uses the USD values to calculate ETH balances of tranches
    function reallocate(
        uint256 _poolId,
        uint256 _currentAssetUsd, // in usdDecimal form
        int256 _cooledChange,
        int256 _cooledAllocation
    ) private {
        uint256 totalLockedUsd = ((pool[_poolId].cEthBal +
            pool[_poolId].hEthBal) * _currentAssetUsd) / decimals; // USD balance of protocol in usdDecimal terms
        int256 cooledBalAfterAllocation = ((int256(
            pool[_poolId].cEthBal * pool[_poolId].lastSettledUsdPrice
        ) + _cooledChange) / int256(decimals)) + _cooledAllocation;
        int256 heatedBalAfterAllocation = int256(totalLockedUsd) - // heated USD balance in usdDecimal terms
            cooledBalAfterAllocation;
        pool[_poolId].cEthBal =
            (uint256(cooledBalAfterAllocation) * decimals) /
            _currentAssetUsd; // new cEth Balance in Wei
        pool[_poolId].hEthBal =
            (uint256(heatedBalAfterAllocation) * decimals) /
            _currentAssetUsd; // new hEth Balance in Wei
        pool[_poolId].lastSettledUsdPrice = pool[_poolId].currentUsdPrice;
    }

    //@@  REMOVE-FROM-ARRAY  @@// - removes the staker from the array of ETH stakers
    // can be expanded on to further optimize by removing redundancy
    function removeFromArray(uint256 _poolId, uint256 index) private {
        ethStakers[_poolId][index] = ethStakers[_poolId][
            ethStakers[_poolId].length - 1
        ];
        ethStakers[_poolId].pop();
    }

    //@@  TRANCHE/POOL SPECIFIC CALCS  @@// - calculates allocation difference for a tranche/pool
    function trancheSpecificCalcs(
        uint256 _poolId,
        bool _isCooled,
        int256 _assetUsdProfit,
        uint256 _currentAssetUsd
    )
        private
        view
        returns (
            int256,
            int256,
            uint256
        )
    {
        // use tranche/pool balances to estimate expected return
        // and determine balanced re-allocation between pools
        uint256 trancheBal;
        int256 r;
        // get tranche balance and basis points for expected return
        if (_isCooled == true) {
            trancheBal = pool[_poolId].cEthBal; // in Wei
            r = pool[_poolId].cRate; // basis points
        } else {
            trancheBal = pool[_poolId].hEthBal; // in Wei
            r = pool[_poolId].hRate; // basis points
        }
        uint256 cooledRatio = ((pool[_poolId].cEthBal * bps) /
            (pool[_poolId].cEthBal + pool[_poolId].hEthBal));
        uint256 nonNaturalRatio = _assetUsdProfit > 0
            ? cooledRatio
            : ((1 * bps) - cooledRatio);
        int256 trancheChange = (int256(trancheBal) * int256(_currentAssetUsd)) -
            (int256(trancheBal) * int256(pool[_poolId].lastSettledUsdPrice));
        int256 expectedPayout;
        if (pool[_poolId].poolType == 0) {
            expectedPayout =
                (trancheChange * ((1 * int256(bps)) + r)) /
                int256(bps);
        } else if (pool[_poolId].poolType == 1) {
            if (cooledRatio > 50_0000000000) {
                expectedPayout =
                    (trancheChange *
                        (int256(bps) + ((r - int256(cooledRatio))))) /
                    int256(bps);
            } else {
                expectedPayout =
                    (trancheChange *
                        (int256(bps) +
                            ((r - (int256(bps) - int256(cooledRatio)))))) /
                    int256(bps);
            }
        }
        int256 allocationDifference = expectedPayout - trancheChange;
        allocationDifference = allocationDifference / int256(decimals);
        return (allocationDifference, trancheChange, nonNaturalRatio);
    }

    function bothPoolsHaveBalance(uint256 _poolId) public view returns (bool) {
        if (pool[_poolId].cEthBal == 0 || pool[_poolId].hEthBal == 0) {
            return false;
        } else {
            return true;
        }
    }

    //@@  CeTH NEEDED  @@// -- determines the amount of cEth to optimally balance child pools
    function cEthNeededForPools(uint256 poolId) private view returns (uint256) {
        uint256 parentId = parentPoolId[poolId];
        uint256 cEthNeeded;
        for (
            uint256 i = 0;
            i < parentPoolBal[parentId].childPoolIds.length;
            i++
        ) {
            uint256 poolIdIndex = parentPoolBal[parentId].childPoolIds[i];
            if (pool[poolIdIndex].hEthBal == 0) {
                return 0;
            }
            int256 cethPerHeth = cethPerHethTarget(poolIdIndex);
            cEthNeeded += (pool[poolIdIndex].hEthBal * uint256(cethPerHeth));
        }
        return cEthNeeded;
    }

    //@@  CeTH to HeTH ratio  @@// -- determines optimal ratio of cEth per hEth for a child pool
    function cethPerHethTarget(uint256 poolId) private view returns (int256) {
        int256 cethPerHeth = abs(pool[poolId].hRate) / abs(pool[poolId].cRate);
        return cethPerHeth;
    }

    //@@  ReADJUST CHILD POOLS  @@// -- uses available parent balances to optimally balance child pools
    function reAdjustChildPools(uint256 poolId) private {
        uint256 parentId = parentPoolId[poolId]; // set parent ID
        if (parentId != 0) {
            // if pool has parent
            uint256 cEthForBalance = cEthNeededForPools(poolId); // total cEth needed
            uint256 cEthStakedToTargetedRatio; // the ratio of cEth-in-pool/optimal-cEth
            if (cEthForBalance != 0) {
                // avoid divide by zero error
                cEthStakedToTargetedRatio =
                    (parentPoolBal[parentId].cEthBal * bps) /
                    cEthForBalance; // percent of actual eth to amount needed for balance (bps)
            }
            for (
                uint256 i = 0;
                i < parentPoolBal[parentId].childPoolIds.length;
                i++
            ) {
                uint256 poolIdIndex = parentPoolBal[parentId].childPoolIds[i];
                int256 cethPerHeth = cethPerHethTarget(poolIdIndex);
                if (parentPoolBal[parentId].cEthBal == 0) {
                    // if parent pool is zero, zero all individual pool balances too
                    pool[poolIdIndex].cEthBal = 0;
                } else {
                    if (
                        parentPoolBal[parentId].cEthBal > 0 &&
                        pool[poolIdIndex].hEthBal > 0
                    ) {
                        // if hEth values exist to balance and parent has cEth balance
                        if (cEthStakedToTargetedRatio <= bps) {
                            // underweight/even cooled allocation to each child pool
                            pool[poolIdIndex].cEthBal =
                                (pool[poolIdIndex].hEthBal *
                                    uint256(cethPerHeth) *
                                    cEthStakedToTargetedRatio) /
                                bps;
                        } else {
                            // overweight cooled allocation to each child pool
                            uint256 cEthOverEven = parentPoolBal[parentId]
                                .cEthBal - cEthForBalance;
                            pool[poolIdIndex].cEthBal =
                                (pool[poolIdIndex].hEthBal *
                                    uint256(cethPerHeth)) +
                                (cEthOverEven /
                                    parentPoolBal[parentId]
                                        .childPoolIds
                                        .length);
                        }
                    } else {
                        // if values didn't exist to balance, leave cEth balances as is
                        return;
                    }
                }
            }
        }
    }

    //@@  ADD AGGREGATOR  @@// -- adds chainlink price feed aggregator
    function addAggregator(bytes32 currencyKey, address aggregatorAddress)
        private
        onlyOwner
    {
        AggregatorV3Interface aggregator = AggregatorV3Interface(
            aggregatorAddress
        );
        uint8 feedDecimals = aggregator.decimals();
        // assign key (ex. ETH/USD)
        if (address(aggregators[currencyKey]) == address(0)) {
            aggregatorKeys.push(currencyKey);
        }
        aggregators[currencyKey] = aggregator;
        currencyKeyDecimals[currencyKey] = feedDecimals;
    }

    //@@ INTERACT BY POOL  @@// -- interacts to settle pool or all child pools
    function interactByPool(uint256 poolId) private {
        uint256 parentId = parentPoolId[poolId];
        if (parentId == 0) {
            // if no parent, settle single pool
            interact(poolId);
        } else {
            // settle all relevant pools
            uint256 cEthInChildPools;
            uint256 hEthInChildPools;
            for (
                uint256 i = 0;
                i < parentPoolBal[parentId].childPoolIds.length;
                i++
            ) {
                uint256 poolIdIndex = parentPoolBal[parentId].childPoolIds[i];
                // settle each pool
                interact(poolIdIndex);
                // add all balances to get parent pool balances
                cEthInChildPools += pool[poolIdIndex].cEthBal;
                hEthInChildPools += pool[poolIdIndex].hEthBal;
            }
            // set parent pool balances after settling
            parentPoolBal[parentId].cEthBal = cEthInChildPools;
            parentPoolBal[parentId].hEthBal = hEthInChildPools;
        }
    }

    //@@  RE-ADJUST  @@// - adjusts only affected user pool percentages and balances
    function reAdjust(
        uint256 _poolId,
        bool _beforeTx,
        bool _isCooled,
        bool _isHeated
    ) private {
        uint256 parentId = parentPoolId[_poolId];
        if (_beforeTx == true) {
            // BEFORE deposit, only balances are affected based on percentages
            liquidateIfZero(_poolId); // reset percentages on zeroed balances
            for (
                uint256 ethStakersIndex = 0;
                ethStakersIndex < ethStakers[_poolId].length;
                ethStakersIndex++
            ) {
                // adjust balances based on percentage claim
                address addrC = ethStakers[_poolId][ethStakersIndex];
                if (parentPoolId[_poolId] == 0) {
                    // track by single pool
                    ethStakedBalance[_poolId][addrC].cBal =
                        (pool[_poolId].cEthBal *
                            ethStakedBalance[_poolId][addrC].cPercent) /
                        bps;
                } else {
                    // track by parent pool
                    ethStakedWithParent[parentId][addrC].cBal =
                        (parentPoolBal[parentId].cEthBal *
                            ethStakedWithParent[parentId][addrC].cPercent) /
                        bps;
                }
                // adjust heated balance by pool
                ethStakedBalance[_poolId][addrC].hBal =
                    (pool[_poolId].hEthBal *
                        ethStakedBalance[_poolId][addrC].hPercent) /
                    bps;
            }
        } else {
            // AFTER tx, only affected pool percentages change (ex. cooled)
            uint256 indexToRemove; // to track index of user in ethStakers array if account emptied
            bool indexNeedsRemoved = false; // to differentiate indexToRemove == 0 from default ethStakers[0]
            if (_isCooled == true && _isHeated == false) {
                // only Cooled tranche percentage numbers are affected by cooled tx
                for (
                    uint256 ethStakersIndex = 0;
                    ethStakersIndex < ethStakers[_poolId].length;
                    ethStakersIndex++
                ) {
                    address addrC = ethStakers[_poolId][ethStakersIndex];
                    if (parentPoolId[_poolId] == 0) {
                        // track by single pool
                        if (pool[_poolId].cEthBal == 0) {
                            // if pool cEth balance is zero, user balance is zero
                            ethStakedBalance[_poolId][addrC].cPercent = 0;
                        } else {
                            // if pool cEth bal is positive, use user bal to calculate percent
                            ethStakedBalance[_poolId][addrC].cPercent =
                                (ethStakedBalance[_poolId][addrC].cBal * bps) /
                                pool[_poolId].cEthBal;
                        }
                    } else {
                        // track by parent pool
                        if (parentPoolBal[parentId].cEthBal == 0) {
                            // if parent cEth balance is zero, user balance is zero
                            ethStakedWithParent[parentId][addrC].cPercent = 0;
                        } else {
                            // if parent cEth bal is positive, use user bal to calculate percent
                            ethStakedWithParent[parentId][addrC].cPercent =
                                (ethStakedWithParent[parentId][addrC].cBal *
                                    bps) /
                                parentPoolBal[parentId].cEthBal;
                        }
                    }
                }
            } else if (_isCooled == false && _isHeated == true) {
                // only Heated tranche percentage numbers are affected by heated tx
                for (
                    uint256 ethStakersIndex = 0;
                    ethStakersIndex < ethStakers[_poolId].length;
                    ethStakersIndex++
                ) {
                    // heated percentages are always by single pool
                    address addrC = ethStakers[_poolId][ethStakersIndex];
                    if (pool[_poolId].hEthBal == 0) {
                        // if pool hEth bal is zero, user percent is also zero
                        ethStakedBalance[_poolId][addrC].hPercent = 0;
                    } else {
                        // if pool hEth bal is positive, use user bal to calculate percent
                        ethStakedBalance[_poolId][addrC].hPercent =
                            (ethStakedBalance[_poolId][addrC].hBal * bps) /
                            pool[_poolId].hEthBal;
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
                    if (parentPoolId[_poolId] == 0) {
                        // track by single pool
                        if (pool[_poolId].cEthBal == 0) {
                            // if pool cEth bal is zero, user % is also zero
                            ethStakedBalance[_poolId][addrC].cPercent = 0;
                        } else {
                            // if pool cEth bal exists, use user bal to calculate percent
                            ethStakedBalance[_poolId][addrC].cPercent =
                                (ethStakedBalance[_poolId][addrC].cBal * bps) /
                                pool[_poolId].cEthBal;
                        }
                    } else {
                        // track by parent pool
                        if (parentPoolBal[parentId].cEthBal == 0) {
                            // if parent pool cEth bal is zero, user % is also zero
                            ethStakedWithParent[parentId][addrC].cPercent = 0;
                        } else {
                            // if parent cEth bal is positive, use user bal to calculate percent
                            ethStakedWithParent[parentId][addrC].cPercent =
                                (ethStakedWithParent[parentId][addrC].cBal *
                                    bps) /
                                parentPoolBal[parentId].cEthBal;
                        }
                    }
                    // track heated by single pool
                    if (pool[_poolId].hEthBal == 0) {
                        // if pool hEth bal is zero, user % is also zero
                        ethStakedBalance[_poolId][addrC].hPercent = 0;
                    } else {
                        // if pool hEth bal is positive, use user bal to calculate percent
                        ethStakedBalance[_poolId][addrC].hPercent =
                            (ethStakedBalance[_poolId][addrC].hBal * bps) /
                            pool[_poolId].hEthBal;
                    }
                }
            }
        }
    }

    //@@ LIQUIDATE-IF-ZERO  @@// - liquidates every user in a zero balance tranche
    function liquidateIfZero(uint256 _poolId) private {
        // when user balance falls to zero, user percent needs to be set to zero
        for (
            uint256 ethStakersIndex = 0;
            ethStakersIndex < ethStakers[_poolId].length;
            ethStakersIndex++
        ) {
            uint256 parentId = parentPoolId[_poolId];
            address addrC = ethStakers[_poolId][ethStakersIndex];
            if (parentId != 0 && parentPoolBal[parentId].cEthBal == 0) {
                ethStakedWithParent[parentId][addrC].cPercent = 0;
                ethStakedWithParent[parentId][addrC].cBal = 0;
            }
            if (pool[_poolId].cEthBal == 0) {
                // if pool is liquidated, reset user to zero
                ethStakedBalance[_poolId][addrC].cPercent = 0;
                ethStakedBalance[_poolId][addrC].cBal = 0;
            }
            if (pool[_poolId].hEthBal == 0) {
                // if pool is liquidated, reset user to zero
                ethStakedBalance[_poolId][addrC].hBal = 0;
                ethStakedBalance[_poolId][addrC].hPercent = 0;
            }
        }
    }

    //@@  SIMULATE REALLOCATE  @@// - uses the USD values to calculate ETH balances of tranches
    function simulateReallocate(
        uint256 _poolId,
        uint256 _simAssetUsd, // in usdDecimal form
        int256 _cooledChange,
        int256 _cooledAllocationDiff,
        uint256 _absAllocationTotal
    ) private view returns (uint256, uint256) {
        // calculate the actual allocation for the cooled tranche
        int256 cooledAllocation;
        if (_cooledAllocationDiff < 0) {
            if (
                // the cEthBal USD value - absAllocation (in usdDecimals)
                int256((pool[_poolId].cEthBal * _simAssetUsd) / decimals) -
                    int256(_absAllocationTotal) >
                0
            ) {
                cooledAllocation = -int256(_absAllocationTotal);
            } else {
                cooledAllocation = -int256(
                    (pool[_poolId].cEthBal * _simAssetUsd) / decimals
                ); // the cEthBal USD value (in UsDecimals * Decimals)
            }
        } else {
            if (
                int256((pool[_poolId].hEthBal * _simAssetUsd) / decimals) -
                    int256(_absAllocationTotal) >
                0
            ) {
                cooledAllocation = int256(_absAllocationTotal); // absolute allocation in UsDecimals
            } else {
                cooledAllocation = int256(
                    (pool[_poolId].hEthBal * _simAssetUsd) / decimals
                );
            }
        }
        uint256 totalLockedUsd = ((pool[_poolId].cEthBal +
            pool[_poolId].hEthBal) * _simAssetUsd) / decimals; // USD balance of protocol in usdDecimal terms
        int256 cooledBalAfterAllocation = ((int256(
            pool[_poolId].cEthBal * pool[_poolId].lastSettledUsdPrice
        ) + _cooledChange) / int256(decimals)) + cooledAllocation;
        int256 heatedBalAfterAllocation = int256(totalLockedUsd) - // heated USD balance in usdDecimal terms
            cooledBalAfterAllocation;
        uint256 cEthSimBal = (uint256(cooledBalAfterAllocation) * decimals) /
            _simAssetUsd; // new cEth Balance in Wei
        uint256 hEthSimBal = (uint256(heatedBalAfterAllocation) * decimals) /
            _simAssetUsd; // new hEth Balance in Wei
        return (hEthSimBal, cEthSimBal);
    }

    //@@  ABSOLUTE-VALUE  @@// - returns the absolute value of an int
    function abs(int256 x) private pure returns (int256) {
        return x >= 0 ? x : -x;
    }

    //////// ERC-20 FOR FUTURE USE /////////

    //@@  STAKE TOKENS  @@// - for future use with ERC-20s
    function stakeTokens(uint256 _amount, address _token) public {
        // Make sure that the amount to stake is more than 0
        require(_amount > 0, "Amount must be more than 0");
        // Check whether token is allowed by passing it to tokenIsAllowed()
        require(tokenIsAllowed(_token), "Token is not currently allowed.");
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

    //@@  UPDATE UNIQUE POSITIONS  @@// - updates the mapping of user to tokens staked
    function updateUniquePositions(address _user, address _token) internal {
        // If the staking balance of the staker is less that or equal to 0 then...
        if (stakingBalance[_token][_user] <= 0) {
            // add 1 to the number of unique tokens staked
            uniquePositions[_user] = uniquePositions[_user] + 1;
        }
    }

    //@@ STAKE TOKENS  @@// - add a token address to allowed tokens for staking, only owner can call
    function addAllowedTokens(address _token) public onlyOwner {
        // add token address to allowedTokens[] array
        allowedTokens.push(_token);
    }

    //@@  TOKEN IS ALLOWED  @@// - returns whether token is allowed
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
}
