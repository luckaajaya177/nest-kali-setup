-- NestExecutor Demo Script
-- Cross-platform Roblox testing
-- Usage: python nest_executor.py --script demo.luau --execute

print("[NestExecutor] Demo script loaded!")
print("[NestExecutor] Platform: " .. tostring(game:GetService("RunService"):IsStudio()))

-- Show game info
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")

print("[NestExecutor] Players: " .. tostring(#Players:GetPlayers()))
print("[NestExecutor] Workspace children: " .. tostring(#Workspace:GetChildren()))

-- Success message
print("[NestExecutor] Demo complete!")
