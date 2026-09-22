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
const AMOY_RPC_URL = process.env.AMOY_RPC_URL || "https://rpc-amoy.polygon.technology";
const POLYGONSCAN_API_KEY = process.env.POLYGONSCAN_API_KEY || "";

const AMOY_CHAIN_ID = 80002;
const POLYGON_CHAIN_ID = 137;

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
    amoy: {
      url: AMOY_RPC_URL,
      ...(configuredAccounts ? { accounts: configuredAccounts } : {}),
      chainId: 80002,
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
      polygonAmoy: POLYGONSCAN_API_KEY,
    },
    customChains: [
      {
        network: "amoy",
        chainId: 80002,
        urls: {
          apiURL: "https://api-amoy.polygonscan.com/api",
          browserURL: "https://amoy.polygonscan.com",
        },
      },
    ],
  },
  paths: {
    sources: "./src",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },
  mocha: {
    timeout: 60000,
  },
};