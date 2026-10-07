local events, entities, messages = {}, {}, {}
local sessions = {"session"}
local luck = "GSL_Desperado_DesperadosLuckUnlock"
local fortune = "GSL_Desperado_DesperadosFortuneUnlock"
local selector = {
    Class = "4a518934-644d-4120-ae6a-d922cf7cac34", Level = 15,
    SelectorId = "GritAbility", Passives = {""}
}
local current = {Upgrades = {Passives = {selector}}}
local definition = {LevelUp = {LevelUpData = current}, Definition = {LevelUpData = {}}, Character = "character"}
entities.session = {CCLevelUpDefinition = definition}
local originalHistory = {{Upgrades = {Passives = {{Passives = {luck}}}}}}
entities.character = {PassiveContainer = {Passives = {}}, LevelUp = {LevelUps = originalHistory}}
entities.fortune = {Passive = {PassiveId = fortune}}
local scans = 0
local chooserOwned = false
Ext = {
    Require = function(file)
        if file == "FortuneChooserOwned.lua" then
            return function(owned) chooserOwned = owned end
        end
        assert(file == "FortuneChooserDiagnostic.lua")
        return dofile("GunslingerClass\\Mods\\GunslingerClass\\ScriptExtender\\Lua\\" .. file)
    end,
    RegisterConsoleCommand = function(name, callback)
        assert(name == "gsl_fortune_chooser" and type(callback) == "function")
    end,
    Entity = {
        Get = function(handle) return entities[handle] end,
        HandleToUuid = function(handle) return handle end,
        GetAllEntitiesWithComponent = function(component)
            assert(component == "CCLevelUpDefinition")
            scans = scans + 1
            return sessions
        end
    },
    Events = {}, Json = {Stringify = function(message) return message end},
    ClientNet = {PostMessageToServer = function(channel, message)
        assert(channel == "GSL_FortunePreview")
        messages[#messages + 1] = message
    end},
    UI = {GetRoot = function() error("UI traversal must not run") end},
    Utils = {Print = function() error("Debug output must not run") end},
    IO = {SaveFile = function() error("Debug file writes must not run") end}
}
for _, name in ipairs({"SessionLoaded", "Tick"}) do
    Ext.Events[name] = {Subscribe = function(_, callback) events[name] = callback end}
end
dofile("GunslingerClass\\Mods\\GunslingerClass\\ScriptExtender\\Lua\\BootstrapClient.lua")
local function poll() for _ = 1, 6 do events.Tick() end end
events.SessionLoaded()
poll()
assert(#messages == 0, "Without Luck the chooser must remain unchanged")
for _, chosenLevel in ipairs({5, 7, 9, 11, 13}) do
    local history = {}
    for level = 1, 14 do
        history[level] = {Upgrades = {Passives = {}}}
        if level >= 5 and level % 2 == 1 then
            history[level].Upgrades.Passives[1] = {
                Level = level, PassiveList = "pool-" .. level,
                Passives = {level == chosenLevel and luck or "AnotherAbility", "UnchangedAbility"}
            }
        end
    end
    definition.Definition.LevelUpData = history
    entities.character.PassiveContainer.Passives = {}
    selector.Level = 15
    poll()
    assert(messages[#messages].Open and history[chosenLevel].Upgrades.Passives[1].Passives[1] == luck,
        "The preview must wait for actual Fortune ownership")
    assert(not chooserOwned, "The owned-row override must wait for the actual class feature")
    entities.character.PassiveContainer.Passives = {"fortune"}
    poll()
    local chosen = history[chosenLevel].Upgrades.Passives[1]
    assert(chosen.Passives[1] == fortune and chosen.Passives[2] == "UnchangedAbility",
        "Replace only the Luck stat ID at the original chosen level " .. chosenLevel)
    assert(chooserOwned, "Replicated Fortune must activate the native owned-row override")
    assert(selector.Passives[1] == "" and chosen.PassiveList == "pool-" .. chosenLevel,
        "The level-15 choice and shared pool IDs must not change")
    for _ = 1, 60 do events.Tick() end
    assert(chosen.Passives[1] == fortune and messages[#messages].Open,
        "Renewal must preserve preview eligibility after replacing Luck")
    selector.Level = 14
    poll()
    assert(chosen.Passives[1] == luck and not messages[#messages].Open,
        "Cancellation must revert the original selection at level " .. chosenLevel)
    assert(not chooserOwned, "Cancellation must restore the native chooser row")
    selector.Level = 15
    poll()
    assert(chosen.Passives[1] == fortune, "Reopening must swap the original Luck choice again")
    chosen.Passives[1] = "DifferentRespecChoice"
    poll()
    assert(chosen.Passives[1] == "DifferentRespecChoice" and not messages[#messages].Open,
        "Restoration must not overwrite a subsequent player selection")
end
definition.Definition.LevelUpData = {{Upgrades = {Passives = {{PassiveList = "pool", Passives = {luck}}}}}}
poll()
assert(definition.Definition.LevelUpData[1].Upgrades.Passives[1].Passives[1] == fortune)
events.SessionLoaded()
assert(definition.Definition.LevelUpData[1].Upgrades.Passives[1].Passives[1] == luck,
    "Session reload must restore reachable preview history")
local before = scans
for _ = 1, 60 do events.Tick() end
assert(scans - before <= 11, "Eligibility scanning must remain throttled")
local otherPick = {PassiveList = "other-pool", Passives = {luck}}
local otherDefinition = {
    LevelUp = {LevelUpData = current}, Definition = {LevelUpData = {{Upgrades = {Passives = {otherPick}}}}},
    Character = "other-character"
}
entities.otherSession = {CCLevelUpDefinition = otherDefinition}
entities["other-character"] = {PassiveContainer = {Passives = {"fortune"}}}
sessions[2] = "otherSession"
poll()
assert(otherPick.Passives[1] == fortune and
    definition.Definition.LevelUpData[1].Upgrades.Passives[1].Passives[1] == fortune,
    "Two eligible characters must independently swap their original picks")
otherDefinition.LevelUp.LevelUpData = {Upgrades = {Passives = {}}}
poll()
assert(not chooserOwned, "Mixed simultaneous previews must not apply the override to an ineligible character")
assert(otherPick.Passives[1] == luck and
    definition.Definition.LevelUpData[1].Upgrades.Passives[1].Passives[1] == fortune,
    "Cancelling one character must not revert the other character's preview")
sessions[2] = nil
sessions = {}
entities.session = nil
poll()
assert(originalHistory[1].Upgrades.Passives[1].Passives[1] == luck and not messages[#messages].Open,
    "Destroying the preview must leave the actual character's recorded Luck unchanged")
print("Fortune preview passed: temporary stat-ID replacement at levels 5/7/9/11/13, cancellation, respec edits, reload, throttling and no UI traversal")
