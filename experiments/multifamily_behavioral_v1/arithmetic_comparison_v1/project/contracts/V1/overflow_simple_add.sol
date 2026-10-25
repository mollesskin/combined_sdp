/*
 * @source: https://smartcontractsecurity.github.io/SWC-registry/docs/SWC-101#overflow-simple-addsol
 * @author: -
 * @vulnerable_at_lines: 14
 */

pragma solidity 0.4.25;

contract Overflow_Add {
    uint public balance = 1;

    function add(uint256 deposit) public {
        // <yes> <report> ARITHMETIC
        balance = ResearchChecked.add(balance, deposit);
    }
}

// AI-assisted experimental checked arithmetic; not an original SafeMath release.
// Post-result add/mul checks follow the idiom in this dataset's BECToken SafeMath.
library ResearchChecked {
 function add(uint a,uint b) internal pure returns(uint) { uint c=a+b; require(c>=a); return c; }
 function sub(uint a,uint b) internal pure returns(uint) { require(b<=a); return a-b; }
 function mul(uint a,uint b) internal pure returns(uint) { uint c=a*b; require(a==0 || c/a==b); return c; }
}
