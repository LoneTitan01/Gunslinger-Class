local passiveType = "ls.VMCharacterCreationPassive"
local wrapperType = "GSL_OwnedFortuneBindings"
local fortuneName = "h00000027g0000g4000g8000g000000000001"
local registered = false
local propertyCache = {}
local owned = false
local paths = {}
local scanPath
local scanCounts = {}
local ticks = 120

local function propertiesOf(node)
    local typeName = tostring(node.Type)
    if propertyCache[typeName] == nil then
        local properties = {}
        local info = node:TypeInfo()
        while info do
            for _, property in pairs(info.Properties) do
                properties[tostring(property.Name)] = true
            end
            for _, property in pairs(info.DependencyProperties) do
                properties[tostring(property.Name)] = true
            end
            info = info.Base
        end
        propertyCache[typeName] = properties
    end
    return propertyCache[typeName]
end

local function preserveTooltipModel(node, original)
    local properties = propertiesOf(node)
    if properties.ToolTip then
        local tooltip = node.ToolTip
        local kind = type(tooltip)
        if (kind == "table" or kind == "userdata") and type(tooltip.TypeInfo) == "function" then
            local tooltipProperties = propertiesOf(tooltip)
            if tooltipProperties.DataContext then tooltip.DataContext = original end
            if tooltipProperties.Content then tooltip.Content = original end
        end
    end
    for index = 1, node.VisualChildrenCount do
        local child = node:VisualChild(index)
        if child then preserveTooltipModel(child, original) end
    end
end

local function updateRow(node)
    local properties = propertiesOf(node)
    if not properties.DataContext or not properties.IsEnabled then return false end
    local context = node.DataContext
    local kind = type(context)
    if (kind ~= "table" and kind ~= "userdata") or type(context.TypeInfo) ~= "function" then return false end
    local typeName = tostring(context.Type)
    if typeName == "se::" .. wrapperType then
        preserveTooltipModel(node, context.Original)
        if not owned then
            node.DataContext = context.Original
        end
        return true
    end
    if typeName ~= passiveType or tostring(context.Name) ~= fortuneName or
        tostring(context.IconName) ~= "GSL_DesperadosFortune" then return false end
    if owned and not (context.Value == 1 and context.Enabled == false) then
        if not registered then
            assert(Ext.UI.RegisterType(wrapperType, {
                Value = {Type = "Double", Notify = true},
                Enabled = {Type = "Bool", Notify = true},
                Original = {Type = "Object"}
            }, passiveType), "Unable to register Fortune chooser ownership wrapper")
            registered = true
        end
        local wrapper = assert(Ext.UI.Instantiate("se::" .. wrapperType, context),
            "Unable to create Fortune chooser ownership wrapper")
        wrapper.Original = context
        wrapper.Value = 1
        wrapper.Enabled = false
        node.DataContext = wrapper
        preserveTooltipModel(node, context)
    end
    return true
end

local function resolve(root, path)
    local node = root
    for _, index in ipairs(path) do
        if not node or index > node.VisualChildrenCount then return nil end
        node = node:VisualChild(index)
    end
    return node
end

local function copyPath(path)
    local result = {}
    for index, value in ipairs(path) do result[index] = value end
    return result
end

local function resetScan()
    scanPath = {}
    scanCounts = {}
    paths = {}
end

local function scan(root)
    local started = Ext.Timer.MicrosecTime()
    for _ = 1, 24 do
        if Ext.Timer.MicrosecTime() - started >= 500 then return end
        local node = resolve(root, scanPath)
        local found = node and updateRow(node)
        if found then paths[#paths + 1] = copyPath(scanPath) end
        local count = node and not found and node.VisualChildrenCount or 0
        if count > 0 then
            scanCounts[#scanPath + 1] = count
            scanPath[#scanPath + 1] = 1
        else
            while #scanPath > 0 and scanPath[#scanPath] >= scanCounts[#scanPath] do
                scanCounts[#scanPath] = nil
                scanPath[#scanPath] = nil
            end
            if #scanPath == 0 then
                scanPath = nil
                ticks = 0
                return
            end
            scanPath[#scanPath] = scanPath[#scanPath] + 1
        end
    end
end

return function(shouldOwn)
    ticks = ticks + 6
    local changed = owned ~= shouldOwn
    owned = shouldOwn
    if not owned and not changed and not scanPath then return end
    local root = Ext.UI.GetRoot()
    if not root then
        scanPath = nil
        paths = {}
        return
    end
    local stale = false
    for _, path in ipairs(paths) do
        local node = resolve(root, path)
        if not node or not updateRow(node) then stale = true end
    end
    if changed or stale or (owned and #paths == 0 and not scanPath and ticks >= 120) then resetScan() end
    -- Engine proxies are local to this call. Only primitive index paths are cached.
    if scanPath then scan(root) end
end
