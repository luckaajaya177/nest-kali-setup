# NestExecutor Windows Form Interface
# Cross-platform Roblox Script Executor
# C# / .NET 6+ / Windows Forms

using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Forms;
using Newtonsoft.Json;

namespace NestExecutor
{
    /// <summary>
    /// Main form for NestExecutor Windows interface
    /// </summary>
    public class MainForm : Form
    {
        // Core components
        private Panel mainPanel;
        private SplitContainer splitContainer;
        private ListBox scriptList;
        private TextBox codeEditor;
        private Button executeBtn;
        private Button injectBtn;
        private Button uninjectBtn;
        private Button addScriptBtn;
        private Button deleteScriptBtn;
        private ComboBox platformCombo;
        private StatusStrip statusStrip;
        private ToolStripStatusLabel statusLabel;
        private ToolStripStatusLabel injectStatusLabel;
        private TextBox consoleOutput;
        private TabControl tabControl;
        private TabPage scriptsTab;
        private TabPage settingsTab;
        private GroupBox platformGroup;
        private CheckBox autoInjectCheck;
        private NumericUpDown portNumeric;
        
        // State
        private bool isInjected = false;
        private string currentPlatform = "windows";
        private List<ScriptItem> scripts = new List<ScriptItem>();
        private NestCoreClient coreClient;
        
        public MainForm()
        {
            InitializeComponent();
            InitializeCore();
            LoadDefaultScripts();
            UpdateStatus();
        }
        
