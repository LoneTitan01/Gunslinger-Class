-- Firearm requirements added to spell stats when they load. Loaded by both the server and the client: each has
-- its own copy of the stats, and the hotbar greys actions out from the client's copy, so both must be edited.
local Rules = Ext.Require("GritRules.lua")
local Stats = {}

Stats.AmmoSpells = {Zone_GSL_LineEmUp = true, Zone_GSL_PiercingRound = true, Shout_GSL_HailOfLead = true}
local ammoSpells = Stats.AmmoSpells

-- The caster's own checks use GunslingerFirearmWorking (Scripts/thoth/helpers/GunslingerConditions.khn), which
-- fails with the reason "Firearm Broken". Interrupts check the observing gunslinger, which that script cannot
-- name, so they keep the raw status check.
local function workingFirearmCondition(hand, character)
    if character == "context.Source" then
        return "GunslingerFirearmWorking(" .. (hand == "Off" and "true" or "false") .. ")"
    end
    local slot = hand == "Off" and "RangedOffHand" or "RangedMainHand"
    return "not HasStatus('GSL_FIREARM_ITEM_DESTROYED',GetItemInEquipmentSlot(EquipmentSlot." ..
        slot .. "," .. character .. "))"
end

function Stats.RequireWorkingFirearm(stat, field, hand, character)
    local condition = workingFirearmCondition(hand, character)
    local previous = stat[field] or ""
    if not previous:find(condition, 1, true) then
        stat[field] = (previous ~= "" and "(" .. previous .. ") and " or "") .. condition
    end
end
local requireWorkingFirearm = Stats.RequireWorkingFirearm

