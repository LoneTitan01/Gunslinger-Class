local Rules = Ext.Require("GritRules.lua")
local templates = {
    ["3d8b177d-89db-4826-8068-9f2d777faf04"] = "Flintlock",
    ["a710ad68-179b-4b0e-8ef2-3b37609a3f12"] = "Flintlock",
    ["4a7854fd-718a-4a4e-b9db-3875b5788065"] = "Blunderbuss",
    ["1da91e88-3f0e-4ccc-ac25-0bdf00426880"] = "Musket"
}
local slots = {Main = "Ranged Main Weapon", Off = "Ranged Offhand Weapon"}
local casts = {}
local refreshing = {}
local pendingRefresh = {}
local pendingLastWord = {}
local recentAttackers = {}
local pendingAttackTargets = {}
local pendingSessionRefresh = false
local cleanupRemovedAbilities

Ext.Vars.RegisterModVariable(Rules.ModuleUUID, "Firearms", {
    Server = true, WriteableOnServer = true, Persistent = true
})

local function database()
    local vars = Ext.Vars.GetModVariables(Rules.ModuleUUID)
    if not vars.Firearms then vars.Firearms = {weapons = {}, owners = {}} end
    return vars.Firearms
end

local function save(data)
    Ext.Vars.GetModVariables(Rules.ModuleUUID).Firearms = data
end

local hotStreakStatus = "GSL_HOT_STREAK"
local hotStreakCounterStatus = "GSL_HOT_STREAK_COUNTER"
local hotStreakSource = "GSL_HOT_STREAK"

local function clearHotStreak(character)
    local data = database()
    local streak = data.hotStreaks and data.hotStreaks[character]
    if type(streak) == "table" and streak.boost then
        Osi.RemoveBoosts(character, streak.boost, 0, hotStreakSource, character)
    end
    if data.hotStreaks then data.hotStreaks[character] = nil end
    save(data)
    Osi.RemoveStatus(character, hotStreakCounterStatus)
end

local luckPassive = "GSL_Desperado_DesperadosLuckUnlock"
local fortunePassive = "GSL_Desperado_DesperadosFortuneUnlock"
local fortuneUpgradePassive = "GSL_Desperado_FortuneUpgrade"
local respecInProgress = {}
local pendingLuckCleanup = {}
local reportedLuckCleanup = {}
local fortunePreviewLeases = {}
local pendingFortunePreviewMessages = {}
local previewTick = 0

