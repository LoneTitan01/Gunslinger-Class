local Rules = Ext.Require("GritRules.lua")
local templates = {
    ["3d8b177d-89db-4826-8068-9f2d777faf04"] = "Flintlock",
    ["4a7854fd-718a-4a4e-b9db-3875b5788065"] = "Blunderbuss",
    ["1da91e88-3f0e-4ccc-ac25-0bdf00426880"] = "Musket"
}
local slots = {Main = "Ranged Main Weapon", Off = "Ranged Offhand Weapon"}
local casts = {}
local refreshing = {}
local pendingRefresh = {}
local pendingLastWord = {}

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
        local entity = assert(Ext.Entity.Get(item), "Equipped firearm has no entity")
        data.weapons[item] = {
            kind = kind, ammo = Rules.Firearms[kind].capacity,
            baseRange = assert(entity.Weapon, "Firearm has no Weapon component").WeaponRange
        }
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

local function applyItem(item, state)
    for kind in pairs(Rules.Firearms) do
        status(item, "GSL_TINKERER_DAMAGE_" .. kind:upper(), state.mode == "Damage" and state.kind == kind)
    end
    local entity = assert(Ext.Entity.Get(item), "Tracked firearm has no entity")
    local weapon = assert(entity.Weapon, "Tracked firearm has no Weapon component")
    local range = state.baseRange + (state.mode == "Range" and Rules.Firearms[state.kind].rangeBonus or 0)
    if weapon.WeaponRange ~= range then
        weapon.WeaponRange = range
        entity:Replicate("Weapon")
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

local function refresh(character, restoreAmmo)
    if refreshing[character] then return end
    refreshing[character] = true
    local data = database()
    local owner = data.owners[character] or {}
    data.owners[character] = owner
    for hand in pairs(slots) do
        local item, kind = equipped(character, hand)
        local changed = owner[hand] ~= item
        local newItem = item and not data.weapons[item]
        local previousBoost = owner[hand .. "Boost"]
        local state = item and itemState(data, item, kind)
        local boost = state and state.mode == "Capacity" and
            "ActionResource(" .. (hand == "Off" and "GunslingerOffhandFlintlockAmmo" or
                "Gunslinger" .. kind .. "Ammo") .. ",2,0)" or nil
        local source = "GSL_Tinkerer_" .. hand
        if previousBoost ~= boost then
            if previousBoost then Osi.RemoveBoosts(character, previousBoost, 0, source, character) end
            if boost then Osi.AddBoosts(character, boost, source, character) end
            owner[hand .. "Boost"] = boost
        end
        owner[hand] = item
        status(character, "GSL_FIREARM_" .. hand:upper() .. "_DISABLED", state and (state.broken or state.misfire))
        status(character, "GSL_FIREARM_" .. hand:upper() .. "_DESTROYED", state and state.broken)
        if hand == "Off" then
            status(character, "GSL_TINKERER_OFF_RANGE", state and state.mode == "Range")
        end
        for dc = 12, 16 do
            local repairable = state and state.misfire and not state.broken
            local rarity = repairable and assert(Ext.Entity.Get(item).Value, "Firearm has no rarity").Rarity
            status(character, "GSL_REPAIR_" .. hand:upper() .. "_" .. dc,
                repairable and Rules.RepairDC(rarity) == dc)
        end
        if state then
            applyItem(item, state)
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
    refreshing[character] = nil
end

Ext.Events.StatsLoaded:Subscribe(function()
    for _, name in ipairs(Ext.Stats.GetStats("SpellData")) do
        local spell = Ext.Stats.Get(name)
        if name:match("^GSL_.*_attack") or name:match("^Projectile_GSL_") or name == "Zone_GSL_LineEmUp" then
            local hand = name:find("OffHand", 1, true) and "OFF" or "MAIN"
            local condition = "not HasStatus('GSL_FIREARM_" .. hand .. "_DISABLED',context.Source)"
            if not spell.RequirementConditions:find("GSL_FIREARM_" .. hand .. "_DISABLED", 1, true) then
                if spell.RequirementConditions ~= "" then condition = "(" .. spell.RequirementConditions .. ") and " .. condition end
                spell.RequirementConditions = condition
            end
            if name == "Zone_GSL_LineEmUp" or name:match("^Projectile_GSL_InfusedRounds") then
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
    if not spell:find("GSL_", 1, true) then return end
    refresh(character, false)
    local hand, mode = Rules.ParseTinkerer(spell)
    local shotHand = spell:match("^Shout_GSL_RapidRepair_(%a+)%d+$") or
        (spell:find("OffHand", 1, true) and "Off" or "Main")
    local item = equipped(character, hand or shotHand)
    casts[character] = {spell = spell, item = item, action = action, mode = mode, hand = hand}
    local grit = spell:match("^Projectile_GSL_FanningFire_%a+_(%d)$")
    if grit then Osi.ApplyStatus(character, "GSL_FANNING_FIRE_" .. grit, -1, 1, character) end
end)

