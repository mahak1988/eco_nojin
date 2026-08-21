// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title CarbonCredit
 * @notice ERC-1155 carbon credits for Eco Nojin
 * @dev Each token ID represents a project, amount is tCO2e
 */
contract CarbonCredit {
    
    struct Project {
        string name;
        address owner;
        uint256 totalCredits;
        uint256 retired;
        bool verified;
    }
    
    mapping(uint256 => Project) public projects;
    mapping(uint256 => mapping(address => uint256)) public balances;
    uint256 public nextProjectId;
    
    event CreditMinted(uint256 projectId, address to, uint256 amount);
    event CreditRetired(uint256 projectId, address by, uint256 amount);
    
    function mint(address to, uint256 amount) external returns (uint256) {
        uint256 projectId = nextProjectId++;
        projects[projectId] = Project({
            name: "Eco Nojin Project",
            owner: to,
            totalCredits: amount,
            retired: 0,
            verified: true
        });
        balances[projectId][to] = amount;
        
        emit CreditMinted(projectId, to, amount);
        return projectId;
    }
    
    function retire(uint256 projectId, uint256 amount) external {
        require(balances[projectId][msg.sender] >= amount, "Insufficient");
        
        balances[projectId][msg.sender] -= amount;
        projects[projectId].retired += amount;
        
        emit CreditRetired(projectId, msg.sender, amount);
    }
    
    function balanceOf(uint256 projectId, address account) 
        external view returns (uint256) 
    {
        return balances[projectId][account];
    }
}