Ext.RegisterNetListener("GSL_FortunePreview", function(_, payload)
    local message = Ext.Json.Parse(payload)
    assert(type(message) == "table" and type(message.Character) == "string" and
        type(message.Open) == "boolean", "Invalid Fortune preview message")
    pendingFortunePreviewMessages[#pendingFortunePreviewMessages + 1] = message
end)

local function fortunePreviewEligible(character)
    local entity = Ext.Entity.Get(character)
    if not entity or Osi.HasPassive(character, luckPassive) ~= 1 then return false end
    local classLevels = 0
    for _, level in pairs(entity.LevelUp and entity.LevelUp.LevelUps or {}) do
        if tostring(level.Class) == "799af9fb-7ff1-4a4f-a9b3-041a16dbee0c" then
            classLevels = classLevels + 1
        end
    end
    return classLevels == 14
end

local function finishFortunePreview(character)
    local data = database()
    if not data.fortunePreviews or not data.fortunePreviews[character] then return end
    if not Ext.Entity.Get(character) then return end
    if Osi.HasPassive(character, fortuneUpgradePassive) == 1 and not respecInProgress[character] then
        data.fortuneUpgrades = data.fortuneUpgrades or {}
        data.fortuneUpgrades[character] = true
    else
        Osi.RemovePassive(character, fortunePassive)
    end
    data.fortunePreviews[character] = nil
    fortunePreviewLeases[character] = nil
    save(data)
end

local function updateFortunePreviews()
    previewTick = previewTick + 1
    local data = database()
    for _, message in ipairs(pendingFortunePreviewMessages) do
        local character = message.Character
        if message.Open then
            if data.fortunePreviews and data.fortunePreviews[character] then
                fortunePreviewLeases[character] = previewTick + 600
            elseif fortunePreviewEligible(character) and Osi.HasPassive(character, fortunePassive) ~= 1 then
                data.fortunePreviews = data.fortunePreviews or {}
                data.fortunePreviews[character] = true
                save(data)
                Osi.AddPassive(character, fortunePassive)
                fortunePreviewLeases[character] = previewTick + 600
            end
        elseif data.fortunePreviews and data.fortunePreviews[character] then
            -- Let progression changes settle before deciding whether the preview was confirmed.
            fortunePreviewLeases[character] = previewTick + 2
        end
    end
    pendingFortunePreviewMessages = {}
    for character, expires in pairs(fortunePreviewLeases) do
        if expires <= previewTick then finishFortunePreview(character) end
    end
end

local function selectedDesperadosLuck(character)
    local entity = assert(Ext.Entity.Get(character), "Desperado has no entity")
    for _, level in pairs(entity.LevelUp and entity.LevelUp.LevelUps or {}) do
        for _, selector in pairs(level.Upgrades.Passives) do
            for _, passive in pairs(selector.Passives) do
                if passive == luckPassive then return true end
            end
        end
    end
    return false
end

local function reportPersistentLuck(character)
    if reportedLuckCleanup[character] then return end
    reportedLuckCleanup[character] = true
    Ext.Utils.Print("[Gunslinger] WARNING: Luck remains owned after Fortune upgrade and RemovePassive: " .. character)
end

local function upgradeDesperadosLuck(character)
    if respecInProgress[character] then return end
    local data = database()
    if data.fortunePreviews and data.fortunePreviews[character] then
        if Osi.HasPassive(character, fortuneUpgradePassive) ~= 1 then return end
        finishFortunePreview(character)
    end
    local hasLuck = Osi.HasPassive(character, luckPassive) == 1
    local hasFortune = Osi.HasPassive(character, fortunePassive) == 1
    if not hasLuck then
        pendingLuckCleanup[character] = nil
    end
    if not hasFortune and (Osi.HasPassive(character, fortuneUpgradePassive) ~= 1 or
        (not hasLuck and not selectedDesperadosLuck(character))) then return end
    if not hasFortune then
        Osi.AddPassive(character, fortunePassive)
        local data = database()
        data.fortuneUpgrades = data.fortuneUpgrades or {}
        data.fortuneUpgrades[character] = true
        save(data)
    end
    if hasLuck then
        Osi.RemovePassive(character, luckPassive)
        pendingLuckCleanup[character] = 2
    end
end

local function refreshClassFeatures(character)
    upgradeDesperadosLuck(character)
    cleanupRemovedAbilities(character)
end

Ext.Osiris.RegisterListener("LeveledUp", 1, "after", refreshClassFeatures)
local function finishRespec(character)
    respecInProgress[character] = nil
    refreshClassFeatures(character)
end
Ext.Osiris.RegisterListener("RespecCompleted", 1, "after", finishRespec)
Ext.Osiris.RegisterListener("RespecCancelled", 1, "after", finishRespec)
Ext.Osiris.RegisterListener("StartRespec", 1, "before", function(character)
    respecInProgress[character] = true
    finishFortunePreview(character)
    cleanupRemovedAbilities(character)
    pendingLuckCleanup[character] = nil
    local data = database()
    if not data.fortuneUpgrades or not data.fortuneUpgrades[character] then return end
    -- Return script-granted upgrades to the original selection before the engine rebuilds the class.
    Osi.RemovePassive(character, fortunePassive)
    if Osi.HasPassive(character, fortuneUpgradePassive) == 1 then
        Osi.AddPassive(character, luckPassive)
    end
    data.fortuneUpgrades[character] = nil
    save(data)
end)

local function equipped(character, hand)
    local item = Osi.GetEquippedItem(character, slots[hand])
    if not item then return nil end
    local template = Osi.GetTemplate(item)
    local kind = template and templates[template:sub(-36):lower()]
    if not kind then return nil end
    return item, kind
end

local function itemState(data, item, kind)
    if not data.weapons[item] then
        data.weapons[item] = {kind = kind, ammo = Rules.Firearms[kind].capacity}
    end
    return data.weapons[item]
end

local function resource(character, hand, state)
    local entity = assert(Ext.Entity.Get(character), "Firearm wielder has no entity")
    local id = hand == "Off" and Rules.OffhandResource or Rules.Firearms[state.kind].resource
    local entries = assert(entity.ActionResources, "Wielder has no ActionResources").Resources[id]
    assert(entries, "Equipped firearm ammunition resource is missing: " .. id)
    for _, entry in pairs(entries) do
        if entry.Level == 0 then return entry, entity end
    end
    error("Ammunition resource has no level-zero entry: " .. id)
end

local function status(object, name, enabled)
    local present = Osi.HasActiveStatus(object, name) == 1
    if enabled and not present then Osi.ApplyStatus(object, name, -1, 1, object) end
    if not enabled and present then Osi.RemoveStatus(object, name) end
end

cleanupRemovedAbilities = function(character)
    -- Retire All In unlocks and dynamic boosts from existing saves.
    if Osi.HasPassive(character, "GSL_Desperado_AllInUnlock") == 1 then
        Osi.RemovePassive(character, "GSL_Desperado_AllInUnlock")
    end
    local data = database()
    local previous = data.allInBoosts and data.allInBoosts[character]
    if previous then
        Osi.RemoveBoosts(character, previous, 0, "GSL_AllIn", character)
        data.allInBoosts[character] = nil
        save(data)
    end
    status(character, "GSL_ALL_IN_READY", false)
end

local BonusActionPoint = "420c8df5-45c2-4253-93c2-7ec44e127930"
local reloadPollTicks = 0

-- Reload hotbar costs follow the bonus action: a bonus action while one remains, otherwise an action.
local function updateReloadCosts(character)
    local entity = Ext.Entity.Get(character)
    local resources = entity and entity.ActionResources and entity.ActionResources.Resources
    if not resources then return end
    local bonus = false
    for _, entry in pairs(resources[BonusActionPoint] or {}) do
        if entry.Amount >= 1 then bonus = true end
    end
    status(character, "GSL_RELOAD_NO_BONUS_ACTION", not bonus)
    status(character, "GSL_QUICK_FULL_RELOAD", bonus and Osi.HasPassive(character, "GSL_Feat_QuickReload_Marker") == 1)
end

local function applyItem(item, state, hand, rapid)
    status(item, "GSL_FIREARM_ITEM_MISFIRED", state.misfire and not state.broken)
    status(item, "GSL_FIREARM_ITEM_DESTROYED", state.broken)
    for slot in pairs(slots) do
        local repairable = slot == hand and state.misfire and not state.broken
        status(item, "GSL_REPAIR_MENU_" .. slot:upper(), repairable and not rapid)
        status(item, "GSL_REPAIR_MENU_" .. slot:upper() .. "_RAPID", repairable and rapid)
    end
    local capacityCount = Rules.ModCount(state, "Capacity")
    status(item, "GSL_TINKERER_CAPACITY", capacityCount == 1)
    status(item, "GSL_TINKERER_MASTER_AMMO", capacityCount >= 2)
    for kind in pairs(Rules.Firearms) do
        local current = state.kind == kind
        local damageCount = current and Rules.ModCount(state, "Damage") or 0
        local rangeCount = current and Rules.ModCount(state, "Range") or 0
        status(item, "GSL_TINKERER_DAMAGE_" .. kind:upper(), damageCount == 1)
        status(item, "GSL_TINKERER_MASTER_DAMAGE_" .. kind:upper(), damageCount >= 2)
        status(item, "GSL_TINKERER_RANGE_" .. kind:upper(), rangeCount == 1)
        status(item, "GSL_TINKERER_MASTER_RANGE_" .. kind:upper(), rangeCount >= 2)
    end
    -- Older versions edited the Weapon component directly; restore it once, since range now comes from statuses.
    if state.baseRange then
        local entity = Ext.Entity.Get(item)
        pcall(function()
            if entity.Weapon.WeaponRange ~= state.baseRange then
                entity.Weapon.WeaponRange = state.baseRange
                entity:Replicate("Weapon")
            end
        end)
        state.baseRange = nil
    end
end

local function snapshot(character)
    local data = database()
    local owner = data.owners[character]
    if not owner then return end
    for hand in pairs(slots) do
        local item = equipped(character, hand)
        if item and owner[hand] == item then
            local state = data.weapons[item]
            local entry = resource(character, hand, state)
            state.ammo = math.min(entry.Amount, Rules.Capacity(state))
        end
    end
    save(data)
end

local function refreshNow(character, restoreAmmo)
    local data = database()
    local owner = data.owners[character] or {}
    data.owners[character] = owner
    status(character, "GSL_MISFIRE", false)
    status(character, "GSL_DOUBLE_LOAD_BROKEN", false)
    for hand in pairs(slots) do
        local item, kind = equipped(character, hand)
        local changed = owner[hand] ~= item
        local newItem = item and not data.weapons[item]
        local previousBoost = owner[hand .. "Boost"]
        local state = item and itemState(data, item, kind)
        local capacityCount = state and Rules.ModCount(state, "Capacity") or 0
        local boostAmount = state and Rules.Firearms[kind].capacity * capacityCount or 0
        local boost = boostAmount > 0 and
            "ActionResource(" .. (hand == "Off" and "GunslingerOffhandFlintlockAmmo" or
                "Gunslinger" .. kind .. "Ammo") .. "," .. boostAmount .. ",0)" or nil
        local source = "GSL_Tinkerer_" .. hand
        if previousBoost ~= boost then
            if previousBoost then Osi.RemoveBoosts(character, previousBoost, 0, source, character) end
            if boost then Osi.AddBoosts(character, boost, source, character) end
            owner[hand .. "Boost"] = boost
        end
        owner[hand] = item
        status(character, "GSL_FIREARM_" .. hand:upper() .. "_DISABLED", state and state.broken)
        status(character, "GSL_FIREARM_" .. hand:upper() .. "_MISFIRED", false)
        status(character, "GSL_FIREARM_" .. hand:upper() .. "_DESTROYED", false)
        if hand == "Off" then
            local rangeCount = state and Rules.ModCount(state, "Range") or 0
            status(character, "GSL_TINKERER_OFF_RANGE", rangeCount == 1)
            status(character, "GSL_TINKERER_OFF_RANGE_MASTER", rangeCount >= 2)
        else
            -- Longarm Specialist's range is a spell-variant boost, so it is applied only while a musket is held.
            status(character, "GSL_LONGARM_SPECIALIST_RANGE", state and state.kind == "Musket" and
                Osi.HasPassive(character, "GSL_Feat_LongarmSpecialist_Range") == 1)
            for gun in pairs(Rules.Firearms) do
                local rangeCount = state and state.kind == gun and Rules.ModCount(state, "Range") or 0
                status(character, "GSL_TINKERER_MAIN_RANGE_" .. gun:upper(),
                    rangeCount == 1)
                status(character, "GSL_TINKERER_MAIN_RANGE_MASTER_" .. gun:upper(),
                    rangeCount >= 2)
            end
        end
        -- Retire character-owned repair unlocks from existing saves.
        status(character, "GSL_REPAIR_MENU_" .. hand:upper(), false)
        status(character, "GSL_REPAIR_MENU_" .. hand:upper() .. "_RAPID", false)
        if state then
            applyItem(item, state, hand, Osi.HasPassive(character, "GSL_RapidRepairUnlock") == 1)
            local entry, entity = resource(character, hand, state)
            if newItem then state.ammo = entry.Amount end
            if changed or restoreAmmo then
                entry.Amount = math.min(state.ammo, entry.MaxAmount)
                entity:Replicate("ActionResources")
            else
                state.ammo = math.min(entry.Amount, Rules.Capacity(state))
            end
        end
    end
    save(data)
    updateReloadCosts(character)
    cleanupRemovedAbilities(character)
end

local function refresh(character, restoreAmmo)
    if refreshing[character] then return end
    refreshing[character] = true
    -- Release the re-entrancy guard even on error, or every later refresh for this character is silently skipped.
    local ok, err = pcall(refreshNow, character, restoreAmmo)
    refreshing[character] = nil
    if not ok then error(err, 0) end
end

local function misfireItem(character, item, broken)
    local data = database()
    local kind = item and templates[(Osi.GetTemplate(item) or ""):sub(-36):lower()]
    assert(kind, "Misfire could not be correlated to a physical firearm")
    Rules.Misfire(itemState(data, item, kind), broken)
    save(data)
    refresh(character, false)
end

local ammoSpells = {Zone_GSL_LineEmUp = true, Zone_GSL_PiercingRound = true, Shout_GSL_HailOfLead = true}
local rollTheBones = {"GSL_RTB_BUST", "GSL_RTB_HIT", "GSL_RTB_JACKPOT"}

Ext.Events.StatsLoaded:Subscribe(function()
    -- Every magical firearm has its own root template; map them all from their weapon stats.
    for _, name in ipairs(Ext.Stats.GetStats("Weapon")) do
        local kind = name:match("^WPN_GSL_(%a+)")
        local root = kind and Rules.Firearms[kind] and Ext.Stats.Get(name).RootTemplate
        if root and root ~= "" then templates[root:lower()] = kind end
    end
    for _, name in ipairs(Ext.Stats.GetStats("SpellData")) do
        local spell = Ext.Stats.Get(name)
        if name:match("^GSL_.*_attack") or name:match("^Projectile_GSL_") or ammoSpells[name] then
            local hand = name:find("OffHand", 1, true) and "OFF" or "MAIN"
            local condition = "not HasStatus('GSL_FIREARM_" .. hand .. "_DISABLED',context.Source)"
            if not spell.RequirementConditions:find("GSL_FIREARM_" .. hand .. "_DISABLED", 1, true) then
                if spell.RequirementConditions ~= "" then condition = "(" .. spell.RequirementConditions .. ") and " .. condition end
                spell.RequirementConditions = condition
            end
            if ammoSpells[name] then
                local ready = {}
                local costs = {}
                for kind in pairs(Rules.Firearms) do
                    local passive = "HasPassive('GSL_" .. kind .. "_MainHand',context.Source)"
                    ready[#ready + 1] = "(" .. passive .. " and HasActionResource('Gunslinger" .. kind .. "Ammo',1,0))"
                    costs[#costs + 1] = "IF(" .. passive .. "):UseActionResource(SELF,Gunslinger" .. kind .. "Ammo,1,0)"
                end
                if not spell.SpellProperties:find("UseActionResource(SELF,Gunslinger", 1, true) then
                    spell.RequirementConditions = "(" .. spell.RequirementConditions .. ") and (" .. table.concat(ready, " or ") .. ")"
                    spell.SpellProperties = (spell.SpellProperties ~= "" and spell.SpellProperties .. ";" or "") .. table.concat(costs, ";")
                end
            end
            Ext.Stats.Sync(name)
        end
        if not name:find("GSL_", 1, true) and
            (spell.SpellRoll:find("AttackType.RangedWeaponAttack", 1, true) or
                spell.SpellRoll:find("AttackType.RangedOffHandWeaponAttack", 1, true)) and
            not spell.SpellProperties:find("UseActionResource(SELF,Gunslinger", 1, true) then
            local offhand = spell.SpellRoll:find("AttackType.RangedOffHandWeaponAttack", 1, true)
            local ready, equippedGun, costs = {}, {}, {}
            for kind in pairs(Rules.Firearms) do
                if not offhand or kind == "Flintlock" then
                    local passive = "HasPassive('GSL_" .. kind .. (offhand and "_OffHand" or "_MainHand") .. "',context.Source)"
                    local ammo = offhand and "GunslingerOffhandFlintlockAmmo" or "Gunslinger" .. kind .. "Ammo"
                    equippedGun[#equippedGun + 1] = passive
                    ready[#ready + 1] = "(" .. passive .. " and HasActionResource('" .. ammo .. "',1,0))"
                    costs[#costs + 1] = "IF(" .. passive .. "):UseActionResource(SELF," .. ammo .. ",1,0)"
                end
            end
            local condition = "(not (" .. table.concat(equippedGun, " or ") .. ") or (not HasStatus('GSL_FIREARM_" ..
                (offhand and "OFF" or "MAIN") .. "_DISABLED',context.Source) and (" .. table.concat(ready, " or ") .. ")))"
            spell.RequirementConditions = (spell.RequirementConditions ~= "" and "(" .. spell.RequirementConditions .. ") and " or "") .. condition
            spell.SpellProperties = (spell.SpellProperties ~= "" and spell.SpellProperties .. ";" or "") .. table.concat(costs, ";")
            Ext.Stats.Sync(name)
        end
    end
end)

Ext.Osiris.RegisterListener("UsingSpell", 5, "before", function(character, spell, _, _, action)
    -- Grit Recovery triggers once per attack; a new attack re-arms it.
    if Osi.HasActiveStatus(character, "GSL_GRIT_RECOVERY_SPENT") == 1 then
        Osi.RemoveStatus(character, "GSL_GRIT_RECOVERY_SPENT")
    end
    if Osi.HasActiveStatus(character, "GSL_HOT_STREAK_ADVANCED") == 1 then
        Osi.RemoveStatus(character, "GSL_HOT_STREAK_ADVANCED")
    end
    if not spell:find("GSL_", 1, true) then return end
    refresh(character, false)
    local hand, mode = Rules.ParseTinkerer(spell)
    local shotHand = spell:match("^Shout_GSL_%a+Repair_(%a+)") or
        (spell:find("OffHand", 1, true) and "Off" or "Main")
    local item = equipped(character, hand or shotHand)
    casts[character] = {spell = spell, item = item, action = action, mode = mode, hand = hand, itemHand = hand or shotHand}
    -- Applied before the attack roll so Double Load's critical-miss passive is active for this shot.
    if spell == "Projectile_GSL_DoubleLoad" then Osi.ApplyStatus(character, "GSL_DOUBLE_LOAD", -1, 1, character) end
    casts[character].violent = tonumber(spell:match("^Projectile_GSL_ViolentShot_(%d)$"))
    if spell:match("^Projectile_GSL_DoubleOrNothing$") then
        casts[character].doubleOrNothingWin = Rules.DoubleOrNothing(Ext.Math.Random(1, 20))
        casts[character].lose = not casts[character].doubleOrNothingWin
    end
end)

local function clearShotStatuses(character, spell)
    if spell:match("^Projectile_GSL_DoubleLoad$") then Osi.RemoveStatus(character, "GSL_DOUBLE_LOAD") end
end

local function cheatDeathsOdds(character, spell)
    if Osi.HasPassive(character, "GSL_Desperado_CheatDeathsOdds") ~= 1 then return end
    local cost = Rules.GritCost((Ext.Stats.Get(spell) or {}).UseCosts)
    local entity = Ext.Entity.Get(character)
    local health = entity and entity.Health
    if health and health.MaxHp > 0 and Rules.CheatDeathRefund(cost, health.Hp / health.MaxHp) then
        Osi.ApplyStatus(character, "GSL_CHEAT_DEATHS_ODDS_REFUND", 0, 1, character)
    end
end

Ext.Osiris.RegisterListener("CastedSpell", 5, "after", function(character, spell, _, _, action)
    local cast = casts[character]
    if cast and cast.spell == spell and cast.action == action then
        if cast.mode then
            assert(cast.item, "Tinkerer resolved without an equipped firearm")
            local data = database()
            local state = assert(data.weapons[cast.item])
            if cast.mode == "Remove" then
                Rules.RemoveModifications(state)
            else
                local limit = Osi.HasPassive(character, "GSL_MasterTinkerer") == 1 and 2 or 1
                Rules.Modify(state, cast.mode, limit)
            end
            save(data)
            refresh(character, true)
        end
        if spell == "Projectile_GSL_DoubleOrNothing" then
            local target = pendingAttackTargets[character]
            pendingAttackTargets[character] = nil
            if cast.doubleOrNothingWin then
                target = assert(target, "Double or Nothing resolved without its triggering attack target")
                if Osi.IsDead(target) == 0 then
                    Osi.UseSpell(character, "Projectile_GSL_DoubleOrNothingAttack", target)
                end
            end
        end
        clearShotStatuses(character, spell)
        -- Volleys hit several targets, so their bullets are spent once per cast here rather than per target in stats.
        local volley = tonumber(spell:match("^Projectile_GSL_FanningFire_(%d)$"))
        local shots = volley and volley + 1
        local volleyState = shots and cast.item and database().weapons[cast.item]
        if volleyState then
            local entry, entity = resource(character, "Main", volleyState)
            entry.Amount = math.max(0, entry.Amount - shots)
            entity:Replicate("ActionResources")
        end
        if cast.item and (cast.lose or (cast.violent and Rules.ViolentMisfire(cast.violent, Ext.Math.Random(1, 20)))) then
            misfireItem(character, cast.item, false)
        end
        if spell == "Shout_GSL_RollTheBones" then
            for _, name in ipairs(rollTheBones) do Osi.RemoveStatus(character, name) end
            Osi.ApplyStatus(character, "GSL_RTB_" .. Rules.RollTheBones(Ext.Math.Random(1, 6)), 12, 1, character)
        end
        cheatDeathsOdds(character, spell)
        casts[character] = nil
    end
    if database().owners[character] then
        snapshot(character)
        refresh(character, false)
    end
    cleanupRemovedAbilities(character)
end)

Ext.Osiris.RegisterListener("CastSpellFailed", 5, "after", function(character, spell, _, _, action)
    local cast = casts[character]
    if cast and cast.action == action then
        clearShotStatuses(character, spell)
        casts[character] = nil
    end
    if database().owners[character] then
        snapshot(character)
        refresh(character, false)
    end
    cleanupRemovedAbilities(character)
end)

-- Last Word's Downed replacement and the lethal hit's AttackedBy event can arrive in either order.
local function lastWordShot(character, attacker)
    pendingLastWord[character] = nil
    Osi.RemoveStatus(character, "GSL_LASTWORD_PENDING")
    if attacker and attacker ~= character and Osi.IsDead(character) == 0 and Osi.IsDead(attacker) == 0 then
        Osi.UseSpell(character, "Projectile_GSL_ReactionShot", attacker)
    end
end

Ext.Osiris.RegisterListener("StatusApplied", 4, "after", function(character, applied, _, action)
    if applied == hotStreakStatus then
        clearHotStreak(character)
    elseif applied == "GSL_LASTWORD_PENDING" then
        if recentAttackers[character] then
            lastWordShot(character, recentAttackers[character])
        else
            pendingLastWord[character] = true
        end
    elseif applied == "GSL_MISFIRE" or applied == "GSL_DOUBLE_LOAD_BROKEN" then
        local cast = casts[character]
        local item = cast and cast.item or equipped(character, "Main") or equipped(character, "Off")
        Osi.RemoveStatus(character, applied)
        -- Any critical miss during Double Load breaks the gun, even if only the ordinary misfire passive fired.
        misfireItem(character, item, applied == "GSL_DOUBLE_LOAD_BROKEN" or
            (cast ~= nil and cast.spell == "Projectile_GSL_DoubleLoad"))
    elseif applied == "GSL_REPAIR_MAIN_DONE" or applied == "GSL_REPAIR_OFF_DONE" or
        applied == "GSL_FIELD_REPAIR_MAIN_DONE" or applied == "GSL_FIELD_REPAIR_OFF_DONE" then
        local cast = casts[character]
        assert(cast and cast.action == action and cast.item, "Repair lost its physical firearm/action correlation")
        local hand = applied:find("_OFF_", 1, true) and "Off" or "Main"
        assert(cast.itemHand == hand, "Repair success does not match the selected firearm hand")
        local data = database()
        assert(Rules.Repair(data.weapons[cast.item]), "Repair cannot restore a destroyed firearm")
        save(data)
        Osi.RemoveStatus(character, applied)
        refresh(character, false)
    end
end)

Ext.Osiris.RegisterListener("StatusRemoved", 4, "after", function(character, removed)
    if removed == hotStreakStatus then clearHotStreak(character) end
end)

Ext.Osiris.RegisterListener("AttackedBy", 7, "after", function(defender, _, attacker)
    recentAttackers[defender] = attacker
    if attacker and attacker ~= defender then pendingAttackTargets[attacker] = defender end
    if pendingLastWord[defender] and Osi.HasActiveStatus(defender, "GSL_LASTWORD_PENDING") == 1 then
        lastWordShot(defender, attacker)
    end
end)

Ext.Osiris.RegisterListener("Equipped", 2, "after", function(_, character)
    if database().owners[character] or equipped(character, "Main") or equipped(character, "Off") then
        pendingRefresh[character] = 2
    end
end)
Ext.Osiris.RegisterListener("Unequipped", 2, "before", function(item, character)
    snapshot(character)
    local state = database().weapons[item]
    if state then applyItem(item, state) end
end)
Ext.Osiris.RegisterListener("Unequipped", 2, "after", function(_, character)
    if database().owners[character] then pendingRefresh[character] = 2 end
end)
-- Osiris databases are nil until the story is bound (main menu, or after a failed story compile/merge).
local function playerDatabase()
    local ok, db = pcall(function() return Osi.DB_Players end)
    return ok and db or nil
end
local function refreshLoadedSession()
    for character in pairs(database().fortunePreviews or {}) do finishFortunePreview(character) end
    for character in pairs(database().fortuneUpgrades or {}) do
        if Ext.Entity.Get(character) then upgradeDesperadosLuck(character) end
    end
    for _, player in pairs(playerDatabase():Get(nil)) do
        local character = player[1]
        if Ext.Entity.Get(character) then refreshClassFeatures(character) end
    end
    for character in pairs(database().owners) do
        if Ext.Entity.Get(character) then
            upgradeDesperadosLuck(character)
            refresh(character, true)
        end
    end
end

Ext.Events.Tick:Subscribe(function()
    local players = playerDatabase()
    if not players then return end
    if pendingSessionRefresh then
        pendingSessionRefresh = false
        refreshLoadedSession()
    end
    updateFortunePreviews()
    for _, player in pairs(players:Get(nil)) do
        local character = player[1]
        if Ext.Entity.Get(character) then cleanupRemovedAbilities(character) end
    end
    recentAttackers = {}
    for character, ticks in pairs(pendingLuckCleanup) do
        if ticks > 0 then
            pendingLuckCleanup[character] = ticks - 1
        else
            pendingLuckCleanup[character] = nil
            if not respecInProgress[character] and Osi.HasPassive(character, fortunePassive) == 1 and
                Osi.HasPassive(character, luckPassive) == 1 then
                reportPersistentLuck(character)
            end
        end
    end
    for character, ticks in pairs(pendingRefresh) do
        if ticks > 0 then
            pendingRefresh[character] = ticks - 1
        else
            pendingRefresh[character] = nil
            refresh(character, false)
        end
    end
    reloadPollTicks = reloadPollTicks + 1
    if reloadPollTicks >= 5 then
        reloadPollTicks = 0
        for character in pairs(database().owners) do updateReloadCosts(character) end
        -- Progression passives can arrive after LeveledUp; retry independently of equipped firearms.
        for _, player in pairs(players:Get(nil)) do
            local character = player[1]
            if Ext.Entity.Get(character) then upgradeDesperadosLuck(character) end
        end
    end
end)
-- Arcane Reload's concentration status sits on the firearm itself, so the bullet follows the enchanted gun.
local function arcaneReload(character)
    local data = database()
    for hand in pairs(slots) do
        local item = equipped(character, hand)
        local state = item and data.weapons[item]
        if state and not state.broken and Osi.HasActiveStatus(item, "GSL_ARCANE_RELOAD") == 1 then
            local entry, entity = resource(character, hand, state)
            if entry.Amount < entry.MaxAmount then
                entry.Amount = entry.Amount + 1
                entity:Replicate("ActionResources")
                state.ammo = math.min(entry.Amount, Rules.Capacity(state))
            end
        end
    end
    save(data)
end

Ext.Osiris.RegisterListener("TurnStarted", 1, "after", function(character)
    upgradeDesperadosLuck(character)
    status(character, "GSL_GRIT_RECOVERY_SPENT", false)
    if database().owners[character] then
        refresh(character, false)
        arcaneReload(character)
    end
end)
Ext.Osiris.RegisterListener("LongRestFinished", 0, "after", function()
    local data = database()
    for item, state in pairs(data.weapons) do
        Rules.LongRest(state)
        if Ext.Entity.Get(item) then applyItem(item, state) end
    end
    save(data)
    for character in pairs(data.owners) do
        if Ext.Entity.Get(character) then refresh(character, true) end
    end
end)
Ext.Events.SessionLoaded:Subscribe(function()
    casts = {}
    pendingRefresh = {}
    pendingLastWord = {}
    recentAttackers = {}
    pendingAttackTargets = {}
    pendingLuckCleanup = {}
    reportedLuckCleanup = {}
    fortunePreviewLeases = {}
    pendingFortunePreviewMessages = {}
    previewTick = 0
    -- SessionLoaded restricts Osiris calls; gameplay initialization must wait for Tick.
    pendingSessionRefresh = true
end)
