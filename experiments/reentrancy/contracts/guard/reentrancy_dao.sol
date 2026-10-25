/*
 * @source: https://github.com/ConsenSys/evm-analyzer-benchmark-suite
 * @author: Suhabe Bugrara
 * @vulnerable_at_lines: 18
 */

pragma solidity ^0.4.19;

contract ReentrancyDAO {
    // Experiment guard: Solidity 0.4-compatible, shared contract lock.
    bool private experimentEntered;
    modifier nonReentrant() {
        require(!experimentEntered);
        experimentEntered = true;
        _;
        experimentEntered = false;
    }

    mapping (address => uint) credit;
    uint balance;

    function withdrawAll() public nonReentrant {
        uint oCredit = credit[msg.sender];
        if (oCredit > 0) {
            balance -= oCredit;
            // <yes> <report> REENTRANCY
            bool callResult = msg.sender.call.value(oCredit)();
            require (callResult);
            credit[msg.sender] = 0;
        }
    }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        balance += msg.value;
    }
}