        private void InitializeComponent()
        {
            // Main form
            this.Text = "NestExecutor v2.0.0 - Universal Roblox Script Executor";
            this.Size = new Size(1200, 800);
            this.MinimumSize = new Size(900, 600);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.Font = new Font("Segoe UI", 9F);
            
            // Main panel with splitter
            mainPanel = new Panel { Dock = DockStyle.Fill };
            
            splitContainer = new SplitContainer();
            splitContainer.Dock = DockStyle.Fill;
            splitContainer.SplitterDistance = 350;
            splitContainer.FixedPanel = FixedPanel.Panel1;
            
            // Left panel - Script list
            scriptList = new ListBox();
            scriptList.Dock = DockStyle.Fill;
            scriptList.ItemHeight = 20;
            scriptList.SelectedIndexChanged += ScriptList_SelectedIndexChanged;
            
            // Left panel buttons
            var leftPanel = new Panel();
            leftPanel.Dock = DockStyle.Bottom;
            leftPanel.Height = 50;
            
            addScriptBtn = new Button();
            addScriptBtn.Text = "+ Add Script";
            addScriptBtn.Location = new Point(10, 10);
            addScriptBtn.Size = new Size(120, 30);
            addScriptBtn.Click += AddScriptBtn_Click;
            
            deleteScriptBtn = new Button();
            deleteScriptBtn.Text = "- Delete";
            deleteScriptBtn.Location = new Point(140, 10);
            deleteScriptBtn.Size = new Size(100, 30);
            deleteScriptBtn.Click += DeleteScriptBtn_Click;
            
            leftPanel.Controls.Add(addScriptBtn);
            leftPanel.Controls.Add(deleteScriptBtn);
            
            var leftContainer = new Panel();
            leftContainer.Controls.Add(scriptList);
            leftContainer.Controls.Add(leftPanel);
            leftContainer.Dock = DockStyle.Fill;
            
            splitContainer.Panel1.Controls.Add(leftContainer);
            
            // Right panel - Code editor and controls
            var rightPanel = new Panel();
            rightPanel.Dock = DockStyle.Fill;
            
            // Tab control
            tabControl = new TabControl();
            tabControl.Dock = DockStyle.Top;
            tabControl.Height = 400;
            
            // Scripts tab
            scriptsTab = new TabPage("Scripts");
            
            codeEditor = new TextBox();
            codeEditor.Multiline = true;
            codeEditor.ScrollBars = ScrollBars.Both;
            codeEditor.Font = new Font("Consolas", 10F);
            codeEditor.Dock = DockStyle.Fill;
            codeEditor.AcceptsTab = true;
            
            // Execute button
            executeBtn = new Button();
            executeBtn.Text = "▶ Execute";
            executeBtn.Size = new Size(120, 40);
            executeBtn.Location = new Point(codeEditor.Right - 130, 10);
            executeBtn.BackColor = Color.FromArgb(0, 122, 204);
            executeBtn.ForeColor = Color.White;
            executeBtn.Click += ExecuteBtn_Click;
            
            scriptsTab.Controls.Add(codeEditor);
            scriptsTab.Controls.Add(executeBtn);
            
            // Settings tab
            settingsTab = new TabPage("Settings");
            
            platformGroup = new GroupBox();
            platformGroup.Text = "Platform Configuration";
            platformGroup.Location = new Point(10, 10);
            platformGroup.Size = new Size(300, 200);
            
            platformCombo = new ComboBox();
            platformCombo.DropDownStyle = ComboBoxStyle.DropDownList;
            platformCombo.Items.AddRange(new object[] { "Windows", "macOS", "Linux", "Android", "iOS" });
            platformCombo.SelectedIndex = 0;
            platformCombo.Location = new Point(10, 25);
            platformCombo.Size = new Size(280, 25);
            platformCombo.SelectedIndexChanged += PlatformCombo_SelectedIndexChanged;
            
            autoInjectCheck = new CheckBox();
            autoInjectCheck.Text = "Auto-inject on startup";
            autoInjectCheck.Location = new Point(10, 60);
            autoInjectCheck.Checked = false;
            
            var portLabel = new Label();
            portLabel.Text = "IPC Port:";
            portLabel.Location = new Point(10, 95);
            
            portNumeric = new NumericUpDown();
            portNumeric.Value = 17841;
            portNumeric.Minimum = 1024;
            portNumeric.Maximum = 65535;
            portNumeric.Location = new Point(80, 90);
            portNumeric.Size = new Size(80, 25);
            
            platformGroup.Controls.Add(platformCombo);
            platformGroup.Controls.Add(autoInjectCheck);
            platformGroup.Controls.Add(portLabel);
            platformGroup.Controls.Add(portNumeric);
            
            settingsTab.Controls.Add(platformGroup);
            
            tabControl.TabPages.Add(scriptsTab);
            tabControl.TabPages.Add(settingsTab);
            
            rightPanel.Controls.Add(tabControl);
            
            // Console output
            var consoleLabel = new Label();
            consoleLabel.Text = "Console Output:";
            consoleLabel.Location = new Point(10, 410);
            
            consoleOutput = new TextBox();
            consoleOutput.Multiline = true;
            consoleOutput.ScrollBars = ScrollBars.Both;
            consoleOutput.Font = new Font("Consolas", 9F);
            consoleOutput.ReadOnly = true;
            consoleOutput.Location = new Point(10, 435);
            consoleOutput.Size = new Size(830, 200);
            
            rightPanel.Controls.Add(consoleLabel);
            rightPanel.Controls.Add(consoleOutput);
            
            splitContainer.Panel2.Controls.Add(rightPanel);
            
            mainPanel.Controls.Add(splitContainer);
            
            // Bottom toolbar
            var toolBar = new Panel();
            toolBar.Dock = DockStyle.Bottom;
            toolBar.Height = 50;
            
            injectBtn = new Button();
            injectBtn.Text = "🔌 Inject";
            injectBtn.Size = new Size(120, 35);
            injectBtn.Location = new Point(10, 8);
            injectBtn.BackColor = Color.LimeGreen;
            injectBtn.Click += InjectBtn_Click;
            
            uninjectBtn = new Button();
            uninjectBtn.Text = "🔌 Uninject";
            uninjectBtn.Size = new Size(120, 35);
            uninjectBtn.Location = new Point(140, 8);
            uninjectBtn.BackColor = Color.OrangeRed;
            uninjectBtn.Click += UninjectBtn_Click;
            
            // Status strip
            statusStrip = new StatusStrip();
            statusLabel = new ToolStripStatusLabel("Ready");
            injectStatusLabel = new ToolStripStatusLabel("Not Injected");
            statusStrip.Items.Add(statusLabel);
            statusStrip.Items.Add(injectStatusLabel);
            
            this.Controls.Add(mainPanel);
            this.Controls.Add(toolBar);
            this.Controls.Add(statusStrip);
        }
        
