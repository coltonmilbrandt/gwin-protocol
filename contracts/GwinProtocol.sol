// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract GwinProtocol is Ownable {
    // token address -> staker address -> amount
    mapping(address => mapping(address => uint256)) public stakingBalance;
    // staker address -> unique tokens staked
    mapping(address => uint256) public uniqueTokensStaked;
    // token address -> token price feed address
    mapping(address => address) public tokenPriceFeedMapping;
    // array of stakers
    address[] public stakers;
    // array of the allowed tokens
    address[] public allowedTokens;
    // Storing the GWIN token as a global variable, IERC20 imported above, address passed into constructor
    IERC20 public gwinToken;

    // Right when we deploy this contract, we need to know the address of GWIN token
    constructor(address _gwinTokenAddress) public {
        // we pass in the address from the GwinToken.sol contract
        gwinToken = IERC20(_gwinTokenAddress);
    }

    function setPriceFeedContract(address _token, address _priceFeed)
        public
        onlyOwner
    {
        // sets the mapping for the token to its corresponding price feed contract
        tokenPriceFeedMapping[_token] = _priceFeed;
    }

    // Issue tokens to all stakers
    function issueTokens() public onlyOwner {
        // loops through the global array, stakers[], for length of stakers[]
        for (
            uint256 stakersIndex = 0;
            stakersIndex < stakers.length;
            stakersIndex++
        ) {
            // the recipient is the index of array stakers[]
            address recipient = stakers[stakersIndex];
            // userTotalValue is fetched through getUserTotalValue()
            uint256 userTotalValue = getUserTotalValue(recipient);
            // Send them a token reward based on their total value locked
            gwinToken.transfer(recipient, userTotalValue);
        }
    }

    // Gets the user's value
    function getUserTotalValue(address _user) public view returns (uint256) {
        // Initialize totalValue at 0
        uint256 totalValue = 0;
        // require that user has some tokens staked
        require(uniqueTokensStaked[_user] > 0, "No tokens staked!");
        // loop through the array of allowed tokens
        for (
            uint256 allowedTokensIndex = 0;
            allowedTokensIndex < allowedTokens.length;
            allowedTokensIndex++
        ) {
            // loops through each single token, calls function to get the staked token's value for payout
            totalValue =
                totalValue +
                getUserSingleTokenValue(
                    _user,
                    allowedTokens[allowedTokensIndex]
                );
        }
        // returns the total value to pay out stake
        return totalValue;
    }

    // Gets the staking value to pay out for a single token
    function getUserSingleTokenStakedValue(address _user, address _token)
        public
        view
        returns (uint256)
    {
        // if there is no tokens staked, return 0
        if (uniqueTokensStaked[_user] <= 0) {
            return 0;
        }
        return stakingBalance[_token][_user];
    }

    // Gets the staking value to pay out for a single token
    function getUserSingleTokenValue(address _user, address _token)
        public
        view
        returns (uint256)
    {
        // if there is no tokens staked, return 0
        if (uniqueTokensStaked[_user] <= 0) {
            return 0;
        }
        // passes getTokenValue() the _token address to get current price and decimals
        (uint256 price, uint256 decimals) = getTokenValue(_token);
        // returns the staking value to pay out
        return (// 10,000000000000000000 ETH
        // ETH/USD --> 100,00000000 USD/ 1 ETH
        // 10 * 100 = 1,000

        // Mapped staking balance * price / decimals
        (stakingBalance[_token][_user] * price) / (10**decimals));
    }

    function getTokenValue(address _token)
        public
        view
        returns (uint256, uint256)
    {
        // priceFeedAddress is pulled from the mapping
        address priceFeedAddress = tokenPriceFeedMapping[_token];
        // priceFeedAddress is fed into the AggregatorV3Interface
        AggregatorV3Interface priceFeed = AggregatorV3Interface(
            priceFeedAddress
        );
        (
            ,
            /*uint80 roundID*/
            int price, /*uint startedAt*/ /*uint timeStamp*/ /*uint80 answeredInRound*/
            ,
            ,

        ) = priceFeed.latestRoundData();
        // set number of decimals for token value
        uint256 decimals = priceFeed.decimals();
        // return token price and decimals
        return (uint256(price), decimals);
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
        updateUniqueTokensStaked(msg.sender, _token);
        // Update the staking balance for the staker
        stakingBalance[_token][msg.sender] =
            stakingBalance[_token][msg.sender] +
            _amount;
        // If after this, the staker has just 1 token staked, then add the staker to stakers[] array
        if (uniqueTokensStaked[msg.sender] == 1) {
            stakers.push(msg.sender);
        }
    }

    // NOTES: Vulnerable to Reentrancy attacks? Yeah. Probably.

    // allows staker to unstake tokens
    function unstakeTokens(address _token) public {
        // set current balance by checking the stakingBalance mapping
        uint256 balance = stakingBalance[_token][msg.sender];
        // current balance must be more than 0
        require(balance > 0, "Staking balance cannot be less than 0");
        // transfer the entire current balance to the staker
        IERC20(_token).transfer(msg.sender, balance);
        // update the mapping of the stakingBalance to 0
        stakingBalance[_token][msg.sender] = 0;
        // reduce the unique tokens staked mapping by 1
        uniqueTokensStaked[msg.sender] = uniqueTokensStaked[msg.sender] - 1;
        // we could also remove the staker entirely... later?
    }

    // updates the mapping of user to tokens staked, could be called INCREMENT
    function updateUniqueTokensStaked(address _user, address _token) internal {
        // NOTES: I feel like it should be '>=' below instead

        // If the staking balance of the staker is less that or equal to 0 then...
        if (stakingBalance[_token][_user] <= 0) {
            // add 1 to the number of unique tokens staked
            uniqueTokensStaked[_user] = uniqueTokensStaked[_user] + 1;
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

    // return a list of allowed token addresses
    function getAllowedTokenArray() public view returns (address[] memory) {
        return allowedTokens;
    }
}
