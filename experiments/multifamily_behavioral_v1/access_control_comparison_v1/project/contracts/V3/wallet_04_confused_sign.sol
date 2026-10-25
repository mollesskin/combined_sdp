/*
 * @source: https://smartcontractsecurity.github.io/SWC-registry/docs/SWC-105#wallet-04-confused-signsol
 * @author: -
 * @vulnerable_at_lines: 30
 */

 pragma solidity ^0.4.24;

 /* User can add pay in and withdraw Ether.
    Unfortunatelty, the developer was drunk and used the wrong comparison operator in "withdraw()"
    Anybody can withdraw arbitrary amounts of Ether :()
 */

 contract Wallet {
     address creator;

     mapping(address => uint256) balances;

     constructor() public {
         creator = msg.sender;
     }

     function deposit() public payable {
         assert(balances[msg.sender] + msg.value > balances[msg.sender]);
         balances[msg.sender] += msg.value;
     }

     function withdraw(uint256 amount) public {
         // <yes> <report> ACCESS_CONTROL
         require(amount <= balances[msg.sender]);
         msg.sender.transfer(amount);
         balances[msg.sender] = ResearchDebit.sub(balances[msg.sender], amount);
     }

     // In an emergency the owner can migrate  allfunds to a different address.

     function migrateTo(address to) public {
         require(creator == msg.sender);
         to.transfer(this.balance);
     }

 }

// AI-assisted local checked subtraction, not a third-party library release.
// Check the computed modular result before it can be assigned to storage.
library ResearchDebit {
 function sub(uint a,uint b) internal pure returns(uint) { uint c=a-b; require(c<=a); return c; }
}
