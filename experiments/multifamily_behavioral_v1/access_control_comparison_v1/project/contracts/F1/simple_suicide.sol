/*
 * @source: https://github.com/SmartContractSecurity/SWC-registry/blob/master/test_cases/unprotected_critical_functions/simple_suicide.sol
 * @author: -
 * @vulnerable_at_lines: 12,13
 */

//added prgma version
pragma solidity ^0.4.0;

contract SimpleSuicide {
  address private deploymentOwner;
  constructor() public { deploymentOwner = msg.sender; }
  // <yes> <report> ACCESS_CONTROL
  function sudicideAnyone() {
    require(msg.sender == deploymentOwner);
    selfdestruct(msg.sender);
  }

}