-- The Script Extender returns SpellRoll as a table of groups ({Default = "...", CastOffhand = "..."}) and
-- SpellProperties/SpellSuccess as parsed functors, never as their stats text. Writing a string still works.
local function rollText(roll)
    if type(roll) == "string" then return roll end
    local parts = {}
    for _, text in pairs(roll or {}) do parts[#parts + 1] = text end
    return table.concat(parts, ";")
end

function Stats.Field(object, key)
    local ok, value = pcall(function() return object[key] end)
    return ok and value or nil
end
local field = Stats.Field

-- Returns whether any DealDamage in the functors uses the given weapon's damage (e.g. "MainRangedWeapon").
function Stats.DealsWeaponDamage(functors, weapon)
    if type(functors) == "string" then return functors:find(weapon, 1, true) ~= nil end
    local ok, found = pcall(function()
        for _, group in pairs(functors or {}) do
            for _, functor in pairs(field(group, "Functors") or {group}) do
                if field(functor, "TypeId") == "DealDamage" and (field(functor, "WeaponType") == weapon or
                    field(functor, "WeaponDamageType") == weapon .. "DamageType") then
                    return true
                end
            end
        end
        return false
    end)
    return ok and found
end
local dealsWeaponDamage = Stats.DealsWeaponDamage

-- Returns whether a non-thrown spell fires the main-hand and/or off-hand ranged weapon. Besides the
-- attack roll, this catches saving-throw shots that deal ranged weapon damage (Hail of Thorns, Conjure Barrage).
local function rangedShotHands(spell)
    if spell.SpellType == "Throw" then return false, false end
    local roll = rollText(spell.SpellRoll)
    local main = roll:find("AttackType.RangedWeaponAttack", 1, true) ~= nil
    local off = roll:find("AttackType.RangedOffHandWeaponAttack", 1, true) ~= nil
    if not main and (roll == "" or roll:find("SavingThrow", 1, true)) then
        main = dealsWeaponDamage(spell.SpellSuccess, "MainRangedWeapon") or
            dealsWeaponDamage(spell.SpellProperties, "MainRangedWeapon")
    end
    return main, off
end

-- Returns the requirement condition for a shot from the given hand: a held gun must work and be loaded.
-- GunslingerFirearmReady (Scripts/thoth/helpers/GunslingerConditions.khn) passes when no gun is held in that
-- hand, and otherwise fails with its own reason, "Firearm Broken" or "No Ammo" (ErrorDescriptions).
local function firearmShotCondition(hand)
    return "GunslingerFirearmReady(" .. (hand == "Off" and "true" or "false") .. ")"
end

local function addRequirement(spell, condition)
    local previous = spell.RequirementConditions or ""
    if previous:find(condition, 1, true) then return end
    spell.RequirementConditions = (previous ~= "" and "(" .. previous .. ") and " or "") .. condition
end

-- Returns the hand whose gun a spell fires and whether the shot spends a bullet, or nil if it fires no gun.
function Stats.ShotKind(name, spell)
    if ammoSpells[name] then return "Main", true end
    if name:find("GSL_", 1, true) then return nil end
    local mainShot, offShot = rangedShotHands(spell)
    if not (mainShot or offShot) then return nil end
    -- Spells rolling both hands (e.g. Projectile_MainHandAttack) are main-hand shots; their CastOffhand[...]
    -- section is the bundled dual-wield shot, which firearms disable. Special arrows (Projectile_ArrowOf*,
    -- Barbed Arrow, Arrow of Many Targets' ricochets) are the ammunition fired, so they spend no bullet.
    return mainShot and "Main" or "Off", not name:find("Arrow", 1, true)
end
local shotKind = Stats.ShotKind

local function weaponTypeList(spell)
    local types, list = field(spell, "WeaponTypes"), {}
    if type(types) == "string" then
        for name in types:gmatch("[^;%s]+") do list[#list + 1] = name end
    else
        for _, name in pairs(types or {}) do list[#list + 1] = name end
    end
    return list
end

-- Returns whether a spell needs a held Ammunition weapon (WeaponTypes "Ammunition"), which a gun always is.
local function needsAmmunitionWeapon(spell)
    for _, weaponType in ipairs(weaponTypeList(spell)) do
        if weaponType == "Ammunition" then return true end
    end
    return false
end

-- Adds the firearm requirements to one spell. Returns whether it changed.
local function applySpell(name, spell)
    if name:match("^GSL_.*_attack") or name:match("^Projectile_GSL_") or
        name:match("^Zone_GSL_Scattershot") or ammoSpells[name] then
        -- Match both spellings, "OffHand" and "Offhand".
        local hand = name:lower():find("offhand", 1, true) and "Off" or "Main"
        requireWorkingFirearm(spell, "RequirementConditions", hand, "context.Source")
        if ammoSpells[name] then
            local ready = {}
            for kind in pairs(Rules.Firearms) do
                local passive = "HasPassive('GSL_" .. kind .. "_MainHand',context.Source)"
                ready[#ready + 1] = "(" .. passive .. " and HasActionResource('Gunslinger" .. kind .. "Ammo',1,0))"
            end
            addRequirement(spell, "(" .. table.concat(ready, " or ") .. ")")
        end
        return true
    end
    if name:find("GSL_", 1, true) then return false end
    local hand = shotKind(name, spell)
    local arrow = name:find("Arrow", 1, true) ~= nil
    if arrow and (hand or needsAmmunitionWeapon(spell)) then
        -- Special arrows are the ammunition fired, so they only need a working gun, not a bullet.
        requireWorkingFirearm(spell, "RequirementConditions", hand or "Main", "context.Source")
        return true
    elseif hand or needsAmmunitionWeapon(spell) then
        -- An empty gun keeps its Ammunition property, so every other action needing an Ammunition weapon
        -- (even one the shot detection does not recognise) needs a loaded gun while a gun is held.
        addRequirement(spell, firearmShotCondition(hand or "Main"))
        return true
    end
    return false
end

-- Edits the loaded stats. The server syncs each change to clients; a client only edits its own copy.
-- Each entry is edited on its own, so one that fails cannot leave the rest without their requirements.
function Stats.Apply(context)
    local sync = context == "server"
    local changed, failed, firstError = 0, 0, nil
    local function edit(name, apply)
        local ok, result = pcall(apply)
        if not ok then
            failed = failed + 1
            firstError = firstError or (name .. ": " .. tostring(result))
        elseif result then
            changed = changed + 1
            if sync then Ext.Stats.Sync(name) end
        end
    end
    for _, name in ipairs(Ext.Stats.GetStats("Weapon")) do
        local kind = name:match("^WPN_GSL_(%a+)")
        if kind and Rules.Firearms[kind] then
            edit(name, function()
                local weapon = Ext.Stats.Get(name)
                -- Fused guns can override their base gun's equipment boosts.
                for _, hand in ipairs(kind == "Flintlock" and {"Main", "Off"} or {"Main"}) do
                    local key = "BoostsOnEquip" .. hand .. "Hand"
                    local unlock = "UnlockSpell(Shout_GSL_Repair_" .. hand .. ")"
                    local boosts = weapon[key] or ""
                    if not boosts:find(unlock, 1, true) then
                        weapon[key] = (boosts ~= "" and boosts .. ";" or "") .. unlock
                    end
                end
                return true
            end)
        end
    end
    for _, name in ipairs(Ext.Stats.GetStats("SpellData")) do
        edit(name, function() return applySpell(name, Ext.Stats.Get(name)) end)
    end
    for _, name in ipairs({"Interrupt_GSL_HairTrigger", "Interrupt_GSL_CloseCall",
        "Interrupt_GSL_QuickOnTheDraw", "Interrupt_GSL_DoubleOrNothing", "Interrupt_GSL_ReturnFire"}) do
        edit(name, function()
            local interrupt = assert(Ext.Stats.Get(name), "Missing firearm interrupt")
            requireWorkingFirearm(interrupt, "Conditions", "Main", "context.Observer")
            return true
        end)
    end
    Ext.Utils.Print("[Gunslinger] Firearm requirements added to " .. changed .. " stats (" .. context .. ").")
    if failed > 0 then
        Ext.Utils.Print("[Gunslinger] WARNING: " .. failed .. " stats could not be edited (" .. context ..
            "); first: " .. firstError)
    end
    return changed, failed
end

return Stats
