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
    uint256 myFavoriteNumber;

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

    // Interact: cEthBal, hEthBal, cEthUsdBal, hEthUsdBal, tranche, lastEthUsd, currentEthUsd
    function interact(uint256 _num) public {
        myFavoriteNumber = _num;
    }

    function viewMyNumber() public view returns (uint256) {
        return myFavoriteNumber;
    }

    // Pass in: address, tranche, amount, hotColdRatio, priceChange
}
