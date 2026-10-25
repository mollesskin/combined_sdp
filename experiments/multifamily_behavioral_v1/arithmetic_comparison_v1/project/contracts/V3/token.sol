/*
 * @source: https://github.com/sigp/solidity-security-blog
 * @author: Steve Marx
 * @vulnerable_at_lines: 20,22
 */

 pragma solidity ^0.4.18;

 contract Token {

   mapping(address => uint) balances;
   uint public totalSupply;

   function Token(uint _initialSupply) {
     balances[msg.sender] = totalSupply = _initialSupply;
   }

   function transfer(address _to, uint _value) public returns (bool) {
     // <yes> <report> ARITHMETIC
     require(_value <= balances[msg.sender]);
        require(ResearchChecked.sub(balances[msg.sender], _value) >= 0);
     // <yes> <report> ARITHMETIC
     require(_value <= balances[msg.sender]);
        balances[msg.sender] = ResearchChecked.sub(balances[msg.sender], _value);
     require(_value <= uint256(-1) - balances[_to]);
        balances[_to] = ResearchChecked.add(balances[_to], _value);
     return true;
   }

   function balanceOf(address _owner) public constant returns (uint balance) {
     return balances[_owner];
   }
 }

// AI-assisted experimental checked arithmetic; not an original SafeMath release.
// Post-result add/mul checks follow the idiom in this dataset's BECToken SafeMath.
library ResearchChecked {
 function add(uint a,uint b) internal pure returns(uint) { uint c=a+b; require(c>=a); return c; }
 function sub(uint a,uint b) internal pure returns(uint) { require(b<=a); return a-b; }
 function mul(uint a,uint b) internal pure returns(uint) { uint c=a*b; require(a==0 || c/a==b); return c; }
}
