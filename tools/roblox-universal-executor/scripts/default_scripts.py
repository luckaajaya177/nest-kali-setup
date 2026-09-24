"""
NestExecutor - Sample Scripts for Roblox
Pre-configured scripts for common use cases
"""

# ============================================================
# UTILITY SCRIPTS
# ============================================================

CLOCK_SCRIPT = """
-- Clock Display
-- Shows current time in Roblox chat
-- Usage: Works on all platforms

local Players = game:GetService("Players")
local player = Players.LocalPlayer

while true do
    local time = os.date("%H:%M:%S")
    player:Chat("Current time: " .. time, false)
    wait(1)
end
"""

FPS_COUNTER_SCRIPT = """
-- FPS Counter
-- Displays frames per second
-- Usage: Works on all platforms

local Stats = game:GetService("Stats")
local Players = game:GetService("Players")
local player = Players.LocalPlayer

while true do
    wait(1)
    local fps = Stats.FPS
    player:Chat("FPS: " .. tostring(fps), false)
end
"""

AUTO_RECONNECT_SCRIPT = """
-- Auto Reconnect
-- Automatically reconnects if disconnected
-- Usage: Works on all platforms

local Players = game:GetService("Players")
local player = Players.LocalPlayer

while true do
    if not player or not player.Parent then
        wait(5)
        game:GetService("TeleportService"):TeleportToPlaceInstance(
            game.PlaceId,
            game.JobId,
            player
        )
    end
    wait(1)
end
"""

# ============================================================
# VISUAL SCRIPTS
# ============================================================

ESP_SCRIPT = """
-- ESP (Extra Sensory Perception)
-- Shows player information through walls
-- Usage: Works on PC (Windows/macOS/Linux)

local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local RunService = game:GetService("RunService")

local function createESP(player)
    local character = player.Character
    if not character then return end
    
    local head = character:FindFirstChild("Head")
    if not head then return end
    
    -- Create BillboardGui
    local billboard = Instance.new("BillboardGui")
    billboard.Size = UDim2.new(0, 200, 0, 50)
    billboard.StudsOffset = Vector3.new(0, 2, 0)
    billboard.Adornee = head
    billboard.Parent = head
    
    -- Create label
    local label = Instance.new("TextLabel")
    label.Size = UDim2.new(1, 0, 1, 0)
    label.BackgroundTransparency = 1
    label.Text = player.Name .. " | HP: ??? "
    label.TextColor3 = Color3.fromRGB(255, 0, 0)
    label.TextScaled = true
    label.Font = Enum.Font.SourceSansBold
    label.Parent = billboard
end

for _, player in ipairs(Players:GetPlayers()) do
    if player ~= Players.LocalPlayer then
        createESP(player)
    end
end

Players.PlayerAdded:Connect(createESP)
Players.PlayerRemoving:Connect(function(player)
    local character = player.Character
    if character then
        local head = character:FindFirstChild("Head")
        if head and head.Parent:FindFirstChild("BillboardGui") then
            head.Parent:FindFirstChild("BillboardGui"):Destroy()
        end
    end
end)

print("[NestExecutor] ESP loaded!")
"""

AIMBOT_SCRIPT = """
-- Aimbot (Visual Indicator Only)
-- Draws lines to players
-- Usage: PC only (visual assist)

local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local Camera = Workspace.CurrentCamera

local function getDistance(pos1, pos2)
    return (pos1 - pos2).Magnitude
end

local function getNearestPlayer()
    local localPlayer = Players.LocalPlayer
    local char = localPlayer.Character
    if not char then return nil end
    
    local head = char:FindFirstChild("Head")
    if not head then return nil end
    
    local nearest = nil
    local nearestDist = math.huge
    
    for _, player in ipairs(Players:GetPlayers()) do
        if player ~= localPlayer and player.Character then
            local enemyHead = player.Character:FindFirstChild("Head")
            if enemyHead then
                local dist = getDistance(head.Position, enemyHead.Position)
                if dist < nearestDist then
                    nearestDist = dist
                    nearest = enemyHead
                end
            end
        end
    end
    
    return nearest
end

RunService.RenderStepped:Connect(function()
    local target = getNearestPlayer()
    if target then
        local pos = Camera:WorldToScreenPoint(target.Position)
        -- Draw indicator (requires graphics API)
        print("[NestExecutor] Target acquired: " .. tostring(pos.X) .. ", " .. tostring(pos.Y))
    end
end)

print("[NestExecutor] Aimbot visual loaded!")
"""

# ============================================================
# AUTOMATION SCRIPTS
# ============================================================

AUTO_FARM_SCRIPT = """
-- Auto Farm (Example)
-- Automatically collects items
-- Usage: Modify for specific game mechanics

local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local RunService = game:GetService("RunService")

local localPlayer = Players.LocalPlayer
local character = localPlayer.Character
local humanoid = character:WaitForChild("Humanoid")
local rootPart = character:WaitForChild("HumanoidRootPart")

local farmPoints = {}

-- Configure farm points (modify for your game)
table.insert(farmPoints, Vector3.new(0, 10, 0))
table.insert(farmPoints, Vector3.new(100, 10, 100))
table.insert(farmPoints, Vector3.new(-50, 10, 50))

local currentPoint = 1

RunService.Heartbeat:Connect(function()
    local target = farmPoints[currentPoint]
    if target then
        local direction = (target - rootPart.Position).Unit
        humanoid:Move(direction)
        
        -- Check if reached
        if (rootPart.Position - target).Magnitude < 5 then
            currentPoint = (currentPoint % #farmPoints) + 1
        end
    end
end)

print("[NestExecutor] Auto farm loaded! Points: " .. #farmPoints)
"""

SPAM_SCRIPT = """
-- Chat Spam (For testing)
-- Send repeated messages
-- Usage: Works on all platforms

local Players = game:GetService("Players")
local player = Players.LocalPlayer

local messages = {
    "Hello!",
    "NestExecutor",
    "Test message 1",
    "Test message 2",
}

local index = 1

while true do
    player:Chat(messages[index], false)
    index = (index % #messages) + 1
    wait(0.5)
end
"""

# ============================================================
# DEBUG SCRIPTS
# ============================================================

DEBUG_INSPECTOR_SCRIPT = """
-- Debug Inspector
-- Shows detailed game information
-- Usage: All platforms

local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local RunService = game:GetService("RunService")
local Stats = game:GetService("Stats")

local function inspect()
    local info = {
        players = #Players:GetPlayers(),
        workspace_objects = #Workspace:GetChildren(),
        fps = Stats.FPS,
        memory = Stats.MemoryUsage,
        ping = Stats.Network.ServerReplicationLatency,
    }
    
    print("[NestExecutor] Debug Info:")
    for key, value in pairs(info) do
        print("  " .. key .. ": " .. tostring(value))
    end
end

while true do
    inspect()
    wait(5)
end
"""

# ============================================================
# EXPORT ALL SCRIPTS
# ============================================================

ALL_SCRIPTS = {
    ["clock"] = CLOCK_SCRIPT,
    ["fps_counter"] = FPS_COUNTER_SCRIPT,
    ["auto_reconnect"] = AUTO_RECONNECT_SCRIPT,
    ["esp"] = ESP_SCRIPT,
    ["aimbot"] = AIMBOT_SCRIPT,
    ["auto_farm"] = AUTO_FARM_SCRIPT,
    ["spam"] = SPAM_SCRIPT,
    ["debug_inspector"] = DEBUG_INSPECTOR_SCRIPT,
}

return ALL_SCRIPTS
