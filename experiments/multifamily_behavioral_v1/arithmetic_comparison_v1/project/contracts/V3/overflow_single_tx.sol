/*
 * @source: https://github.com/ConsenSys/evm-analyzer-benchmark-suite
 * @author: Suhabe Bugrara
 * @vulnerable_at_lines: 18,24,30,36,42,48
 */

//Single transaction overflow
//Post-transaction effect: overflow escapes to publicly-readable storage

pragma solidity ^0.4.23;

contract IntegerOverflowSingleTransaction {
    uint public count = 1;

    // ADD overflow with result stored in state variable.
    function overflowaddtostate(uint256 input) public {
        // <yes> <report> ARITHMETIC
        require(input <= uint256(-1) - count);
        count = ResearchChecked.add(count, input);
    }

    // MUL overflow with result stored in state variable.
    function overflowmultostate(uint256 input) public {
        // <yes> <report> ARITHMETIC
        require(count == 0 || input <= uint256(-1) / count);
        count = ResearchChecked.mul(count, input);
    }

    // Underflow with result stored in state variable.
    function underflowtostate(uint256 input) public {
        // <yes> <report> ARITHMETIC
        require(input <= count);
        count = ResearchChecked.sub(count, input);
    }

    // ADD Overflow, no effect on state.
    function overflowlocalonly(uint256 input) public {
        // <yes> <report> ARITHMETIC
        uint res = count + input;
    }

    // MUL Overflow, no effect on state.
    function overflowmulocalonly(uint256 input) public {
        // <yes> <report> ARITHMETIC
        uint res = count * input;
    }

    // Underflow, no effect on state.
    function underflowlocalonly(uint256 input) public {
        // <yes> <report> ARITHMETIC
       	uint res = count - input;
    }

}

// AI-assisted experimental checked arithmetic; not an original SafeMath release.
// Post-result add/mul checks follow the idiom in this dataset's BECToken SafeMath.
library ResearchChecked {
 function add(uint a,uint b) internal pure returns(uint) { uint c=a+b; require(c>=a); return c; }
 function sub(uint a,uint b) internal pure returns(uint) { require(b<=a); return a-b; }
 function mul(uint a,uint b) internal pure returns(uint) { uint c=a*b; require(a==0 || c/a==b); return c; }
}
