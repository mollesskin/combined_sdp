// SYNTHETIC LOCAL FIXTURE ONLY. No real token address or deployed contract.
pragma solidity ^0.4.18;
contract TransferFromToken {
    uint256 public mode;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    function setMode(uint256 m) public { require(m <= 2); mode = m; }
    function mint(address who, uint256 amount) public { balanceOf[who] += amount; }
    function approve(address spender, uint256 amount) public returns(bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }
    function transferFrom(address from, address to, uint256 amount) public returns(bool) {
        if (mode == 1) return false;
        if (mode == 2) revert();
        require(balanceOf[from] >= amount);
        require(allowance[from][msg.sender] >= amount);
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        allowance[from][msg.sender] -= amount;
        return true;
    }
}
