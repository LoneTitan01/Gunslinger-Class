local outputFile = "GunslingerFortuneChooser.json"
local luck = "GSL_Desperado_DesperadosLuckUnlock"
local fortune = "GSL_Desperado_DesperadosFortuneUnlock"

local function summarize(value)
    local result = {}
    for key, property in pairs(value) do
        local kind = type(property)
        if kind == "string" or kind == "number" or kind == "boolean" then
            result[tostring(key)] = property
        else
            result[tostring(key)] = tostring(property)
        end
    end
    return result
end

local function reflectedProperties(object)
    local kind = type(object)
    if kind == "nil" or kind == "string" or kind == "number" or kind == "boolean" or
        kind == "function" or kind == "thread" then return nil end
    if type(object.TypeInfo) ~= "function" then return nil end
    local properties = {}
    local info = object:TypeInfo()
    while info do
        for _, property in pairs(info.Properties) do
            properties[tostring(property.Name)] = {ReadOnly = property.IsReadOnly}
        end
        for _, property in pairs(info.DependencyProperties) do
            properties[tostring(property.Name)] = {ReadOnly = property.IsReadOnly}
        end
        info = info.Base
    end
    return properties
end

local function selectionHistory(levels)
    local result = {}
    for index, level in pairs(levels) do
        for selectorIndex, selector in pairs(level.Upgrades.Passives) do
            local passives = {}
            for passiveIndex, passive in pairs(selector.Passives) do
                passives[tostring(passiveIndex)] = passive
            end
            result[#result + 1] = {
                Index = index, SelectorIndex = selectorIndex, Level = selector.Level,
                Class = tostring(selector.Class), SelectorId = selector.SelectorId,
                PassiveList = tostring(selector.PassiveList), Passives = passives
            }
        end
    end
    return result
end

local function ownedPassives(handle)
    local entity = Ext.Entity.Get(handle)
    local result = {}
    for _, passiveHandle in pairs(entity and entity.PassiveContainer and entity.PassiveContainer.Passives or {}) do
        local passiveEntity = Ext.Entity.Get(passiveHandle)
        local passive = passiveEntity and passiveEntity.Passive
        if passive and (passive.PassiveId == luck or passive.PassiveId == fortune) then
            result[#result + 1] = {Id = passive.PassiveId, Source = tostring(passive.Type)}
        end
    end
    return result
end

Ext.RegisterConsoleCommand("gsl_fortune_chooser", function()
    local root = assert(Ext.UI.GetRoot(), "No client UI root; open the level-15 grit chooser first")
    local capture = {Sessions = {}, ContextTypes = {}, Rows = {}, Selectors = {}, NodesVisited = 0}
    for _, handle in pairs(Ext.Entity.GetAllEntitiesWithComponent("CCLevelUpDefinition")) do
        local entity = Ext.Entity.Get(handle)
        local definition = entity.CCLevelUpDefinition
        local session = {
            Session = tostring(handle), Character = tostring(definition.Character),
            ChangeId = definition.ChangeId, NeedsSync = definition.NeedsSync,
            PreviewHistory = selectionHistory(definition.Definition.LevelUpData),
            CurrentSelection = selectionHistory({definition.LevelUp.LevelUpData}),
            CharacterPassives = ownedPassives(definition.Character)
        }
        local character = Ext.Entity.Get(definition.Character)
        if character and character.LevelUp then
            session.CharacterHistory = selectionHistory(character.LevelUp.LevelUps)
        end
        if entity.ClientCCLevelUpDefinition then
            session.ClientSelection = selectionHistory({entity.ClientCCLevelUpDefinition.Definition.LevelUpData})
        end
        if entity.ClientCCDummyDefinition then
            session.Dummy = tostring(entity.ClientCCDummyDefinition.Dummy)
            session.DummyPassives = ownedPassives(entity.ClientCCDummyDefinition.Dummy)
        end
        capture.Sessions[#capture.Sessions + 1] = session
    end
    assert(#capture.Sessions > 0, "No level-up session; open the level-15 grit chooser first")
    local fortuneName = Ext.Loca.GetTranslatedString("h00000027g0000g4000g8000g000000000001")
    local seen = {}
    local stack = {{Node = root, Path = "Root"}}
    local started = Ext.Timer.MicrosecTime()
    while #stack > 0 do
        if capture.NodesVisited >= 20000 or Ext.Timer.MicrosecTime() - started >= 1000000 then
            capture.Truncated = true
            break
        end
        local entry = table.remove(stack)
        local node = entry.Node
        capture.NodesVisited = capture.NodesVisited + 1
        local nodeProperties = reflectedProperties(node)
        if nodeProperties and nodeProperties.DataContext then
            local context = node.DataContext
            if context then
                local nativeType = Ext.Types.GetObjectType(context)
                local contextType = nativeType or type(context)
                local properties = reflectedProperties(context)
                local values
                if properties then
                    contextType = tostring(context.Type)
                    values = summarize(context:GetAllProperties())
                elseif type(context) == "table" then
                    values = summarize(context)
                end
                capture.ContextTypes[contextType] = (capture.ContextTypes[contextType] or 0) + 1
                local row = values and (
                    values.Name == fortuneName or values.IconName == "GSL_DesperadosFortune" or
                    contextType:find("VMCharacterCreationPassive", 1, true))
                if row then
                    local key = tostring(context)
                    if not seen[key] then
                        seen[key] = true
                        local record = {
                            Path = entry.Path, LuaType = type(context), NativeType = nativeType,
                            ContextType = contextType, Properties = properties, Values = values
                        }
                        if values.SelectedPassiveCount ~= nil then
                            capture.Selectors[#capture.Selectors + 1] = record
                        else
                            capture.Rows[#capture.Rows + 1] = record
                        end
                    end
                end
            end
        end
        for index = node.VisualChildrenCount, 1, -1 do
            local child = node:VisualChild(index)
            if child then
                stack[#stack + 1] = {Node = child, Path = entry.Path .. "." .. index}
            end
        end
    end
    capture.FortuneName = fortuneName
    Ext.IO.SaveFile(outputFile, Ext.Json.Stringify(capture))
    Ext.Utils.Print("[Gunslinger] Manual chooser capture saved to " .. outputFile ..
        " (" .. #capture.Rows .. " passive rows, " .. capture.NodesVisited .. " UI nodes).")
    if capture.Truncated or #capture.Rows == 0 then
        Ext.Utils.Print("[Gunslinger] WARNING: capture incomplete or no passive rows found; include the file anyway.")
    end
end)
