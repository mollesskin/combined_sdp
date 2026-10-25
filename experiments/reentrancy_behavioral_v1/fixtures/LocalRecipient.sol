// SYNTHETIC LOCAL FIXTURE, unchanged contract extract from compatibility_v2.
pragma solidity ^0.4.24;
contract LocalRecipient {
    address public target;
    bytes4 public withdrawalSelector;
    uint public amount;
    uint public callbacks;
    bool public reject;
    bool public retryOnce;
    function configure(address t, bytes4 sel, uint a, bool r, bool retry) public {
        target = t; withdrawalSelector = sel; amount = a; reject = r; retryOnce = retry; callbacks = 0;
    }
    function fund(bytes4 depositSelector) public payable { require(target.call.value(msg.value)(depositSelector)); }
    function withdraw() public { require(target.call(withdrawalSelector, amount)); }
    function() public payable {
        require(!reject);
        callbacks += 1;
        if (retryOnce && callbacks == 1) { target.call(withdrawalSelector, amount); }
    }
}
