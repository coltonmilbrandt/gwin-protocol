// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract TokenFarm is Ownable {
    // want a mapping token address -> staker address -> amount
    mapping(address => mapping(address => uint256)) public stakingBalance;
    mapping(address => uint256) public uniqueTokensStaked;
    // token address to token price feed address
    mapping(address => address) public tokenPriceFeedMapping;
    address[] public stakers;
    address[] public allowedTokens;
    IERC20 public gwinToken;


    // stakeTokens - DONE!
    // unStakeTokens - DONE! 
    // issueTokens - DONE!
    // addAllowedTokens - DONE!
    // getEthValue - DONE!

    // **  Staking Rewards  **
    // 1:1 ETH per GWIN
    // If 50 ETH and 50 DAI, and we want to reward 1 GWIN / 1 DAI

    constructor(address _gwinTokenAddress) public {
        gwinToken = IERC20(_gwinTokenAddress);
    }

    function setPriceFeedContract(address _token, address _priceFeed) public onlyOwner {
        // this maps the token to its corresponding price feed contract
        tokenPriceFeedMapping[_token] = _priceFeed;
    }

    function issueTokens() public onlyOwner {
        // Issue tokens to all stakers
        for (
            uint256 stakersIndex = 0; 
            stakersIndex < stakers.length; 
            stakersIndex++
        ) {
            address recipient = stakers[stakersIndex];
            uint256 userTotalValue = getUserTotalValue(recipient);
            gwinToken.transfer(recipient, userTotalValue);
            // Send them a token reward based on their total value locked
            // gwinToken.transfer(recipient, ????)
        }
    }

    function getUserTotalValue(address _user) public view returns (uint256) {
        uint256 totalValue = 0;
        require(uniqueTokensStaked[_user] > 0, "No tokens staked!");
        for (
            uint256 allowedTokensIndex = 0;
            allowedTokensIndex < allowedTokens.length;
            allowedTokensIndex++
        ){
            totalValue = totalValue + getUserSingleTokenValue(_user, allowedTokens[allowedTokensIndex]);
        }
        return totalValue;
    }

    function getUserSingleTokenValue(address _user, address _token) public view returns (uint256) {
        if (uniqueTokensStaked[_user] <= 0) {
            return 0;
        }
        // price of the token * stakingBalance[_token][user]
        (uint256 price, uint256 decimals) = getTokenValue(_token);
        return (
            // 10,000000000000000000 ETH
            // ETH/USD --> 100,00000000 USD/ 1 ETH
            // 10 * 100 = 1,000
            stakingBalance[_token][_user] * price / (10**decimals)
        );
    }

    function getTokenValue(address _token) public view returns (uint256, uint256) {
        // priceFeedAddress
        address priceFeedAddress = tokenPriceFeedMapping[_token];
        AggregatorV3Interface priceFeed = AggregatorV3Interface(priceFeedAddress);
        (
            /*uint80 roundID*/,
            int price,
            /*uint startedAt*/,
            /*uint timeStamp*/,
            /*uint80 answeredInRound*/
        ) = priceFeed.latestRoundData();
        uint256 decimals = priceFeed.decimals();
        return (uint256(price), decimals);
    }

    function stakeTokens(uint256 _amount, address _token) public {
        // what tokens can they stake?
        // how much can they stake?
        require(_amount > 0, "Amount must be more than 0");
        require(tokenIsAllowed(_token), "Token is not currently allowed.");
        // transferFrom  --  ERC20s have transfer and transfer from. 
        // Transfer only works if you call it from the wallet that owns the token
        IERC20(_token).transferFrom(msg.sender, address(this), _amount);
        updateUniqueTokensStaked(msg.sender, _token);
        stakingBalance[_token][msg.sender] = stakingBalance[_token][msg.sender] + _amount;
        if (uniqueTokensStaked[msg.sender] == 1){
            stakers.push(msg.sender);
        }
    }

    // Vulnerable to Reentrancy attacks? Yeah. Probably.
    function unstakeTokens(address _token) public {
        uint256 balance = stakingBalance[_token][msg.sender];
        require(balance > 0, "Staking balance cannot be less than 0");
        IERC20(_token).transfer(msg.sender, balance);
        stakingBalance[_token][msg.sender] = 0;
        uniqueTokensStaked[msg.sender] = uniqueTokensStaked[msg.sender] - 1;
    }

    function updateUniqueTokensStaked(address _user, address _token) internal {
        // I feel like it should be '>=' below instead
        if (stakingBalance[_token][_user] <= 0) {
            uniqueTokensStaked[_user] = uniqueTokensStaked[_user] + 1;
        }
    }

    function addAllowedTokens(address _token) public onlyOwner {
        allowedTokens.push(_token);
    }

    function tokenIsAllowed(address _token) public returns (bool) {
        for(uint256 allowedTokensIndex=0; allowedTokensIndex < allowedTokens.length; allowedTokensIndex++){
            if(allowedTokens[allowedTokensIndex] == _token){
                return true;
            }
        }
        return false;
    }
}