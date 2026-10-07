local luckPassive = "GSL_Desperado_DesperadosLuckUnlock"
local fortunePassive = "GSL_Desperado_DesperadosFortuneUnlock"
local desperadoClass = "4a518934-644d-4120-ae6a-d922cf7cac34"
local previewChannel = "GSL_FortunePreview"
local activePreviews = {}
local selectionSwaps = {}
local heartbeatTicks = 0
local pollTicks = 6

Ext.Require("FortuneChooserDiagnostic.lua")
local updateChooserOwned = Ext.Require("FortuneChooserOwned.lua")

local function ownsFortune(handle)
    local entity = Ext.Entity.Get(handle)
    for _, passiveHandle in pairs(entity and entity.PassiveContainer and entity.PassiveContainer.Passives or {}) do
        local passiveEntity = Ext.Entity.Get(passiveHandle)
        if passiveEntity and passiveEntity.Passive and passiveEntity.Passive.PassiveId == fortunePassive then
            return true
        end
    end
    return false
end

local function isFortuneLevel(level)
    for _, selector in pairs(level.Upgrades.Passives) do
        if selector.Level == 15 and selector.SelectorId == "GritAbility" and
            tostring(selector.Class) == desperadoClass then return true end
    end
    return false
end

local function selectedLuck(levels)
    for _, level in pairs(levels) do
        for _, selector in pairs(level.Upgrades.Passives) do
            for _, passive in pairs(selector.Passives) do
                if passive == luckPassive then return true end
            end
        end
    end
    return false
end

local function restoreSelections(character, handles)
    -- Resolve fresh entity/array proxies; only primitive indices survive between ticks.
    for _, swap in ipairs(selectionSwaps[character] or {}) do
        local entity
        for _, handle in pairs(handles) do
            if tostring(handle) == swap.Session then
                entity = Ext.Entity.Get(handle)
                break
            end
        end
        local definition = entity and entity.CCLevelUpDefinition
        if definition and tostring(Ext.Entity.HandleToUuid(definition.Character)) == character then
            local level = definition.Definition.LevelUpData[swap.Level]
            local selector = level and level.Upgrades.Passives[swap.Selector]
            if selector and tostring(selector.PassiveList) == swap.PassiveList and
                selector.Passives[swap.Passive] == fortunePassive then
                selector.Passives[swap.Passive] = luckPassive
                assert(selector.Passives[swap.Passive] == luckPassive, "Unable to restore Luck preview selection")
            end
        end
    end
    selectionSwaps[character] = nil
end

local function swapSelections(character, session, levels)
    for levelIndex, level in pairs(levels) do
        for selectorIndex, selector in pairs(level.Upgrades.Passives) do
            for passiveIndex, passive in pairs(selector.Passives) do
                if passive == luckPassive then
                    local swaps = selectionSwaps[character] or {}
                    selectionSwaps[character] = swaps
                    swaps[#swaps + 1] = {
                        Session = session, Level = levelIndex, Selector = selectorIndex,
                        Passive = passiveIndex, PassiveList = tostring(selector.PassiveList)
                    }
                    selector.Passives[passiveIndex] = fortunePassive
                    assert(selector.Passives[passiveIndex] == fortunePassive,
                        "Unable to replace Luck in the level-up preview")
                end
            end
        end
    end
end

Ext.Events.SessionLoaded:Subscribe(function()
    if next(selectionSwaps) then
        local handles = Ext.Entity.GetAllEntitiesWithComponent("CCLevelUpDefinition")
        for character in pairs(selectionSwaps) do restoreSelections(character, handles) end
    end
    activePreviews = {}
    heartbeatTicks = 0
    pollTicks = 6
end)

Ext.Events.Tick:Subscribe(function()
    heartbeatTicks = heartbeatTicks + 1
    pollTicks = pollTicks + 1
    if pollTicks < 6 then return end
    pollTicks = 0
    local handles = Ext.Entity.GetAllEntitiesWithComponent("CCLevelUpDefinition")
    -- Restore our changes before evaluating eligibility, so a changed/respec build is not
    -- kept eligible merely because the previous preview contained substituted Fortune.
    for character in pairs(selectionSwaps) do restoreSelections(character, handles) end
    local currentPreviews = {}
    local eligibleOwned = false
    local conflictingPreview = false
    for _, handle in pairs(handles) do
        local entity = Ext.Entity.Get(handle)
        local definition = entity and entity.CCLevelUpDefinition
        if definition and isFortuneLevel(definition.LevelUp.LevelUpData) and
            selectedLuck(definition.Definition.LevelUpData) then
            local uuid = assert(Ext.Entity.HandleToUuid(definition.Character), "Fortune preview character has no UUID")
            local character = tostring(uuid)
            currentPreviews[character] = true
            if not activePreviews[character] or heartbeatTicks >= 30 then
                Ext.ClientNet.PostMessageToServer(previewChannel,
                    Ext.Json.Stringify({Character = character, Open = true}))
            end
            if ownsFortune(definition.Character) then
                eligibleOwned = true
                swapSelections(character, tostring(handle),
                    definition.Definition.LevelUpData)
            else
                conflictingPreview = true
            end
        elseif definition then
            conflictingPreview = true
        end
    end
    for character in pairs(activePreviews) do
        if not currentPreviews[character] then
            Ext.ClientNet.PostMessageToServer(previewChannel,
                Ext.Json.Stringify({Character = character, Open = false}))
        end
    end
    activePreviews = currentPreviews
    if heartbeatTicks >= 30 then heartbeatTicks = 0 end
    updateChooserOwned(eligibleOwned and not conflictingPreview)
end)
