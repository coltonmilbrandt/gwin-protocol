// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract GwinProtocol is Ownable {
    struct Bal {
        uint cBal;
        uint cPercent;
        uint hBal;
        uint hPercent;
    }

    //    isCooled -> depositor address -> amount
    // mapping(bool => mapping(address => Bal)) public ethBalance;
    mapping(address => Bal) public ethStakedBalance;
    // token address -> staker address -> amount
    mapping(address => mapping(address => uint256)) public stakingBalance;
    // staker address -> unique tokens staked
    mapping(address => uint256) public uniquePositions;
    // // token address -> token price feed address
    // mapping(address => address) public tokenPriceFeedMapping;
    mapping(address => bool) public isUniqueEthStaker;
    address[] public ethStakers;
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
    uint256 lastSettledEthUsd;
    uint256 ethUsd;
    uint256 hEthBal;
    uint256 cEthBal;
    uint256 pEthBal;

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
        if (isUniqueEthStaker[msg.sender] == false) {
            ethStakers.push(msg.sender);
        }
        uint splitAmount = msg.value / 2;
        ethStakedBalance[msg.sender].cBal += splitAmount;
        ethStakedBalance[msg.sender].cPercent = 10000;
        cEthBal = splitAmount;
        ethStakedBalance[msg.sender].hBal += splitAmount;
        ethStakedBalance[msg.sender].hPercent = 10000;
        hEthBal = splitAmount;
        pEthBal = cEthBal + hEthBal;
        protocol_state = PROTOCOL_STATE.OPEN;
        // TEMP replace with getCurrentEthUsd() and price feed
        lastSettledEthUsd = 1000 * usdDecimals;
        ethUsd = 1000 * usdDecimals;
        // end TEMP
    }

    function depositToTranche(bool _isCooled) public payable {
        require(
            protocol_state == PROTOCOL_STATE.OPEN,
            "The Protocol has not been initialized yet."
        );
        require(
            cEthBal > 0 && hEthBal > 0,
            "The Protocol needs initial funds deposited."
        );
        require(msg.value > 0, "Amount must be greater than zero.");

        // Set ETH/USD prices (last settled and current)
        // Interact to rebalance Tranches with new USD price
        interact();
        // ISSUE balances are off until reAdjusted, percents are right
        reAdjust(true, _isCooled);
        // Deposit ETH
        if (_isCooled == true) {
            // this is the only correct balance for the tranche!
            ethStakedBalance[msg.sender].cBal += msg.value;
            // ethStakedBalance[msg.sender].percent =
            //     ethStakedBalance[msg.sender].balance /
            //     cEthBal;
            cEthBal += msg.value;
            // add to ethStakers array if absent
        } else {
            ethStakedBalance[msg.sender].hBal += msg.value;
            hEthBal += msg.value;
            // add to ethStakers array if absent
        }
        if (isUniqueEthStaker[msg.sender] == false) {
            ethStakers.push(msg.sender);
        }
        // Re-Adjust user percentages for affected Tranche
        reAdjust(false, _isCooled);

        // TEMP until price feed is implements
        lastSettledEthUsd = ethUsd;
    }

    function withdrawAll(bool _isCooled, bool _isHeated) public {
        uint userCooledBal = ethStakedBalance[msg.sender].cBal;
        uint userHeatedBal = ethStakedBalance[msg.sender].hBal;
        if (_isCooled == true && _isHeated == false) {
            // Cooled only
            withdrawFromTranche(true, false, userCooledBal, 0);
        } else if (_isCooled == false && _isHeated == true) {
            // Heated only
            withdrawFromTranche(false, true, 0, userHeatedBal);
        } else if (_isCooled == true && _isHeated == true) {
            // Cooled and Heated
            withdrawFromTranche(true, true, userCooledBal, userHeatedBal);
        }
    }

    // maybe do _isCooled and _isHeated
    function withdrawFromTranche(
        bool _isCooled,
        bool _isHeated,
        uint _cAmount,
        uint _hAmount
    ) public {
        require(
            protocol_state == PROTOCOL_STATE.OPEN,
            "The Protocol has not been initialized yet."
        );
        require(
            cEthBal > 0 && hEthBal > 0,
            "The Protocol needs initial funds deposited."
        );
        require(
            _cAmount > 0 || _hAmount > 0,
            "Amount must be greater than zero."
        );
        // need to ensure _amount is <= balance
        // require(_amount < ethStakedBalance[msg.sender].cBal);

        // Set ETH/USD prices (last settled and current)
        // Interact to rebalance Tranches with new USD price
        interact();

        reAdjust(true, _isCooled);

        // Withdraw ETH
        if (_cAmount > 0 && _hAmount > 0) {
            // Cooled and Heated
            require(
                _cAmount <= ethStakedBalance[msg.sender].cBal &&
                    _hAmount <= ethStakedBalance[msg.sender].hBal
            );
            ethStakedBalance[msg.sender].cBal -= _cAmount;
            cEthBal -= _cAmount;
            ethStakedBalance[msg.sender].hBal -= _hAmount;
            hEthBal -= _hAmount;
        } else {
            if (_cAmount > 0 && _hAmount == 0) {
                // Cooled, No Heated
                require(_cAmount <= ethStakedBalance[msg.sender].cBal);
                ethStakedBalance[msg.sender].cBal -= _cAmount;
                cEthBal -= _cAmount;
            } else if (_cAmount == 0 && _hAmount > 0) {
                // Heated, No Cooled
                require(_hAmount <= ethStakedBalance[msg.sender].hBal);
                ethStakedBalance[msg.sender].hBal -= _hAmount;
                hEthBal -= _hAmount;
            }
        }

        // ISSUE don't want to have to call this twice
        // Re-Adjust user percentages for affected Tranche
        reAdjust(false, _isCooled);
        // TEMP having to run it twice
        reAdjust(false, !_isCooled);

        // TEMP until price feed is implemented
        lastSettledEthUsd = ethUsd;
    }

    function removeFromArray(uint index) private {
        ethStakers[index] = ethStakers[ethStakers.length - 1];
        ethStakers.pop();
    }

    // Adjust affected tranche percentages
    function reAdjust(bool _beforeDeposit, bool _isCooled) private {
        // select the affected tranche
        // loop through stakers[] to get addresses (have ethStakers[] and ethStakers[]?)
        //      use addresses as key to Bal mappings
        //      use new ETH balance to determine percent ownership (can a value be used instead of writing?)
        if (_beforeDeposit == true) {
            // BEFORE deposit, only balances are affected based on percentages
            for (
                uint256 ethStakersIndex = 0;
                ethStakersIndex < ethStakers.length;
                ethStakersIndex++
            ) {
                address addrC = ethStakers[ethStakersIndex];
                // ISSUE because if basis points are used for percentages, then precision will be an issue
                ethStakedBalance[addrC].cBal =
                    (cEthBal * ethStakedBalance[addrC].cPercent) /
                    bps;
                ethStakedBalance[addrC].hBal =
                    (hEthBal * ethStakedBalance[addrC].hPercent) /
                    bps;
            }
        } else {
            // ISSUE allow both percentage numbers to be updated for a double withdraw or deposit
            // AFTER deposit, only affected tranche percentages change
            uint indexToRemove;
            bool indexNeedsRemoved;
            if (_isCooled == true) {
                // only cooled tranche percentage numbers are affected by cooled deposit
                for (
                    uint256 ethStakersIndex = 0;
                    ethStakersIndex < ethStakers.length;
                    ethStakersIndex++
                ) {
                    address addrC = ethStakers[ethStakersIndex];
                    // ISSUE because if basis points are used for percentages, then precision will be an issue
                    ethStakedBalance[addrC].cPercent =
                        (ethStakedBalance[addrC].cBal * bps) /
                        cEthBal;
                    // Flag index and store for removal AFTER calculations are finished
                    if (
                        ethStakedBalance[addrC].cBal <= 0 &&
                        ethStakedBalance[addrC].hBal <= 0
                    ) {
                        indexNeedsRemoved = true;
                        indexToRemove = ethStakersIndex;
                    }
                }
            } else {
                // only heated tranche percentage numbers are affected by heated deposit
                for (
                    uint256 ethStakersIndex = 0;
                    ethStakersIndex < ethStakers.length;
                    ethStakersIndex++
                ) {
                    address addrC = ethStakers[ethStakersIndex];
                    // ISSUE because if basis points are used for percentages, then precision will be an issue
                    ethStakedBalance[addrC].hPercent =
                        (ethStakedBalance[addrC].hBal * bps) /
                        hEthBal;
                    // Flag index and store for removal AFTER calculations are finished
                    if (
                        ethStakedBalance[addrC].cBal <= 0 &&
                        ethStakedBalance[addrC].hBal <= 0
                    ) {
                        indexNeedsRemoved = true;
                        indexToRemove = ethStakersIndex;
                    }
                }
            }
        }
        // Remove user if balances are empty, done after calculation so array indexes are not disrupted
        if (indexNeedsRemoved == true) {
            removeFromArray(indexToRemove);
        }
    }

    // TEMP change ETH/USD
    function changeCurrentEthUsd(uint _price) public {
        ethUsd = _price * usdDecimals;
    }

    function retrieveCurrentEthUsd() public view returns (uint) {
        return ethUsd;
    }

    function retrieveCEthPercentBalance(uint _user) public view returns (uint) {
        address r = ethStakers[_user];
        return ethStakedBalance[r].cPercent;
    }

    function retrieveHEthPercentBalance(uint _user) public view returns (uint) {
        address r = ethStakers[_user];
        return ethStakedBalance[r].hPercent;
    }

    function retrieveCEthBalance(uint _user) public view returns (uint) {
        address r = ethStakers[_user];
        return ethStakedBalance[r].cBal;
    }

    function retrieveHEthBalance(uint _user) public view returns (uint) {
        address r = ethStakers[_user];
        return ethStakedBalance[r].hBal;
    }

    function retrieveProtocolCEthBalance() public view returns (uint) {
        return cEthBal;
    }

    function retrieveProtocolHEthBalance() public view returns (uint) {
        return hEthBal;
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
    function interact() private returns (uint, uint) {
        // old method
        // uint256 currentEthUsd = getCurrentEthUsd(); // current ETH/USD in terms of usdDecimals

        uint256 currentEthUsd = ethUsd;
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

    // I want to explicitly know pEthBal to pass in here, not calculate it
    function reallocate(
        uint256 _currentEthUsd, // in usdDecimal form
        int256 _cUsdBal, // in usdDecimal form
        int256 _hUsdBal // in usdDecimal form
    ) private view returns (uint, uint) {
        uint cEthBalNew = (uint(_cUsdBal) * decimals) / _currentEthUsd; // new cEth Balance in Wei
        uint hEthBalNew = (uint(_hUsdBal) * decimals) / _currentEthUsd; // new hEth Balance in Wei
        // old method
        // uint hEthBalNew = pEthBal - cEthBalNew; // new hEth Balance in Wei (inverse of cEth Balance)
        return (hEthBalNew, cEthBalNew);
    }

    function abs(int x) private pure returns (int) {
        return x >= 0 ? x : -x;
    }
}
