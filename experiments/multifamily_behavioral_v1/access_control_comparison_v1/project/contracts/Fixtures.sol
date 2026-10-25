pragma solidity ^0.4.25;
// AI-assisted measurement fixtures, not protective variants or additional cases.
contract ResearchRelay {
 function invoke(address target, bytes data) public payable {
  require(target.call.value(msg.value)(data));
 }
 function() public payable {}
}
contract ResearchRejector {
 function invoke(address target, bytes data) public { require(target.call(data)); }
 function() public payable { revert(); }
}
