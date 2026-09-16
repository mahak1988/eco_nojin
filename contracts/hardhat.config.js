// require("@nomicfoundation/hardhat-toolbox");  // Disabled to avoid HH801
require("@nomicfoundation/hardhat-ethers");
require("@nomicfoundation/hardhat-chai-matchers");
require("dotenv").config();

const configuredAccounts = (() => {
  const privateKey = process.env.PRIVATE_KEY;
  if (typeof privateKey === "string" && /^0x[0-9a-fA-F]{64}$/.test(privateKey)) {
    return [privateKey];
  }
  return undefined;
})();
const POLYGON_RPC_URL = process.env.POLYGON_RPC_URL || "https://polygon-rpc.com";
const MUMBAI_RPC_URL = process.env.MUMBAI_RPC_URL || "https://rpc-mumbai.maticvigil.com";
const POLYGONSCAN_API_KEY = process.env.POLYGONSCAN_API_KEY || "";

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.24",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
      viaIR: true,
    },
  },
  networks: {
    hardhat: {
      chainId: 31337,
    },
    localhost: {
      url: "http://127.0.0.1:8545",
    },
    mumbai: {
      url: MUMBAI_RPC_URL,
      ...(configuredAccounts ? { accounts: configuredAccounts } : {}),
      chainId: 80001,
      gasPrice: 35000000000,
    },
    polygon: {
      url: POLYGON_RPC_URL,
      ...(configuredAccounts ? { accounts: configuredAccounts } : {}),
      chainId: 137,
      gasPrice: 50000000000,
    },
  },
  etherscan: {
    apiKey: {
      polygon: POLYGONSCAN_API_KEY,
      polygonMumbai: POLYGONSCAN_API_KEY,
    },
  },
  paths: {
    sources: "./src",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },
  mocha: {
    timeout: 40000,
  },
};
