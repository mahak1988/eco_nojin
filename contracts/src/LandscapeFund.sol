// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title LandscapeFund
 * @notice Manages village landscape funds with council governance
 * @dev Complements existing eco_nojin carbon_registry.py
 */
contract LandscapeFund {
    
    struct Village {
        string villageId;
        uint256 totalCollected;
        uint256 totalDistributed;
        address manager;
        uint16 feeBps;
        bool active;
    }
    
    mapping(string => Village) public villages;
    
    event FeeCollected(string villageId, uint256 amount, uint256 timestamp);
    event FundDistributed(string villageId, uint256 amount, address recipient);
    
    function registerVillage(
        string memory villageId,
        address manager,
        uint16 feeBps
    ) external {
        require(feeBps <= 500, "Fee max 5%");
        villages[villageId] = Village({
            villageId: villageId,
            totalCollected: 0,
            totalDistributed: 0,
            manager: manager,
            feeBps: feeBps,
            active: true
        });
    }
    
    function collectFee(string memory villageId) external payable {
        Village storage v = villages[villageId];
        require(v.active, "Village not active");
        
        uint256 fee = (msg.value * v.feeBps) / 10000;
        v.totalCollected += fee;
        
        emit FeeCollected(villageId, fee, block.timestamp);
    }
    
    function distribute(
        string memory villageId,
        uint256 amount,
        address payable recipient
    ) external {
        Village storage v = villages[villageId];
        require(amount <= v.totalCollected - v.totalDistributed, "Insufficient");
        
        v.totalDistributed += amount;
        recipient.transfer(amount);
        
        emit FundDistributed(villageId, amount, recipient);
    }
    
    function getBalance(string memory villageId) external view returns (uint256) {
        Village storage v = villages[villageId];
        return v.totalCollected - v.totalDistributed;
    }
}
