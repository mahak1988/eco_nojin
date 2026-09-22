@echo off  
chcp 65001  
(  
[profile.default]  
src = \" "src\  
out = \out\  
libs = [\lib\]  
solc_version = \0.8.24\  
optimizer = true  
optimizer_runs = 200  
via_ir = true  
  
[profile.ci]  
verbosity = 3  
  
[fuzz]  
runs = 10000  
  
[invariant]  
runs = 10000  
depth = 1000  
fail_on_revert = true  
  
[rpc_storage_caching]  
enabled = true  
  
[etherscan]  
key = \\\  
[remappings]  
forge-std = \lib/forge-std/src\  
