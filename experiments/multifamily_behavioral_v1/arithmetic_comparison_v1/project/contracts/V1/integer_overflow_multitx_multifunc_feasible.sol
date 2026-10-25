/*
 * @source: https://github.com/ConsenSys/evm-analyzer-benchmark-suite
 * @author: Suhabe Bugrara
 * @vulnerable_at_lines: 25
 */

//Multi-transactional, multi-function
//Arithmetic instruction reachable

pragma solidity ^0.4.23;

contract IntegerOverflowMultiTxMultiFuncFeasible {
    uint256 private initialized = 0;
    uint256 public count = 1;

    function init() public {
        initialized = 1;
    }

    function run(uint256 input) {
        if (initialized == 0) {
            return;
        }
        // <yes> <report> ARITHMETIC
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
