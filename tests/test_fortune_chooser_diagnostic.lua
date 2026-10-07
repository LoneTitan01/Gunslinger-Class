local command, saved, prints
prints = {}
local function model(values)
    return {
        Type = values.Type,
        TypeInfo = function()
            local properties = {}
            for key in pairs(values) do properties[#properties + 1] = {Name = key, IsReadOnly = true} end
            return {Properties = properties, DependencyProperties = {}}
        end,
        GetAllProperties = function() return values end
    }
end
local fortuneRow = model({
    Type = "ls.VMCharacterCreationPassive", Name = "Desperado's Fortune", Value = 0,
    Enabled = true, IconName = "GSL_DesperadosFortune"
})
local luckRow = model({
    Type = "ls.VMCharacterCreationPassive", Name = "Desperado's Luck", Value = 1,
    Enabled = false, IconName = "GSL_DesperadosLuck"
})
local selectorModel = model({
    Type = "ls.VMCharacterCreationPassives", Name = "Grit abilities", SelectedPassiveCount = 0,
    MaxSelectedPassiveCount = 1
})
local function node(context, children)
    return {
        DataContext = context, VisualChildrenCount = #children,
        TypeInfo = function() return {Properties = {}, DependencyProperties = {{Name = "DataContext"}}} end,
        VisualChild = function(_, index)
            assert(index >= 1 and index <= #children)
            return children[index]
        end
    }
end
local root = node(nil, {
    node("scalar context", {}), node({SomeField = true}, {}),
    node(fortuneRow, {}), node(luckRow, {}), node(selectorModel, {})
})
local selector = {Level = 5, Class = "desperado", SelectorId = "GritAbility",
    PassiveList = "pool", Passives = {"GSL_Desperado_DesperadosLuckUnlock"}}
local history = {{Upgrades = {Passives = {selector}}}}
local definition = {
    ChangeId = 17, NeedsSync = false, Character = "character",
    Definition = {LevelUpData = history}, LevelUp = {LevelUpData = history[1]}
}
local entities = {
    session = {CCLevelUpDefinition = definition, ClientCCDummyDefinition = {Dummy = "dummy"}},
    character = {LevelUp = {LevelUps = history}, PassiveContainer = {Passives = {"fortune"}}},
    dummy = {PassiveContainer = {Passives = {}}},
    fortune = {Passive = {PassiveId = "GSL_Desperado_DesperadosFortuneUnlock", Type = "Feat"}}
}
local now, timeStep = 0, 0
Ext = {
    RegisterConsoleCommand = function(name, callback) assert(name == "gsl_fortune_chooser"); command = callback end,
    -- Noesis proxies are not covered by the generic GetObjectType switch in bg3se.
    Types = {GetObjectType = function() return nil end},
    UI = {GetRoot = function() return root end},
    Entity = {
        GetAllEntitiesWithComponent = function() return {"session"} end,
        Get = function(handle) return entities[handle] end
    },
    Loca = {GetTranslatedString = function() return "Desperado's Fortune" end},
    Timer = {MicrosecTime = function() now = now + timeStep; return now end},
    Json = {Stringify = function(value) return value end},
    IO = {SaveFile = function(path, value) assert(path == "GunslingerFortuneChooser.json"); saved = value end},
    Utils = {Print = function(message) prints[#prints + 1] = message end}
}
dofile("GunslingerClass\\Mods\\GunslingerClass\\ScriptExtender\\Lua\\FortuneChooserDiagnostic.lua")
assert(command and not saved and #prints == 0, "Registration must not capture or print automatically")
command()
assert(#saved.Rows == 2 and #saved.Selectors == 1 and saved.NodesVisited == 6)
assert(saved.Rows[1].Values.Value == 0 and saved.Rows[1].Values.Enabled == true and
    saved.Rows[1].Properties.Value.ReadOnly, "Capture actual unchecked Fortune and property writability")
assert(saved.Rows[2].Values.Value == 1 and not saved.Rows[2].Values.Enabled,
    "Capture checked Luck for comparison")
assert(saved.Sessions[1].ChangeId == 17 and saved.Sessions[1].NeedsSync == false and
    saved.Sessions[1].CharacterPassives[1].Id == "GSL_Desperado_DesperadosFortuneUnlock")
assert(fortuneRow:GetAllProperties().Value == 0 and selector.Passives[1] ==
    "GSL_Desperado_DesperadosLuckUnlock", "The diagnostic must not modify row state or selections")
timeStep = 1000001
command()
assert(saved.Truncated and #prints == 3, "A bounded capture must explicitly report truncation")
print("Fortune chooser diagnostic passed: manual-only capture, native row values, read-only state, mixed contexts, selection snapshots and explicit truncation")
