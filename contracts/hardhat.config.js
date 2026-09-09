require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const PRIVATE_KEY = process.env.DEPLOYER_PRIVATE_KEY || "0x0000000000000000000000000000000000000000000000000000000000000001";
const POLYGON_AMOY_RPC = process.env.POLYGON_AMOY_RPC || "https://rpc-amoy.polygon.technology";
const BASE_SEPOLIA_RPC = process.env.BASE_SEPOLIA_RPC || "https://sepolia.base.org";

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },
  networks: {
    hardhat: {
      chainId: 31337,
    },
    polygonAmoy: {
      url: POLYGON_AMOY_RPC,
      accounts: [PRIVATE_KEY],
      chainId: 80002,
    },
    baseSepolia: {
      url: BASE_SEPOLIA_RPC,
      accounts: [PRIVATE_KEY],
      chainId: 84532,
    },
  },
  paths: {
    sources: "./",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },
};
