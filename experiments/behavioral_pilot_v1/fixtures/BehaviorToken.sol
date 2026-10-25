// SYNTHETIC LOCAL FIXTURE ONLY: unrestricted mint/configuration is for tests.
pragma solidity ^0.4.19;
contract BehaviorToken {
    uint256 public mode;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    function setMode(uint256 m) public { require(m <= 2); mode = m; }
    function mint(address who, uint256 amount) public { balanceOf[who] += amount; }
    function transfer(address to, uint256 amount) public returns (bool) {
        if (mode == 1) return false;
        if (mode == 2) revert();
        require(balanceOf[msg.sender] >= amount);
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }
}
