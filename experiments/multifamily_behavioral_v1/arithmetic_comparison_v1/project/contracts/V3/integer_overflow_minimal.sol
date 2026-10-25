/*
 * @source: https://github.com/SmartContractSecurity/SWC-registry/blob/master/test_cases/integer_overflow_and_underflow/integer_overflow_minimal.sol
 * @author: -
 * @vulnerable_at_lines: 17
 */

//Single transaction overflow
//Post-transaction effect: overflow escapes to publicly-readable storage

pragma solidity ^0.4.19;

contract IntegerOverflowMinimal {
    uint public count = 1;

    function run(uint256 input) public {
        // <yes> <report> ARITHMETIC
        require(input <= count);
        count = ResearchChecked.sub(count, input);
    }
}

// AI-assisted experimental checked arithmetic; not an original SafeMath release.
// Post-result add/mul checks follow the idiom in this dataset's BECToken SafeMath.
library ResearchChecked {
 function add(uint a,uint b) internal pure returns(uint) { uint c=a+b; require(c>=a); return c; }
 function sub(uint a,uint b) internal pure returns(uint) { require(b<=a); return a-b; }
 function mul(uint a,uint b) internal pure returns(uint) { uint c=a*b; require(a==0 || c/a==b); return c; }
}