Ext.Osiris.RegisterListener("CastedSpell", 5, "after", function(character, spell, _, _, action)
    local cast = casts[character]
    if cast and cast.spell == spell and cast.action == action then
        if cast.mode then
            assert(cast.item, "Tinkerer resolved without an equipped firearm")
            local data = database()
            Rules.Modify(assert(data.weapons[cast.item]), cast.mode)
            save(data)
            refresh(character, true)
        end
        if spell:match("^Projectile_GSL_FanningFire_") then
            for grit = 1, 3 do Osi.RemoveStatus(character, "GSL_FANNING_FIRE_" .. grit) end
        end
        if spell:match("^Projectile_GSL_DoubleLoad_") then Osi.RemoveStatus(character, "GSL_DOUBLE_LOAD") end
        casts[character] = nil
    end
    if database().owners[character] then
        snapshot(character)
        refresh(character, false)
    end
end)

Ext.Osiris.RegisterListener("CastSpellFailed", 5, "after", function(character, spell, _, _, action)
    local cast = casts[character]
    if cast and cast.action == action then
        if spell:match("^Projectile_GSL_FanningFire_") then
            for grit = 1, 3 do Osi.RemoveStatus(character, "GSL_FANNING_FIRE_" .. grit) end
        end
        if spell:match("^Projectile_GSL_DoubleLoad_") then Osi.RemoveStatus(character, "GSL_DOUBLE_LOAD") end
        casts[character] = nil
    end
    if database().owners[character] then
        snapshot(character)
        refresh(character, false)
    end
end)

Ext.Osiris.RegisterListener("StatusApplied", 4, "after", function(character, applied, _, action)
    if applied == "GSL_LASTWORD_PENDING" then
        pendingLastWord[character] = action
    elseif applied == "GSL_MISFIRE" or applied == "GSL_DOUBLE_LOAD_BROKEN" then
        local cast = casts[character]
        local item = cast and cast.item or Osi.GetEquippedWeapon(character)
        local data = database()
        local kind = item and templates[(Osi.GetTemplate(item) or ""):sub(-36):lower()]
        assert(kind, "Misfire could not be correlated to a physical firearm")
        local state = itemState(data, item, kind)
        Rules.Misfire(state, applied == "GSL_DOUBLE_LOAD_BROKEN")
        save(data)
        Osi.RemoveStatus(character, applied)
        refresh(character, false)
    elseif applied == "GSL_REPAIR_MAIN_DONE" or applied == "GSL_REPAIR_OFF_DONE" then
        local cast = casts[character]
        assert(cast and cast.action == action and cast.item, "Repair lost its physical firearm/action correlation")
        local data = database()
        assert(Rules.Repair(data.weapons[cast.item]), "Rapid Repair cannot restore a destroyed firearm")
        save(data)
        Osi.RemoveStatus(character, applied)
        refresh(character, false)
    end
end)

Ext.Osiris.RegisterListener("AttackedBy", 7, "after", function(defender, _, attacker, _, _, _, action)
    if pendingLastWord[defender] == action and Osi.HasActiveStatus(defender, "GSL_LASTWORD_PENDING") == 1 then
        pendingLastWord[defender] = nil
        Osi.RemoveStatus(defender, "GSL_LASTWORD_PENDING")
        if attacker and Osi.IsDead(defender) == 0 and Osi.IsDead(attacker) == 0 then
            Osi.UseSpell(defender, "Projectile_GSL_ReactionShot", attacker)
        end
    end
end)

Ext.Osiris.RegisterListener("Equipped", 2, "after", function(_, character)
    if database().owners[character] or equipped(character, "Main") or equipped(character, "Off") then
        pendingRefresh[character] = 2
    end
end)
Ext.Osiris.RegisterListener("Unequipped", 2, "before", function(_, character)
    snapshot(character)
end)
Ext.Osiris.RegisterListener("Unequipped", 2, "after", function(_, character)
    if database().owners[character] then pendingRefresh[character] = 2 end
end)
Ext.Events.Tick:Subscribe(function()
    for character, ticks in pairs(pendingRefresh) do
        if ticks > 0 then
            pendingRefresh[character] = ticks - 1
        else
            pendingRefresh[character] = nil
            refresh(character, false)
        end
    end
end)
Ext.Osiris.RegisterListener("TurnStarted", 1, "after", function(character)
    if database().owners[character] then refresh(character, false) end
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
    for character in pairs(database().owners) do
        if Ext.Entity.Get(character) then refresh(character, true) end
    end
    Ext.Utils.Print("[Gunslinger] Persistent firearm/grit runtime loaded")
end)
