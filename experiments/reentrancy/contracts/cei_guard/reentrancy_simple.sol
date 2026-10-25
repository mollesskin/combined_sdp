/*
 * @source: https://github.com/trailofbits/not-so-smart-contracts/blob/master/reentrancy/Reentrancy.sol
 * @author: -
 * @vulnerable_at_lines: 24
 */

 pragma solidity ^0.4.15;

 contract Reentrance {
    // Experiment guard: Solidity 0.4-compatible, shared contract lock.
    bool private experimentEntered;
    modifier nonReentrant() {
        require(!experimentEntered);
        experimentEntered = true;
        _;
        experimentEntered = false;
    }

     mapping (address => uint) userBalance;

     function getBalance(address u) constant returns(uint){
         return userBalance[u];
     }

     function addToBalance() payable{
         userBalance[msg.sender] += msg.value;
     }

     function withdrawBalance() nonReentrant{
         // send userBalance[msg.sender] ethers to msg.sender
         // if mgs.sender is a contract, it will call its fallback function
         // <yes> <report> REENTRANCY
         uint amount = userBalance[msg.sender];
         userBalance[msg.sender] = 0;
         if( ! (msg.sender.call.value(amount)() ) ){
             throw;
         }
     }
 }