        private void InitializeCore()
        {
            coreClient = new NestCoreClient();
            coreClient.OnLog += CoreClient_OnLog;
            coreClient.OnStatusChanged += CoreClient_OnStatusChanged;
        }
        
        private void LoadDefaultScripts()
        {
            // Load built-in scripts
            AddScript("Clock", @"-- Clock Display
local Players = game:GetService(""Players"")
local player = Players.LocalPlayer

while true do
    local time = os.date(""%H:%M:%S"")
    player:Chat(""Current time: "" .. time, false)
    wait(1)
end");
            
            AddScript("FPS Counter", @"-- FPS Counter
local Stats = game:GetService(""Stats"")
local Players = game:GetService(""Players"")
local player = Players.LocalPlayer

while true do
    wait(1)
    local fps = Stats.FPS
    player:Chat(""FPS: "" .. tostring(fps), false)
end");
            
            AddScript("ESP", @"-- ESP (Visual Only)
local Players = game:GetService(""Players"")
local Workspace = game:GetService(""Workspace"")
local RunService = game:GetService(""RunService"")

local function createESP(player)
    local character = player.Character
    if not character then return end
    
    local head = character:FindFirstChild(""Head"")
    if not head then return end
    
    local billboard = Instance.new(""BillboardGui"")
    billboard.Size = UDim2.new(0, 200, 0, 50)
    billboard.StudsOffset = Vector3.new(0, 2, 0)
    billboard.Adornee = head
    billboard.Parent = head
    
    local label = Instance.new(""TextLabel"")
    label.Size = UDim2.new(1, 0, 1, 0)
    label.BackgroundTransparency = 1
    label.Text = player.Name .. "" | HP: ??? ""
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

Players.PlayerAdded:Connect(createESP)");
            
            AddScript("Debug Inspector", @"-- Debug Inspector
local Players = game:GetService(""Players"")
local Workspace = game:GetService(""Workspace"")
local RunService = game:GetService(""RunService"")
local Stats = game:GetService(""Stats"")

local function inspect()
    local info = {
        players = #Players:GetPlayers(),
        workspace_objects = #Workspace:GetChildren(),
        fps = Stats.FPS,
        memory = Stats.MemoryUsage,
        ping = Stats.Network.ServerReplicationLatency,
    }
    
    for key, value in pairs(info) do
        print(key .. "": "" .. tostring(value))
    end
end

while true do
    inspect()
    wait(5)
end");
        }
        
        private void AddScript(string name, string content)
        {
            var script = new ScriptItem(name, content);
            scripts.Add(script);
            scriptList.Items.Add($"{script.Name} ({script.ShortHash})");
            scriptList.SelectedItem = scriptList.Items[scriptList.Items.Count - 1];
        }
        
        private void AddScriptBtn_Click(object sender, EventArgs e)
        {
            using (var dialog = new OpenFileDialog())
            {
                dialog.Filter = "Lua/Luau Files|*.lua;*.luau|All Files|*.*";
                dialog.Title = "Load Script";
                
                if (dialog.ShowDialog() == DialogResult.OK)
                {
                    var content = File.ReadAllText(dialog.FileName);
                    var name = Path.GetFileNameWithoutExtension(dialog.FileName);
                    AddScript(name, content);
                    Log($"Loaded script: {name}");
                }
            }
        }
        
        private void DeleteScriptBtn_Click(object sender, EventArgs e)
        {
            if (scriptList.SelectedIndex >= 0)
            {
                var selected = (ScriptItem)scriptList.SelectedItem;
                scripts.Remove(selected);
                scriptList.Items.Remove(selected);
                codeEditor.Clear();
                Log($"Deleted script: {selected.Name}");
            }
        }
        
        private void ScriptList_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (scriptList.SelectedItem is ScriptItem script)
            {
                codeEditor.Text = script.Content;
            }
        }
        
        private void ExecuteBtn_Click(object sender, EventArgs e)
        {
            if (scriptList.SelectedItem is not ScriptItem script)
            {
                MessageBox.Show("Please select a script first!", "Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
            
            if (!isInjected)
            {
                MessageBox.Show("Not injected! Please click Inject first.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
            
            // Execute script
            ExecuteScript(script);
        }
        
        private async void ExecuteScript(ScriptItem script)
        {
            executeBtn.Enabled = false;
            executeBtn.Text = "⏳ Running...";
            
            try
            {
                var result = await coreClient.ExecuteScriptAsync(script.Content);
                
                if (result.Success)
                {
                    Log($"[SUCCESS] {script.Name} executed in {result.ExecutionTime:F3}s");
                    if (!string.IsNullOrEmpty(result.Output))
                        Log($"  Output: {result.Output}");
                }
                else
                {
                    Log($"[FAILED] {script.Name}: {result.Error}");
                }
            }
            catch (Exception ex)
            {
                Log($"[ERROR] {ex.Message}");
            }
            finally
            {
                executeBtn.Enabled = true;
                executeBtn.Text = "▶ Execute";
            }
        }
        
        private void InjectBtn_Click(object sender, EventArgs e)
        {
            InjectBtn.BackColor = Color.Orange;
            InjectBtn.Text = "⏳ Injecting...";
            InjectBtn.Enabled = false;
            
            Task.Run(async () =>
            {
                try
                {
                    var result = await coreClient.InjectAsync();
                    
                    Invoke(() =>
                    {
                        isInjected = result.Success;
                        UpdateStatus();
                        InjectBtn.BackColor = isInjected ? Color.LimeGreen : Color.OrangeRed;
                        InjectBtn.Text = isInjected ? "✓ Injected" : "🔌 Inject";
                        
                        if (result.Success)
                            Log("[SUCCESS] Injection completed!");
                        else
                            Log($"[FAILED] {result.Error}");
                    });
                }
                catch (Exception ex)
                {
                    Invoke(() =>
                    {
                        Log($"[ERROR] {ex.Message}");
                        InjectBtn.BackColor = Color.OrangeRed;
                        InjectBtn.Text = "🔌 Inject";
                    });
                }
                finally
                {
                    Invoke(() => InjectBtn.Enabled = true);
                }
            });
        }
        
        private void UninjectBtn_Click(object sender, EventArgs e)
        {
            coreClient.Uninject();
            isInjected = false;
            UpdateStatus();
            Log("[INFO] Uninjected");
        }
        
        private void PlatformCombo_SelectedIndexChanged(object sender, EventArgs e)
        {
            currentPlatform = platformCombo.SelectedItem.ToString().ToLower();
            Log($"[INFO] Platform changed to: {currentPlatform}");
        }
        
        private void UpdateStatus()
        {
            statusLabel.Text = $"Platform: {currentPlatform.ToUpper()} | Scripts: {scripts.Count}";
            injectStatusLabel.Text = isInjected ? "✓ Injected" : "✗ Not Injected";
            injectStatusLabel.ForeColor = isInjected ? Color.Green : Color.Red;
        }
        
        private void CoreClient_OnLog(string message)
        {
            Invoke(() =>
            {
                consoleOutput.AppendText($"[{DateTime.Now:HH:mm:ss}] {message}\n");
                consoleOutput.ScrollToCaret();
            });
        }
        
        private void CoreClient_OnStatusChanged(bool injected)
        {
            Invoke(() =>
            {
                isInjected = injected;
                UpdateStatus();
            });
        }
    }
    
    /// <summary>
    /// Script item representation
    /// </summary>
    public class ScriptItem
    {
        public string Name { get; set; }
        public string Content { get; set; }
        public string Hash { get; set; }
        public string ShortHash => Hash?.Substring(0, 8) ?? "unknown";
        
        public ScriptItem(string name, string content)
        {
            Name = name;
            Content = content;
            Hash = BitConverter.ToString(System.Text.Encoding.UTF8.GetBytes(content)).Replace("-", "").Substring(0, 16).ToLower();
        }
        
        public override string ToString() => Name;
    }
    
    /// <summary>
    /// Execution result
    /// </summary>
    public class ExecutionResult
    {
        public bool Success { get; set; }
        public string Output { get; set; }
        public string Error { get; set; }
        public double ExecutionTime { get; set; }
    }
    
    /// <summary>
    /// Client for NestCore IPC
    /// </summary>
    public class NestCoreClient
    {
        private const string DefaultHost = "127.0.0.1";
        private int port = 17841;
        private bool connected = false;
        
        public event Action<string> OnLog;
        public event Action<bool> OnStatusChanged;
        
        private System.Net.Sockets.TcpClient client;
        private System.IO.Stream stream;
        
        public NestCoreClient()
        {
        }
        
        public async Task<ExecutionResult> ExecuteScriptAsync(string scriptContent)
        {
            try
            {
                var request = new
                {
                    command = "execute",
                    content = scriptContent,
                    timestamp = DateTime.Now.Ticks
                };
                
                var response = await SendRequestAsync(request);
                
                return new ExecutionResult
                {
                    Success = response.ContainsKey("success") && response["success"].ToString() == "True",
                    Output = response.GetValueOrDefault("output", ""),
                    Error = response.GetValueOrDefault("error", ""),
                    ExecutionTime = double.TryParse(response.GetValueOrDefault("execution_time", "0"), out var t) ? t : 0
                };
            }
            catch (Exception ex)
            {
                OnLog?.Invoke($"Execute error: {ex.Message}");
                return new ExecutionResult { Success = false, Error = ex.Message };
            }
        }
        
        public async Task<ExecutionResult> InjectAsync()
        {
            try
            {
                var request = new
                {
                    command = "inject",
                    platform = "windows",
                    timestamp = DateTime.Now.Ticks
                };
                
                var response = await SendRequestAsync(request);
                
                var success = response.ContainsKey("success") && response["success"].ToString() == "True";
                OnStatusChanged?.Invoke(success);
                
                return new ExecutionResult
                {
                    Success = success,
                    Error = response.GetValueOrDefault("error", "")
                };
            }
            catch (Exception ex)
            {
                OnLog?.Invoke($"Inject error: {ex.Message}");
                return new ExecutionResult { Success = false, Error = ex.Message };
            }
        }
        
        public void Uninject()
        {
            try
            {
                var request = new
                {
                    command = "uninject",
                    timestamp = DateTime.Now.Ticks
                };
                
                SendRequestAsync(request).Wait();
                OnStatusChanged?.Invoke(false);
            }
            catch (Exception ex)
            {
                OnLog?.Invoke($"Uninject error: {ex.Message}");
            }
        }
        
        private async Task<Dictionary<string, object>> SendRequestAsync(object request)
        {
            var json = JsonConvert.SerializeObject(request);
            var bytes = System.Text.Encoding.UTF8.GetBytes(json);
            
            using (var client = new System.Net.Sockets.TcpClient())
            {
                await client.ConnectAsync(DefaultHost, port);
                
                using (var stream = client.GetStream())
                {
                    // Send length prefix
                    var lengthBytes = System.BitConverter.GetBytes(bytes.Length);
                    stream.Write(lengthBytes, 0, 4);
                    stream.Write(bytes, 0, bytes.Length);
                    stream.Flush();
                    
                    // Read response
                    var responseBytes = new System.Text.StringBuilder();
                    byte[] buffer = new byte[4096];
                    
                    while (true)
                    {
                        int read = stream.Read(buffer, 0, buffer.Length);
                        if (read == 0) break;
                        responseBytes.Append(System.Text.Encoding.UTF8.GetString(buffer, 0, read));
                        
                        if (responseBytes.Length >= 4)
                        {
                            var lenStr = responseBytes.ToString().Substring(0, 4);
                            if (int.TryParse(lenStr, out int len) && len > 0 && responseBytes.Length >= len + 4)
                                break;
                        }
                    }
                    
                    var responseJson = responseBytes.ToString();
                    // Remove length prefix
                    if (responseJson.Length > 4)
                        responseJson = responseJson.Substring(4);
                    
                    return JsonConvert.DeserializeObject<Dictionary<string, object>>(responseJson) 
                           ?? new Dictionary<string, object>();
                }
            }
        }
    }
    
    /// <summary>
    /// Program entry point
    /// </summary>
    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }
    }
}
