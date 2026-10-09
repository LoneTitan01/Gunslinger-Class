local root = "GunslingerClass\\Mods\\GunslingerClass\\ScriptExtender\\Lua\\"
local rules = dofile(root .. "GritRules.lua")
local listeners, events, entities, inventory, statuses = {}, {}, {}, {}, {}
local variables, passives, rolls, durations = {}, {}, {}, {}
local hotStreakStacks = {}
local doubleOrNothingAttacks = 0
local players = {{"charlie"}}
local interrupts = {}
local printed = {}
local protectedPassives = {}
local netListeners = {}
local allInBoosts = {}
local allInChanges = 0
local passiveInterrupts = {
    GSL_Desperado_DesperadosLuckUnlock = "Interrupt_GSL_DesperadosLuck",
    GSL_Desperado_DesperadosFortuneUnlock = "Interrupt_GSL_DesperadosFortune"
}
local osirisRestricted = false
local spellStats = {
    GSL_MainHand_Flintlock_attack = {RequirementConditions = "Character()", SpellProperties = "", SpellRoll = ""},
    GSL_OffHand_Flintlock_attack = {RequirementConditions = "", SpellProperties = "", SpellRoll = ""},
    Projectile_GSL_Bloodletting_Flintlock = {RequirementConditions = "", SpellProperties = "",
        SpellRoll = "Attack(AttackType.RangedWeaponAttack)",
        UseCosts = "ActionPoint:1;GunslingerFlintlockAmmo:1"},
    Zone_GSL_LineEmUp = {RequirementConditions = "Character()", SpellProperties = "OriginalEffect", SpellRoll = ""},
    Zone_GSL_PiercingRound = {RequirementConditions = "Character()", SpellProperties = "", SpellRoll = ""},
    Shout_GSL_HailOfLead = {RequirementConditions = "Character()", SpellProperties = "", SpellRoll = ""},
    Projectile_GSL_DoubleOrNothing = {RequirementConditions = "", SpellProperties = "", SpellRoll = "", UseCosts = ""},
    Projectile_GSL_DoubleOrNothingAttack = {RequirementConditions = "", SpellProperties = "", SpellRoll = "",
        UseCosts = ""},
    Projectile_GSL_DazingShot = {RequirementConditions = "", SpellProperties = "", SpellRoll = "",
        UseCosts = "ActionPoint:1;GunslingerGrit:2"},
    Projectile_PiercingShot = {RequirementConditions = "OriginalRequirement", SpellProperties = "OriginalPiercingEffect",
        SpellRoll = "Attack(AttackType.RangedWeaponAttack)"},
    Projectile_OffhandAttack = {RequirementConditions = "", SpellProperties = "",
        SpellRoll = "Attack(AttackType.RangedOffHandWeaponAttack)"},
    Zone_GSL_Scattershot = {RequirementConditions = "", SpellProperties = "", SpellRoll = ""},
    Zone_GSL_Scattershot_PoisonMist = {RequirementConditions = "", SpellProperties = "", SpellRoll = ""},
    Projectile_GSL_TwoGunTango_OffHand = {RequirementConditions = "", SpellProperties = "", SpellRoll = ""},
    Projectile_GSL_ReactionShot = {RequirementConditions = "", SpellProperties = "", SpellRoll = ""}
}
local interruptStats = {}
local weaponStats = {
    WPN_GSL_Flintlock = {RootTemplate = "3d8b177d-89db-4826-8068-9f2d777faf04",
        BoostsOnEquipMainHand = "UnlockSpell(Shout_GSL_Reload_Flintlock);UnlockSpell(Shout_GSL_Repair_Main)",
        BoostsOnEquipOffHand = "UnlockSpell(Shout_GSL_Reload_OffhandFlintlock)"},
    WPN_GSL_Flintlock_ArtificialLeech = {RootTemplate = "a710ad68-179b-4b0e-8ef2-3b37609a3f12",
        BoostsOnEquipMainHand = "UnlockSpell(Projectile_GSL_Bloodletting_Flintlock)",
        BoostsOnEquipOffHand = "AC(1)"},
    WPN_GSL_Musket = {RootTemplate = "1da91e88-3f0e-4ccc-ac25-0bdf00426880",
        BoostsOnEquipMainHand = "UnlockSpell(Shout_GSL_Reload_Musket)"},
    WPN_GSL_Blunderbuss = {RootTemplate = "4a7854fd-718a-4a4e-b9db-3875b5788065",
        BoostsOnEquipMainHand = "UnlockSpell(Zone_GSL_Scattershot)"}
}
for _, name in ipairs({"Interrupt_GSL_HairTrigger", "Interrupt_GSL_CloseCall",
    "Interrupt_GSL_QuickOnTheDraw", "Interrupt_GSL_DoubleOrNothing"}) do
    interruptStats[name] = {Conditions = "OriginalInterruptCondition"}
end
for _, name in ipairs({"Projectile_GSL_DisarmingShot", "Projectile_GSL_RapidShot",
    "Projectile_GSL_HotStreak_1", "Projectile_GSL_FanningFire_1", "Projectile_GSL_ViolentShot_1"}) do
    spellStats[name] = {RequirementConditions = "OriginalGritRequirement", SpellProperties = "", SpellRoll = ""}
end
local function fire(name, phase, ...)
    local listener = listeners[name .. ":" .. phase]
    if listener then listener(...) end
end
local function ticks()
    for _ = 1, 3 do events.Tick() end
end
Ext = {
    Require = function(path) return dofile(root .. path) end,
    Vars = {
        RegisterModVariable = function(uuid, name, flags)
            assert(uuid == rules.ModuleUUID and name == "Firearms" and flags.Persistent)
        end,
        GetModVariables = function() return variables end
    },
    Entity = {Get = function(id) return entities[id] end},
    Math = {Random = function(low, high)
        local roll = assert(table.remove(rolls, 1), "Unexpected random roll")
        assert(roll >= low and roll <= high)
        return roll
    end},
    Events = {},
    RegisterNetListener = function(channel, callback) netListeners[channel] = callback end,
    Json = {Parse = function(payload) return payload end},
    Stats = {
        GetStats = function(kind)
            local names = {}
            for name in pairs(kind == "Weapon" and weaponStats or spellStats) do names[#names + 1] = name end
            return names
        end,
        Get = function(name) return spellStats[name] or interruptStats[name] or weaponStats[name] end,
        Sync = function() end
    },
    Osiris = {RegisterListener = function(name, arity, phase, callback)
        assert(name ~= "CharacterKilledBy", "BG3 uses KilledBy, not the Divinity CharacterKilledBy event")
        if name == "KilledBy" then assert(arity == 4, "BG3 KilledBy has four arguments") end
        listeners[name .. ":" .. phase] = callback
    end},
    Utils = {Print = function(message) printed[#printed + 1] = message end},
    DumpExport = function() error("Unexpected runtime debug serialization") end
}
for _, name in ipairs({"StatsLoaded", "SessionLoaded", "Tick"}) do
    Ext.Events[name] = {Subscribe = function(_, callback)
        events[name] = function(...)
            osirisRestricted = name == "SessionLoaded" or name == "StatsLoaded"
            local ok, err = pcall(callback, ...)
            osirisRestricted = false
            assert(ok, err)
        end
    end}
end
local function ammo(char, hand)
    local id = hand == "Off" and rules.OffhandResource or rules.Firearms.Flintlock.resource
    return entities[char].ActionResources.Resources[id][1]
end
Osi = {
    DB_Players = {Get = function() return players end},
    GetEquippedItem = function(char, slot) return inventory[char] and inventory[char][slot] end,
    GetEquippedWeapon = function() return "melee" end,
    GetTemplate = function(item) return entities[item].template end,
    HasActiveStatus = function(id, status) return statuses[id] and statuses[id][status] and 1 or 0 end,
    ApplyStatus = function(id, status, duration, force, source)
        durations[status] = duration
        statuses[id] = statuses[id] or {}
        statuses[id][status] = true
        if status == "GSL_HOT_STREAK_COUNTER" then
            assert(force == 1 and source == id,
                "Hot Streak counter must be applied from its gunslinger")
            hotStreakStacks[id] = duration / 6
        end
    end,
    RemoveStatus = function(id, status)
        if statuses[id] then statuses[id][status] = nil end
        if status == "GSL_HOT_STREAK_COUNTER" then hotStreakStacks[id] = nil end
    end,
    AddBoosts = function(char, boost, source)
        assert(source ~= "GSL_AllIn", "Removed All In must never grant new boosts")
        local resource, amount = boost:match("ActionResource%(([^,]+),(%d+),0%)")
        assert(resource and amount, "Unexpected action-resource boost: " .. boost)
        local hand = resource:find("Offhand", 1, true) and "Off" or "Main"
        local entry = ammo(char, hand)
        entry.MaxAmount = entry.MaxAmount + tonumber(amount)
        entry.Amount = entry.Amount + tonumber(amount)
    end,
    RemoveBoosts = function(char, boost, _, source)
        if source == "GSL_AllIn" then
            assert(allInBoosts[char] == boost, "All In must remove exactly its previous variant")
            allInBoosts[char] = nil
            allInChanges = allInChanges + 1
            return
        end
        local resource, amount = boost:match("ActionResource%(([^,]+),(%d+),0%)")
        assert(resource and amount, "Unexpected action-resource boost: " .. boost)
        local hand = resource:find("Offhand", 1, true) and "Off" or "Main"
        local entry = ammo(char, hand)
        entry.MaxAmount = entry.MaxAmount - tonumber(amount)
        entry.Amount = math.min(entry.Amount, entry.MaxAmount)
    end,
    IsDead = function() return 0 end,
    HasPassive = function(char, passive) return passives[char] and passives[char][passive] and 1 or 0 end,
    AddPassive = function(char, passive)
        passives[char] = passives[char] or {}
        passives[char][passive] = true
        if passiveInterrupts[passive] then
            interrupts[char] = interrupts[char] or {}
            interrupts[char][passiveInterrupts[passive]] = true
        end
    end,
    RemovePassive = function(char, passive)
        if protectedPassives[char] and protectedPassives[char][passive] then return end
        if passives[char] then passives[char][passive] = nil end
        if interrupts[char] and passiveInterrupts[passive] then
            interrupts[char][passiveInterrupts[passive]] = nil
        end
    end,
    UseSpell = function(char, spell, target)
        assert(char == "alice" and target == "bob")
        assert(spell == "Projectile_GSL_DoubleOrNothingAttack" or spell == "Projectile_GSL_ReactionShot")
        if spell == "Projectile_GSL_DoubleOrNothingAttack" then
            doubleOrNothingAttacks = doubleOrNothingAttacks + 1
        end
    end
}
for name, callback in pairs(Osi) do
    if type(callback) == "function" then
        Osi[name] = function(...)
            assert(not osirisRestricted, "Attempted to call Osiris function in restricted context: " .. name)
            return callback(...)
        end
    end
end
local getPlayers = Osi.DB_Players.Get
Osi.DB_Players.Get = function(...)
    assert(not osirisRestricted, "Attempted to query Osiris database in restricted context")
    return getPlayers(...)
end
local function character(id)
    entities[id] = {
        ActionResources = {Resources = {
            [rules.Firearms.Flintlock.resource] = {{Level = 0, Amount = 3, MaxAmount = 3}},
            [rules.OffhandResource] = {{Level = 0, Amount = 3, MaxAmount = 3}}
        }},
        Health = {Hp = 30, MaxHp = 30},
        Replicate = function(_, component) assert(component == "ActionResources") end
    }
    inventory[id] = {}
end
local function gun(id)
    entities[id] = {
        template = "3d8b177d-89db-4826-8068-9f2d777faf04",
        Weapon = {WeaponRange = 13.5}, Value = {Rarity = 0},
        Replicate = function(_, component) assert(component == "Weapon") end
    }
end
character("alice")
character("bob")
character("charlie")
gun("first")
entities.first.template = "a710ad68-179b-4b0e-8ef2-3b37609a3f12"
gun("second")
inventory.alice["Ranged Main Weapon"] = "first"
inventory.alice["Ranged Offhand Weapon"] = "second"
dofile(root .. "BootstrapServer.lua")
events.StatsLoaded()
events.StatsLoaded()
for name, weapon in pairs(weaponStats) do
    for _, hand in ipairs(name:find("Flintlock", 1, true) and {"Main", "Off"} or {"Main"}) do
        local boosts = weapon["BoostsOnEquip" .. hand .. "Hand"]
        local _, count = boosts:gsub("UnlockSpell%(Shout_GSL_Repair_" .. hand .. "%)", "")
        assert(count == 1, name .. " must grant one equipment-owned Repair action per hand")
    end
end
assert(weaponStats.WPN_GSL_Flintlock_ArtificialLeech.BoostsOnEquipMainHand:find(
    "UnlockSpell(Projectile_GSL_Bloodletting_Flintlock)", 1, true))
assert(weaponStats.WPN_GSL_Flintlock_ArtificialLeech.BoostsOnEquipOffHand:find("AC(1)", 1, true))
local function repairAvailable(character, hand)
    local item = inventory[character][hand == "Off" and "Ranged Offhand Weapon" or "Ranged Main Weapon"]
    if not item then return false end
    for _, weapon in pairs(weaponStats) do
        if weapon.RootTemplate == entities[item].template then
            return (weapon["BoostsOnEquip" .. hand .. "Hand"] or ""):find(
                "UnlockSpell(Shout_GSL_Repair_" .. hand .. ")", 1, true) ~= nil
        end
    end
    return false
end
local function repairUsable(character, hand)
    local item = inventory[character][hand == "Off" and "Ranged Offhand Weapon" or "Ranged Main Weapon"]
    return repairAvailable(character, hand) and Osi.HasActiveStatus(item, "GSL_FIREARM_ITEM_MISFIRED") == 1 and
        Osi.HasActiveStatus(item, "GSL_FIREARM_ITEM_DESTROYED") == 0
end
assert(repairAvailable("alice", "Main") and repairAvailable("alice", "Off") and
    not repairUsable("alice", "Main") and not repairUsable("alice", "Off"),
    "Equipped working guns must grant Repair but cannot use it")
local function brokenGuard(hand, character)
    return "not HasStatus('GSL_FIREARM_ITEM_DESTROYED',GetItemInEquipmentSlot(EquipmentSlot." ..
        (hand == "Off" and "RangedOffHand" or "RangedMainHand") .. "," .. character .. "))"
end
for name, spell in pairs(spellStats) do
    local offhand = name:find("OffHand", 1, true) or name == "Projectile_OffhandAttack"
    local condition = brokenGuard(offhand and "Off" or "Main", "context.Source")
    assert(spell.RequirementConditions:find(condition, 1, true), name .. " must check the gun's Broken status")
    local _, guards = spell.RequirementConditions:gsub(condition:gsub("(%W)", "%%%1"), "")
    assert(guards == 1, "Stats reload must not duplicate Broken checks for " .. name)
end
for name, interrupt in pairs(interruptStats) do
    assert(interrupt.Conditions:find(brokenGuard("Main", "context.Observer"), 1, true),
        name .. " must check the observing gunslinger's gun, not the attacker's")
    assert(interrupt.Conditions:find("OriginalInterruptCondition", 1, true))
end
spellStats.Shout_GSL_BiteTheBullet = {RequirementConditions = "", SpellProperties = "", SpellRoll = ""}
spellStats.Target_GSL_FlashPowder = {RequirementConditions = "", SpellProperties = "", SpellRoll = ""}
events.StatsLoaded()
assert(spellStats.Shout_GSL_BiteTheBullet.RequirementConditions == "" and
    spellStats.Target_GSL_FlashPowder.RequirementConditions == "",
    "Broken guns must not disable non-firearm grit abilities")
assert(spellStats.Projectile_GSL_Bloodletting_Flintlock.SpellProperties == "", "Bloodletting must not be charged twice")
local _, costs = spellStats.Zone_GSL_LineEmUp.SpellProperties:gsub("UseActionResource", "")
assert(costs == 3, "A stats reload must not duplicate ammo costs")
assert(spellStats.Zone_GSL_LineEmUp.SpellProperties:find("OriginalEffect", 1, true))
local special = spellStats.Projectile_PiercingShot
assert(special.RequirementConditions:find("OriginalRequirement", 1, true))
assert(special.RequirementConditions:find("(not (", 1, true), "Ordinary bows must retain their normal requirements")
assert(special.SpellProperties:find("OriginalPiercingEffect", 1, true))
local _, specialCosts = special.SpellProperties:gsub("UseActionResource", "")
assert(specialCosts == 3, "Native actions must not double-charge on stats reload")
fire("Equipped", "after", "first", "alice")
ticks()
assert(variables.Firearms.weapons.first.kind == "Flintlock", "Fused Flintlocks must track ammunition and firearm state")
local function cast(spell, action)
    fire("UsingSpell", "before", "alice", spell, "", "", action)
    fire("CastedSpell", "after", "alice", spell, "", "", action)
end
cast("Shout_GSL_Tinkerer_MainCapacity", 1)
assert(ammo("alice", "Main").MaxAmount == 6 and ammo("alice", "Main").Amount == 3)
assert(ammo("alice", "Off").MaxAmount == 3, "Primary capacity must not modify the other gun")
assert(Osi.HasActiveStatus("first", "GSL_TINKERER_CAPACITY") == 1, "Capacity must show on the modified gun")
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_CAPACITY") == 0)
fire("UsingSpell", "before", "alice", "Shout_GSL_Reload_Flintlock", "", "", 11)
ammo("alice", "Main").Amount = 6
fire("CastedSpell", "after", "alice", "Shout_GSL_Reload_Flintlock", "", "", 11)
assert(variables.Firearms.weapons.first.ammo == 6, "Reload must snapshot upgraded capacity")
cast("Shout_GSL_Tinkerer_MainRange", 2)
assert(ammo("alice", "Main").MaxAmount == 3)
assert(Osi.HasActiveStatus("first", "GSL_TINKERER_CAPACITY") == 0, "A replaced mod must leave the gun")
assert(Osi.HasActiveStatus("first", "GSL_TINKERER_RANGE_FLINTLOCK") == 1)
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_RANGE_FLINTLOCK") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_MAIN_RANGE_FLINTLOCK") == 1, "Main range must extend main-hand shots")
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_OFF_RANGE") == 0)
assert(entities.first.Weapon.WeaponRange == 13.5, "Range must not edit the Weapon component")
cast("Shout_GSL_Tinkerer_OffDamage", 3)
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_DAMAGE_FLINTLOCK") == 1)
assert(Osi.HasActiveStatus("first", "GSL_TINKERER_DAMAGE_FLINTLOCK") == 0)
cast("Shout_GSL_Tinkerer_OffRange", 31)
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_DAMAGE_FLINTLOCK") == 0, "Below level 10 a new mod replaces the old one")
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_OFF_RANGE") == 1)
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_RANGE_FLINTLOCK") == 1, "Secondary range must show on that gun")
passives.alice = {GSL_MasterTinkerer = true}
cast("Shout_GSL_Tinkerer_OffDamage", 32)
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_DAMAGE_FLINTLOCK") == 1, "Master Tinkerer keeps two mods")
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_OFF_RANGE") == 1)
cast("Shout_GSL_Tinkerer_OffDamage", 33)
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_DAMAGE_FLINTLOCK") == 0)
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_MASTER_DAMAGE_FLINTLOCK") == 1,
    "Repeating Damage with Master Tinkerer must activate its master tier")
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_OFF_RANGE") == 0)
cast("Shout_GSL_Tinkerer_OffRange", 36)
cast("Shout_GSL_Tinkerer_OffRange", 37)
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_OFF_RANGE") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_OFF_RANGE_MASTER") == 1,
    "Repeating Range with Master Tinkerer must activate its master range")
cast("Shout_GSL_Tinkerer_MainCapacity", 34)
assert(ammo("alice", "Main").MaxAmount == 6)
cast("Shout_GSL_Tinkerer_MainCapacity", 35)
assert(ammo("alice", "Main").MaxAmount == 9, "A second Ammo upgrade must triple base capacity")
assert(Osi.HasActiveStatus("first", "GSL_TINKERER_CAPACITY") == 0)
assert(Osi.HasActiveStatus("first", "GSL_TINKERER_MASTER_AMMO") == 1)
cast("Shout_GSL_Tinkerer_MainRange", 38)
cast("Shout_GSL_Tinkerer_MainRange", 39)
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_MAIN_RANGE_MASTER_FLINTLOCK") == 1,
    "Repeating main-hand Range must activate its doubled range boost")
cast("Shout_GSL_Tinkerer_MainDamage", 40)
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_MAIN_RANGE_FLINTLOCK") == 1,
    "A remaining single Range upgrade must use the ordinary range boost")
cast("Shout_GSL_Tinkerer_OffDamage", 41)
cast("Shout_GSL_Tinkerer_OffDamage", 42)
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_MASTER_DAMAGE_FLINTLOCK") == 1,
    "Master Tinkerer damage must be applied to the modified firearm")
cast("Shout_GSL_Tinkerer_MainRange", 43)
cast("Shout_GSL_Tinkerer_MainRange", 44)
assert(Osi.HasActiveStatus("first", "GSL_TINKERER_MASTER_RANGE_FLINTLOCK") == 1,
    "Master Tinkerer range must be applied to the modified firearm")
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_MAIN_RANGE_MASTER_FLINTLOCK") == 1,
    "Master Tinkerer range must affect attacks with the modified firearm")
fire("UsingSpell", "before", "alice", "GSL_OffHand_Flintlock_attack", "", "", 4)
ammo("alice", "Off").Amount = 2
fire("StatusApplied", "after", "alice", "GSL_MISFIRE", "alice", 4)
assert(variables.Firearms.weapons.second.misfire and not variables.Firearms.weapons.first.misfire)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_DISABLED") == 0, "A misfire must not stop the gun firing")
assert(Osi.HasActiveStatus("second", "GSL_FIREARM_ITEM_MISFIRED") == 1)
assert(repairUsable("alice", "Off") and not repairUsable("alice", "Main"),
    "Only the misfired gun's permanent Repair action becomes usable")
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_MISFIRED") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_MAIN_MISFIRED") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_OFF") == 1, "The wielder must receive the misfired gun's Repair unlock")
assert(Osi.HasActiveStatus("second", "GSL_REPAIR_MENU_OFF_RAPID") == 0)
assert(Osi.HasActiveStatus("first", "GSL_REPAIR_MENU_MAIN") == 0, "Only the misfired gun grants Repair")
assert(Osi.HasActiveStatus("second", "GSL_REPAIR_MENU_OFF") == 0, "Item statuses must not own the character's spell unlock")
fire("Unequipped", "before", "second", "alice")
inventory.alice["Ranged Offhand Weapon"] = nil
fire("Unequipped", "after", "second", "alice")
inventory.bob["Ranged Main Weapon"] = "second"
fire("Equipped", "after", "second", "bob")
ticks()
assert(Osi.HasActiveStatus("bob", "GSL_REPAIR_MENU_MAIN") == 1 and
    Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_OFF") == 0,
    "A transferred misfired gun must grant Repair to its new wielder only")
fire("Unequipped", "before", "second", "bob")
assert(Osi.HasActiveStatus("bob", "GSL_REPAIR_MENU_MAIN") == 0,
    "Unequipping must remove the old repair passive and its attack penalty")
inventory.bob["Ranged Main Weapon"] = nil
fire("Unequipped", "after", "second", "bob")
ticks()
inventory.alice["Ranged Offhand Weapon"] = "second"
local legacyStatuses = {
    "GSL_FIREARM_MAIN_DESTROYED", "GSL_FIREARM_OFF_MISFIRED", "GSL_REPAIR_MENU_MAIN_RAPID",
    "GSL_MISFIRE", "GSL_DOUBLE_LOAD_BROKEN"
}
for _, name in ipairs(legacyStatuses) do Osi.ApplyStatus("alice", name, -1, 1, "alice") end
Osi.ApplyStatus("second", "GSL_REPAIR_MENU_OFF", -1, 1, "second")
fire("Equipped", "after", "second", "alice")
events.SessionLoaded()
ticks()
for _, name in ipairs(legacyStatuses) do
    assert(Osi.HasActiveStatus("alice", name) == 0, "Refresh must retire saved character status " .. name)
end
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_OFF") == 1)
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_OFF") == 1 and
    Osi.HasActiveStatus("second", "GSL_REPAIR_MENU_OFF") == 0,
    "Loading a save must replace legacy item-owned unlocks with wielder-owned unlocks")
fire("UsingSpell", "before", "alice", "Shout_GSL_FieldRepair_Off", "", "", 45)
fire("CastedSpell", "after", "alice", "Shout_GSL_FieldRepair_Off", "", "", 45)
assert(variables.Firearms.weapons.second.misfire, "A failed field repair must leave the firearm misfired")
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_OFF") == 1,
    "A failed repair must leave Repair available to the wielder")
fire("CastedSpell", "after", "alice", "GSL_OffHand_Flintlock_attack", "", "", 4)
passives.alice.GSL_RapidRepairUnlock = true
fire("UsingSpell", "before", "alice", "Shout_GSL_RapidRepair_Off", "", "", 5)
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_OFF_RAPID") == 1, "Rapid Repair must unlock on the wielder")
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_OFF") == 0)
local function firearmUsable(name, character)
    local condition = spellStats[name].RequirementConditions
    local slot = condition:match("GetItemInEquipmentSlot%(EquipmentSlot%.(%w+),context%.Source%)")
    assert(slot, "Attack must check the physical gun")
    local hand = slot == "RangedOffHand" and "Off" or "Main"
    local item = inventory[character][hand == "Off" and "Ranged Offhand Weapon" or "Ranged Main Weapon"]
    return Osi.HasActiveStatus(item, "GSL_FIREARM_ITEM_DESTROYED") == 0
end
fire("StatusApplied", "after", "alice", "GSL_REPAIR_OFF_DONE", "alice", 5)
fire("CastedSpell", "after", "alice", "Shout_GSL_RapidRepair_Off", "", "", 5)
assert(not variables.Firearms.weapons.second.misfire)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_MISFIRED") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_OFF_RAPID") == 0, "Repairing removes the wielder's Repair unlock")
assert(Osi.HasActiveStatus("second", "GSL_FIREARM_ITEM_MISFIRED") == 0)
assert(repairAvailable("alice", "Off") and not repairUsable("alice", "Off"),
    "Successful Repair must disable, not remove, the equipment action")
fire("UsingSpell", "before", "alice", "GSL_MainHand_Flintlock_attack", "", "", 43)
fire("StatusApplied", "after", "alice", "GSL_MISFIRE", "alice", 43)
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_MAIN_RAPID") == 1)
fire("CastedSpell", "after", "alice", "GSL_MainHand_Flintlock_attack", "", "", 43)
fire("UsingSpell", "before", "alice", "Shout_GSL_FieldRepair_Main_R", "", "", 44)
fire("StatusApplied", "after", "alice", "GSL_FIELD_REPAIR_MAIN_DONE", "alice", 44)
fire("CastedSpell", "after", "alice", "Shout_GSL_FieldRepair_Main_R", "", "", 44)
assert(not variables.Firearms.weapons.first.misfire)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_MAIN_MISFIRED") == 0)
fire("StatusApplied", "after", "alice", "GSL_MISFIRE", "alice", 99)
assert(variables.Firearms.weapons.first.misfire, "An untracked nat 1 must misfire the equipped firearm, not the melee weapon")
for action = 41, 42 do
    fire("UsingSpell", "before", "alice", "GSL_OffHand_Flintlock_attack", "", "", action)
    fire("StatusApplied", "after", "alice", "GSL_MISFIRE", "alice", action)
    fire("CastedSpell", "after", "alice", "GSL_OffHand_Flintlock_attack", "", "", action)
    if action == 41 then
        assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_MAIN_RAPID") == 1 and
            Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_OFF_RAPID") == 1,
            "Two misfired guns must grant independent Repair menus to their wielder")
    end
end
assert(variables.Firearms.weapons.second.broken, "Misfiring a misfired gun must break it")
assert(repairAvailable("alice", "Off") and not repairUsable("alice", "Off"),
    "Broken guns retain the equipment action but cannot use Repair")
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_DISABLED") == 1)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_MISFIRED") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_DESTROYED") == 0, "Broken belongs only to the gun")
assert(Osi.HasActiveStatus("second", "GSL_FIREARM_ITEM_DESTROYED") == 1 and Osi.HasActiveStatus("second", "GSL_FIREARM_ITEM_MISFIRED") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_OFF_RAPID") == 0, "A broken gun cannot grant Repair")
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_OFF") == 0)
Osi.RemoveStatus("alice", "GSL_FIREARM_OFF_DISABLED")
assert(not firearmUsable("GSL_OffHand_Flintlock_attack", "alice"),
    "Broken must block the basic shot even without a character disable marker")
assert(not firearmUsable("Projectile_GSL_TwoGunTango_OffHand", "alice"),
    "Broken must block an offhand grit shot")
assert(firearmUsable("GSL_MainHand_Flintlock_attack", "alice"),
    "A broken offhand must not block the working main-hand firearm")
fire("UsingSpell", "before", "alice", "Shout_GSL_FieldRepair_Main_R", "", "", 100)
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_MAIN_RAPID") == 1,
    "A broken offhand gun must not block repairing the misfired main-hand gun")
fire("StatusApplied", "after", "alice", "GSL_FIELD_REPAIR_MAIN_DONE", "alice", 100)
fire("CastedSpell", "after", "alice", "Shout_GSL_FieldRepair_Main_R", "", "", 100)
assert(not variables.Firearms.weapons.first.misfire and variables.Firearms.weapons.second.broken)
fire("UsingSpell", "before", "alice", "Projectile_GSL_DoubleLoad", "", "", 6)
fire("StatusApplied", "after", "alice", "GSL_DOUBLE_LOAD_BROKEN", "alice", 6)
fire("CastedSpell", "after", "alice", "Projectile_GSL_DoubleLoad", "", "", 6)
assert(variables.Firearms.weapons.first.broken)
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_MAIN_RAPID") == 0)
fire("Unequipped", "before", "first", "alice")
inventory.alice["Ranged Main Weapon"] = nil
fire("Unequipped", "after", "first", "alice")
inventory.bob["Ranged Main Weapon"] = "first"
fire("Equipped", "after", "first", "bob")
ticks()
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_MAIN_DISABLED") == 0)
assert(Osi.HasActiveStatus("bob", "GSL_FIREARM_MAIN_DISABLED") == 1, "Broken state must follow the physical gun")
Osi.RemoveStatus("bob", "GSL_FIREARM_MAIN_DISABLED")
for _, name in ipairs({"GSL_MainHand_Flintlock_attack", "Projectile_GSL_DisarmingShot",
    "Projectile_GSL_RapidShot", "Projectile_GSL_HotStreak_1", "Projectile_GSL_FanningFire_1",
    "Projectile_GSL_ViolentShot_1", "Zone_GSL_LineEmUp", "Zone_GSL_PiercingRound",
    "Shout_GSL_HailOfLead", "Zone_GSL_Scattershot", "Zone_GSL_Scattershot_PoisonMist",
    "Projectile_GSL_ReactionShot"}) do
    assert(not firearmUsable(name, "bob"), name .. " must not use a broken firearm")
end
gun("replacement")
inventory.alice["Ranged Main Weapon"] = "replacement"
fire("Equipped", "after", "replacement", "alice")
ticks()
assert(firearmUsable("GSL_MainHand_Flintlock_attack", "alice") and
    firearmUsable("Projectile_GSL_DisarmingShot", "alice"),
    "Equipping a working replacement must restore its basic and grit attacks")
fire("UsingSpell", "before", "alice", "GSL_MainHand_Flintlock_attack", "", "", 101)
fire("StatusApplied", "after", "alice", "GSL_MISFIRE", "alice", 101)
fire("CastedSpell", "after", "alice", "GSL_MainHand_Flintlock_attack", "", "", 101)
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_MAIN_RAPID") == 1,
    "A newly crafted replacement must grant Repair even while the original gun is broken")
fire("UsingSpell", "before", "alice", "Shout_GSL_FieldRepair_Main_R", "", "", 102)
fire("StatusApplied", "after", "alice", "GSL_FIELD_REPAIR_MAIN_DONE", "alice", 102)
fire("CastedSpell", "after", "alice", "Shout_GSL_FieldRepair_Main_R", "", "", 102)
assert(not variables.Firearms.weapons.replacement.misfire and variables.Firearms.weapons.first.broken,
    "Repair must affect only the replacement, leaving the original broken")
fire("Unequipped", "before", "replacement", "alice")
inventory.alice["Ranged Main Weapon"] = nil
fire("Unequipped", "after", "replacement", "alice")
ticks()
assert(Osi.HasActiveStatus("bob", "GSL_TINKERER_MAIN_RANGE_MASTER_FLINTLOCK") == 1,
    "Master range must follow the physical gun")
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_MAIN_RANGE_FLINTLOCK") == 0)
statuses.first.GSL_TINKERER_MASTER_RANGE_FLINTLOCK = nil
variables.Firearms.weapons.second.baseRange = 13.5
entities.second.Weapon.WeaponRange = 19.5
events.SessionLoaded()
local boundPlayers = Osi.DB_Players
Osi.DB_Players = nil
local printedBefore = #printed
for _ = 1, 6 do events.Tick() end
assert(#printed == printedBefore, "Session refresh must wait until the Osiris story is bound")
Osi.DB_Players = boundPlayers
ticks()
assert(Osi.HasActiveStatus("first", "GSL_TINKERER_MASTER_RANGE_FLINTLOCK") == 1,
    "Saved master modification must be reapplied")
assert(entities.second.Weapon.WeaponRange == 13.5 and not variables.Firearms.weapons.second.baseRange,
    "Legacy Weapon component range edits must be undone")
fire("LongRestFinished", "after")
assert(not variables.Firearms.weapons.first.broken and not variables.Firearms.weapons.second.broken)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_DISABLED") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_DESTROYED") == 0 and Osi.HasActiveStatus("second", "GSL_FIREARM_ITEM_DESTROYED") == 0)
assert(Osi.HasActiveStatus("first", "GSL_TINKERER_RANGE_FLINTLOCK") == 0)
assert(Osi.HasActiveStatus("bob", "GSL_TINKERER_MAIN_RANGE_FLINTLOCK") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_OFF_RANGE") == 0)
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_DAMAGE_FLINTLOCK") == 0)
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_MASTER_DAMAGE_FLINTLOCK") == 1,
    "Long rests must preserve master damage on the physical gun")
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_RANGE_FLINTLOCK") == 0)
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_MASTER_RANGE_FLINTLOCK") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_OFF_RANGE_MASTER") == 0)
assert(Osi.HasActiveStatus("first", "GSL_TINKERER_MASTER_RANGE_FLINTLOCK") == 1)
assert(Osi.HasActiveStatus("bob", "GSL_TINKERER_MAIN_RANGE_MASTER_FLINTLOCK") == 1,
    "Long rests must preserve the wielder's master range bonus")
assert(ammo("bob", "Main").Amount == 3 and ammo("alice", "Off").Amount == 3)
fire("Unequipped", "before", "first", "bob")
inventory.bob["Ranged Main Weapon"] = nil
fire("Unequipped", "after", "first", "bob")
inventory.alice["Ranged Main Weapon"] = "first"
fire("Equipped", "after", "first", "alice")
ticks()
cast("Shout_GSL_Tinkerer_MainCapacity", 70)
cast("Shout_GSL_Tinkerer_MainCapacity", 71)
fire("LongRestFinished", "after")
assert(Osi.HasActiveStatus("first", "GSL_TINKERER_MASTER_AMMO") == 1)
assert(ammo("alice", "Main").MaxAmount == 9 and ammo("alice", "Main").Amount == 9,
    "Long rests must refill the upgraded capacity without removing it")
fire("UsingSpell", "before", "alice", "Shout_GSL_Tinkerer_MainRemove", "", "", 72)
fire("CastSpellFailed", "after", "alice", "Shout_GSL_Tinkerer_MainRemove", "", "", 72)
assert(Osi.HasActiveStatus("first", "GSL_TINKERER_MASTER_AMMO") == 1,
    "A cancelled removal must leave upgrades intact")
cast("Shout_GSL_Tinkerer_MainRemove", 73)
assert(#variables.Firearms.weapons.first.mods == 0)
assert(Osi.HasActiveStatus("first", "GSL_TINKERER_MASTER_AMMO") == 0)
assert(ammo("alice", "Main").MaxAmount == 3 and ammo("alice", "Main").Amount == 3,
    "Removing capacity must remove the resource boost and clamp excess bullets")
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_MASTER_DAMAGE_FLINTLOCK") == 1,
    "Primary removal must not affect the secondary firearm")
cast("Shout_GSL_Tinkerer_OffRemove", 74)
assert(#variables.Firearms.weapons.second.mods == 0)
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_MASTER_DAMAGE_FLINTLOCK") == 0)
cast("Shout_GSL_Tinkerer_MainRange", 75)
cast("Shout_GSL_Tinkerer_MainDamage", 76)
cast("Shout_GSL_Tinkerer_OffRange", 77)
cast("Shout_GSL_Tinkerer_OffRange", 78)
cast("Shout_GSL_Tinkerer_MainRemove", 79)
assert(Osi.HasActiveStatus("first", "GSL_TINKERER_RANGE_FLINTLOCK") == 0)
assert(Osi.HasActiveStatus("first", "GSL_TINKERER_DAMAGE_FLINTLOCK") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_MAIN_RANGE_FLINTLOCK") == 0,
    "Removal must clear mixed modifications and their wielder bonuses")
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_OFF_RANGE_MASTER") == 1)
cast("Shout_GSL_Tinkerer_OffRemove", 80)
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_MASTER_RANGE_FLINTLOCK") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_OFF_RANGE_MASTER") == 0)
events.SessionLoaded()
ticks()
fire("LongRestFinished", "after")
assert(#variables.Firearms.weapons.first.mods == 0 and #variables.Firearms.weapons.second.mods == 0,
    "Removed modifications must stay removed after save/load and rest")
fire("UsingSpell", "before", "alice", "Projectile_GSL_FanningFire_2", "", "", 7)
fire("CastSpellFailed", "after", "alice", "Projectile_GSL_FanningFire_2", "", "", 7)
assert(variables.Firearms.weapons.first.ammo == ammo("alice", "Main").Amount)
local lastWordShots = 0
local useSpell = Osi.UseSpell
Osi.UseSpell = function(...) lastWordShots = lastWordShots + 1; return useSpell(...) end
ticks()
Osi.ApplyStatus("alice", "GSL_LASTWORD_PENDING")
fire("StatusApplied", "after", "alice", "GSL_LASTWORD_PENDING", "alice", 8)
assert(Osi.HasActiveStatus("alice", "GSL_LASTWORD_PENDING") == 1 and lastWordShots == 0, "Last Word waits for its attacker")
fire("AttackedBy", "after", "alice", "bob", "bob", "Piercing", 10, "Attack", 9)
assert(Osi.HasActiveStatus("alice", "GSL_LASTWORD_PENDING") == 0 and lastWordShots == 1, "Last Word shoots once the attacker is known")
fire("AttackedBy", "after", "alice", "bob", "bob", "Piercing", 10, "Attack", 10)
assert(lastWordShots == 1, "Last Word fires only once")
Osi.ApplyStatus("alice", "GSL_LASTWORD_PENDING")
fire("StatusApplied", "after", "alice", "GSL_LASTWORD_PENDING", "alice", 11)
assert(Osi.HasActiveStatus("alice", "GSL_LASTWORD_PENDING") == 0 and lastWordShots == 2, "Last Word shoots an attacker reported earlier in the same tick")
Osi.ApplyStatus("first", "GSL_FIREARM_ITEM_DESTROYED", -1, 1, "first")
Osi.ApplyStatus("alice", "GSL_LASTWORD_PENDING")
fire("StatusApplied", "after", "alice", "GSL_LASTWORD_PENDING", "alice", 13)
assert(lastWordShots == 2 and Osi.HasActiveStatus("alice", "GSL_LASTWORD_PENDING") == 0,
    "Last Word's forced counterattack must not fire a broken gun")
Osi.RemoveStatus("first", "GSL_FIREARM_ITEM_DESTROYED")
ticks()
Osi.ApplyStatus("alice", "GSL_LASTWORD_PENDING")
fire("StatusApplied", "after", "alice", "GSL_LASTWORD_PENDING", "alice", 12)
assert(lastWordShots == 2, "Stale attackers from earlier ticks are ignored")
Osi.RemoveStatus("alice", "GSL_LASTWORD_PENDING")
Osi.UseSpell = useSpell
for _, name in ipairs({"Zone_GSL_PiercingRound", "Shout_GSL_HailOfLead"}) do
    local _, count = spellStats[name].SpellProperties:gsub("UseActionResource", "")
    assert(count == 3, name .. " must spend main-hand ammunition")
    assert(spellStats[name].RequirementConditions:find(brokenGuard("Main", "context.Source"), 1, true))
end
local function shot(spell, action, ...)
    for _, roll in ipairs({...}) do rolls[#rolls + 1] = roll end
    cast(spell, action)
    assert(#rolls == 0, spell .. " consumed the wrong number of rolls")
end
shot("Projectile_GSL_ViolentShot_2", 50, 3)
assert(not variables.Firearms.weapons.first.misfire, "Violent Shot misfires only on d20 <= grit")
shot("Projectile_GSL_ViolentShot_2", 51, 2)
assert(variables.Firearms.weapons.first.misfire and Osi.HasActiveStatus("first", "GSL_FIREARM_ITEM_MISFIRED") == 1)
fire("LongRestFinished", "after")
rolls[1] = 11
fire("AttackedBy", "after", "bob", "alice", "alice", "Piercing", 10, "Attack", 52)
events.Tick()
fire("UsingSpell", "before", "alice", "Projectile_GSL_DoubleOrNothing", "", "", 52)
fire("CastedSpell", "after", "alice", "Projectile_GSL_DoubleOrNothing", "", "", 52)
assert(doubleOrNothingAttacks == 1 and not variables.Firearms.weapons.first.misfire,
    "A winning Double or Nothing makes a free attack against the original target")
shot("Projectile_GSL_DoubleOrNothing", 53, 10)
assert(variables.Firearms.weapons.first.misfire, "A losing Double or Nothing misfires")
assert(Osi.HasActiveStatus("alice", "GSL_CHEAT_DEATHS_ODDS_REFUND") == 0)
fire("LongRestFinished", "after")
ammo("alice", "Main").Amount = 2
fire("UsingSpell", "before", "alice", "Projectile_GSL_FanningFire_1", "", "", 61)
fire("CastedSpell", "after", "alice", "Projectile_GSL_FanningFire_1", "", "", 61)
assert(ammo("alice", "Main").Amount == 0, "Fanning Fire spends one bullet per shot once per cast")
assert(variables.Firearms.weapons.first.ammo == 0)
ammo("alice", "Main").Amount = 3
shot("Shout_GSL_RollTheBones", 55, 1)
assert(Osi.HasActiveStatus("alice", "GSL_RTB_BUST") == 1 and durations.GSL_RTB_BUST == 12)
shot("Shout_GSL_RollTheBones", 56, 6)
assert(Osi.HasActiveStatus("alice", "GSL_RTB_BUST") == 0 and Osi.HasActiveStatus("alice", "GSL_RTB_JACKPOT") == 1)
passives.alice.GSL_Desperado_CheatDeathsOdds = true
entities.alice.Health.Hp = 14
shot("Shout_GSL_RollTheBones", 57, 3)
assert(Osi.HasActiveStatus("alice", "GSL_CHEAT_DEATHS_ODDS_REFUND") == 0, "One-grit abilities never refund")
fire("AttackedBy", "after", "bob", "alice", "alice", "Piercing", 10, "Attack", 58)
shot("Projectile_GSL_DoubleOrNothing", 58, 11)
assert(Osi.HasActiveStatus("alice", "GSL_CHEAT_DEATHS_ODDS_REFUND") == 0, "The free follow-up shot refunds nothing; the reaction does")
shot("Projectile_GSL_DazingShot", 59)
assert(Osi.HasActiveStatus("alice", "GSL_CHEAT_DEATHS_ODDS_REFUND") == 1, "Bloodied 2-grit abilities refund 1 grit")
assert(durations.GSL_CHEAT_DEATHS_ODDS_REFUND == 0)
local bonusAction = {Level = 0, Amount = 1, MaxAmount = 1}
entities.alice.ActionResources.Resources["420c8df5-45c2-4253-93c2-7ec44e127930"] = {bonusAction}
local function reloadCosts()
    for _ = 1, 5 do events.Tick() end
    return Osi.HasActiveStatus("alice", "GSL_RELOAD_NO_BONUS_ACTION"), Osi.HasActiveStatus("alice", "GSL_QUICK_FULL_RELOAD")
end
local noBonus, quickFull = reloadCosts()
assert(noBonus == 0 and quickFull == 0, "Reloads cost a bonus action while one remains; Full Reload stays an action")
bonusAction.Amount = 0
noBonus, quickFull = reloadCosts()
assert(noBonus == 1 and quickFull == 0, "Without a bonus action the reloads cost an action")
passives.alice.GSL_Feat_QuickReload_Marker = true
noBonus, quickFull = reloadCosts()
assert(noBonus == 1 and quickFull == 0, "Quick Reload's Full Reload falls back to an action")
bonusAction.Amount = 1
noBonus, quickFull = reloadCosts()
assert(noBonus == 0 and quickFull == 1, "Quick Reload makes Full Reload a bonus action while one remains")
Osi.ApplyStatus("alice", "GSL_GRIT_RECOVERY_SPENT", 1)
fire("UsingSpell", "before", "alice", "Projectile_FireBolt", "", "", 60)
assert(Osi.HasActiveStatus("alice", "GSL_GRIT_RECOVERY_SPENT") == 0, "Any new attack re-arms Grit Recovery")
Osi.ApplyStatus("alice", "GSL_GRIT_RECOVERY_SPENT", 1)
fire("TurnStarted", "after", "alice")
assert(Osi.HasActiveStatus("alice", "GSL_GRIT_RECOVERY_SPENT") == 0, "A new turn re-arms Grit Recovery")
local mainGun = Osi.GetEquippedItem("alice", "Ranged Main Weapon")
assert(mainGun and not variables.Firearms.weapons[mainGun].broken, "Arcane Reload test needs a working main gun")
ammo("alice", "Main").Amount = 0
ammo("alice", "Off").Amount = 0
fire("TurnStarted", "after", "alice")
assert(ammo("alice", "Main").Amount == 0, "Without Arcane Reload nothing reloads")
Osi.ApplyStatus(mainGun, "GSL_ARCANE_RELOAD", -1)
fire("TurnStarted", "after", "alice")
assert(ammo("alice", "Main").Amount == 1, "Arcane Reload adds one bullet each turn")
assert(variables.Firearms.weapons[mainGun].ammo == 1, "Arcane Reload's bullet is saved on the gun")
assert(ammo("alice", "Off").Amount == 0, "Only the enchanted gun reloads")
ammo("alice", "Main").Amount = ammo("alice", "Main").MaxAmount
fire("TurnStarted", "after", "alice")
assert(ammo("alice", "Main").Amount == ammo("alice", "Main").MaxAmount, "Arcane Reload never exceeds capacity")
Osi.RemoveStatus(mainGun, "GSL_ARCANE_RELOAD")
character("carol")
entities.carol.ActionResources.Resources[rules.Firearms.Musket.resource] = {{Level = 0, Amount = 1, MaxAmount = 1}}
gun("longarm")
entities.longarm.template = "1da91e88-3f0e-4ccc-ac25-0bdf00426880"
inventory.carol["Ranged Main Weapon"] = "longarm"
fire("Equipped", "after", "longarm", "carol")
ticks()
assert(Osi.HasActiveStatus("carol", "GSL_LONGARM_SPECIALIST_RANGE") == 0, "Longarm range needs the feat")
passives.carol = {GSL_Feat_LongarmSpecialist_Range = true}
fire("TurnStarted", "after", "carol")
assert(Osi.HasActiveStatus("carol", "GSL_LONGARM_SPECIALIST_RANGE") == 1, "Longarm Specialist extends musket range")
passives.alice.GSL_Feat_LongarmSpecialist_Range = true
fire("TurnStarted", "after", "alice")
assert(Osi.HasActiveStatus("alice", "GSL_LONGARM_SPECIALIST_RANGE") == 0, "Longarm range is musket-only")
inventory.carol["Ranged Main Weapon"] = nil
fire("Unequipped", "after", "longarm", "carol")
ticks()
assert(Osi.HasActiveStatus("carol", "GSL_LONGARM_SPECIALIST_RANGE") == 0, "Longarm range leaves with the musket")
inventory.carol["Ranged Main Weapon"] = "longarm"
fire("Equipped", "after", "longarm", "carol")
ticks()
fire("UsingSpell", "before", "carol", "Projectile_GSL_DoubleLoad", "", "", 70)
assert(Osi.HasActiveStatus("carol", "GSL_DOUBLE_LOAD") == 1, "Double Load's misfire passive must be active before the roll")
fire("StatusApplied", "after", "carol", "GSL_MISFIRE", "carol", 70)
fire("CastedSpell", "after", "carol", "Projectile_GSL_DoubleLoad", "", "", 70)
assert(variables.Firearms.weapons.longarm.broken, "A Double Load critical miss must break a working gun")
assert(Osi.HasActiveStatus("carol", "GSL_FIREARM_MAIN_DESTROYED") == 0, "Double Load must not mark the character Broken")
assert(Osi.HasActiveStatus("carol", "GSL_FIREARM_MAIN_MISFIRED") == 0)
assert(Osi.HasActiveStatus("carol", "GSL_DOUBLE_LOAD") == 0)
local musketAmmo = entities.carol.ActionResources.Resources[rules.Firearms.Musket.resource]
entities.carol.ActionResources.Resources[rules.Firearms.Musket.resource] = nil
assert(not pcall(fire, "TurnStarted", "after", "carol"), "A missing ammo resource must still raise")
entities.carol.ActionResources.Resources[rules.Firearms.Musket.resource] = musketAmmo
passives.carol.GSL_Feat_LongarmSpecialist_Range = nil
fire("TurnStarted", "after", "carol")
assert(Osi.HasActiveStatus("carol", "GSL_LONGARM_SPECIALIST_RANGE") == 0,
    "A failed refresh must not lock out every later refresh for that character")
local luck = "GSL_Desperado_DesperadosLuckUnlock"
local fortune = "GSL_Desperado_DesperadosFortuneUnlock"
local upgrade = "GSL_Desperado_FortuneUpgrade"
character("desperado")
Osi.AddPassive("desperado", upgrade)
fire("LeveledUp", "after", "desperado")
assert(Osi.HasPassive("desperado", fortune) == 0, "Level 15 must not grant Fortune without selecting Luck")
Osi.AddPassive("desperado", luck)
Osi.RemovePassive("desperado", upgrade)
fire("LeveledUp", "after", "desperado")
assert(Osi.HasPassive("desperado", fortune) == 0, "Luck must not upgrade before Desperado level 15")
assert(Osi.HasPassive("desperado", luck) == 1)
Osi.AddPassive("desperado", upgrade)
fire("LeveledUp", "after", "desperado")
assert(Osi.HasPassive("desperado", fortune) == 1, "Luck upgrades to an owned Fortune class feature without a firearm")
assert(Osi.HasPassive("desperado", luck) == 0, "The upgrade replaces Luck")
assert(not interrupts.desperado.Interrupt_GSL_DesperadosLuck and
    interrupts.desperado.Interrupt_GSL_DesperadosFortune, "Upgrade must retain only the Fortune reaction")
assert(variables.Firearms.fortuneUpgrades.desperado)
fire("LeveledUp", "after", "desperado")
events.SessionLoaded()
ticks()
assert(Osi.HasPassive("desperado", fortune) == 1, "Later levels and loading must preserve the upgrade")
fire("StartRespec", "before", "desperado")
assert(Osi.HasPassive("desperado", fortune) == 0, "Script-granted Fortune must not survive into a new build")
assert(Osi.HasPassive("desperado", luck) == 1, "Respec restores the original selection")
fire("RespecCancelled", "after", "desperado")
assert(Osi.HasPassive("desperado", fortune) == 1 and Osi.HasPassive("desperado", luck) == 0)
assert(not interrupts.desperado.Interrupt_GSL_DesperadosLuck and
    interrupts.desperado.Interrupt_GSL_DesperadosFortune, "Cancelling respec must restore only the Fortune reaction")
fire("StartRespec", "before", "desperado")
Osi.RemovePassive("desperado", luck)
fire("RespecCompleted", "after", "desperado")
assert(Osi.HasPassive("desperado", fortune) == 0, "Respeccing without Luck must leave Fortune unowned and untaken")
Osi.AddPassive("desperado", luck)
fire("RespecCompleted", "after", "desperado")
assert(Osi.HasPassive("desperado", fortune) == 1 and Osi.HasPassive("desperado", luck) == 0,
    "Respeccing with Luck at level 15 must perform the upgrade")
fire("StartRespec", "before", "desperado")
Osi.RemovePassive("desperado", upgrade)
fire("RespecCompleted", "after", "desperado")
assert(Osi.HasPassive("desperado", fortune) == 0, "Respeccing below Desperado level 15 must not grant Fortune")
Osi.RemovePassive("desperado", luck)
Osi.AddPassive("desperado", upgrade)
Osi.AddPassive("desperado", fortune)
fire("LeveledUp", "after", "desperado")
assert(Osi.HasPassive("desperado", fortune) == 1, "An explicitly selected Fortune must work without Luck")
fire("StartRespec", "before", "desperado")
assert(Osi.HasPassive("desperado", fortune) == 1, "Only script-granted Fortune is removed by the respec listener")
character("lateUpgrade")
players[#players + 1] = {"lateUpgrade"}
Osi.AddPassive("lateUpgrade", luck)
fire("LeveledUp", "after", "lateUpgrade")
Osi.AddPassive("lateUpgrade", upgrade)
for _ = 1, 10 do events.Tick() end
assert(Osi.HasPassive("lateUpgrade", fortune) == 1 and Osi.HasPassive("lateUpgrade", luck) == 0,
    "The upgrade must recover when progression passives arrive after the level-up event")

character("loadedUpgrade")
players[#players + 1] = {"loadedUpgrade"}
Osi.AddPassive("loadedUpgrade", luck)
Osi.AddPassive("loadedUpgrade", upgrade)
assert(not variables.Firearms.owners.loadedUpgrade and not variables.Firearms.fortuneUpgrades.loadedUpgrade)
events.SessionLoaded()
assert(Osi.HasPassive("loadedUpgrade", fortune) == 0, "SessionLoaded must defer Osiris calls until Tick")
events.Tick()
assert(Osi.HasPassive("loadedUpgrade", fortune) == 1 and Osi.HasPassive("loadedUpgrade", luck) == 0,
    "Loading must upgrade eligible players who have no tracked firearm or previous upgrade")
fire("StartRespec", "before", "loadedUpgrade")
for _ = 1, 10 do events.Tick() end
fire("TurnStarted", "after", "loadedUpgrade")
assert(Osi.HasPassive("loadedUpgrade", fortune) == 0 and Osi.HasPassive("loadedUpgrade", luck) == 1,
    "Recovery must not convert Luck while a respec is in progress")
Osi.RemovePassive("loadedUpgrade", luck)
fire("RespecCompleted", "after", "loadedUpgrade")
for _ = 1, 10 do events.Tick() end
assert(Osi.HasPassive("loadedUpgrade", fortune) == 0, "Recovery must never grant Fortune without Luck")
character("staleLuck")
players[#players + 1] = {"staleLuck"}
Osi.AddPassive("staleLuck", luck)
Osi.AddPassive("staleLuck", fortune)
events.SessionLoaded()
events.Tick()
assert(Osi.HasPassive("staleLuck", luck) == 0 and Osi.HasPassive("staleLuck", fortune) == 1,
    "Existing Fortune owners must lose leftover Luck even without an upgrade marker")
assert(not interrupts.staleLuck.Interrupt_GSL_DesperadosLuck and
    interrupts.staleLuck.Interrupt_GSL_DesperadosFortune, "Save-load cleanup must retain only the Fortune reaction")
Osi.AddPassive("staleLuck", luck)
for _ = 1, 10 do events.Tick() end
assert(Osi.HasPassive("staleLuck", luck) == 0 and not interrupts.staleLuck.Interrupt_GSL_DesperadosLuck,
    "Periodic recovery must remove reapplied Luck and its reaction")
character("protectedLuck")
character("nativeUpgrade")
players[#players + 1] = {"nativeUpgrade"}
entities.nativeUpgrade.LevelUp = {LevelUps = {
    {Upgrades = {Passives = {{Passives = {luck, "GSL_Desperado_AnteUpUnlock"}}}}}
}}
Osi.AddPassive("nativeUpgrade", upgrade)
fire("LeveledUp", "after", "nativeUpgrade")
assert(Osi.HasPassive("nativeUpgrade", fortune) == 1 and Osi.HasPassive("nativeUpgrade", luck) == 0,
    "Native progression removal must preserve the Fortune prerequisite through recorded selections")
assert(interrupts.nativeUpgrade.Interrupt_GSL_DesperadosFortune and
    not interrupts.nativeUpgrade.Interrupt_GSL_DesperadosLuck, "Native upgrade must only own the Fortune reaction")
character("nativeWithoutLuck")
players[#players + 1] = {"nativeWithoutLuck"}
entities.nativeWithoutLuck.LevelUp = {LevelUps = {
    {Upgrades = {Passives = {{Passives = {"GSL_Desperado_AnteUpUnlock"}}}}}
}}
Osi.AddPassive("nativeWithoutLuck", upgrade)
fire("LeveledUp", "after", "nativeWithoutLuck")
assert(Osi.HasPassive("nativeWithoutLuck", fortune) == 0, "Other grit choices must not satisfy the Fortune prerequisite")
players[#players + 1] = {"protectedLuck"}
protectedPassives.protectedLuck = {[luck] = true}
entities.protectedLuck.PassiveContainer = {Passives = {"luckSource", "fortuneSource"}}
entities.luckSource = {Passive = {PassiveId = luck}}
entities.fortuneSource = {Passive = {PassiveId = fortune}}
Osi.AddPassive("protectedLuck", luck)
Osi.AddPassive("protectedLuck", upgrade)
fire("LeveledUp", "after", "protectedLuck")
local beforeDiagnostic = #printed
ticks()
assert(#printed == beforeDiagnostic + 1, "A failed Luck removal must report one warning, without debug dumps")
assert(printed[beforeDiagnostic + 1]:find("WARNING: Luck remains owned", 1, true))
for _ = 1, 20 do events.Tick() end
assert(#printed == beforeDiagnostic + 1, "A failed Luck removal must not spam every tick")
assert(Osi.HasPassive("protectedLuck", fortune) == 1, "A cleanup failure must not revoke Fortune")
local allInPassive = "GSL_Desperado_AllInUnlock"
character("legacyAllIn")
players[#players + 1] = {"legacyAllIn"}
Osi.AddPassive("legacyAllIn", allInPassive)
local oldVariant = "UnlockSpellVariant(SpellId('Projectile_GSL_AllIn'),ModifyNumberOfTargets(AdditiveBase,6,false))"
allInBoosts.legacyAllIn = oldVariant
variables.Firearms.allInBoosts = {}
variables.Firearms.allInBoosts.legacyAllIn = oldVariant
events.SessionLoaded()
events.Tick()
assert(Osi.HasPassive("legacyAllIn", allInPassive) == 0, "Removed All In must be revoked from existing saves")
assert(not allInBoosts.legacyAllIn, "Old native variants must be removed from existing saves")
local oldContainer = "UnlockSpell(Shout_GSL_AllIn_9_Musket);IF(SpellId('Projectile_GSL_AllIn_9_Musket')):RollBonus(RangedWeaponAttack,-2)"
allInBoosts.legacyAllIn = oldContainer
variables.Firearms.allInBoosts.legacyAllIn = oldContainer
Osi.ApplyStatus("legacyAllIn", "GSL_ALL_IN_READY", -1)
events.Tick()
assert(not allInBoosts.legacyAllIn and Osi.HasActiveStatus("legacyAllIn", "GSL_ALL_IN_READY") == 0,
    "Old dynamic containers and ready markers must be removed from existing saves")
local unchanged = allInChanges
ticks()
assert(allInChanges == unchanged, "Retired ability cleanup must be idempotent")
local function previewCharacter(id, hasLuck, levelCount)
    character(id)
    players[#players + 1] = {id}
    entities[id].LevelUp = {LevelUps = {}}
    for _ = 1, levelCount do
        entities[id].LevelUp.LevelUps[#entities[id].LevelUp.LevelUps + 1] = {
            Class = "799af9fb-7ff1-4a4f-a9b3-041a16dbee0c",
            Upgrades = {Passives = {}}
        }
    end
    if hasLuck then Osi.AddPassive(id, luck) end
end
local function previewMessage(id, open)
    netListeners.GSL_FortunePreview("GSL_FortunePreview", {Character = id, Open = open})
    events.Tick()
end
for _, luckLevel in ipairs({5, 7, 9, 11, 13}) do
    local id = "previewLuckAt" .. luckLevel
    previewCharacter(id, true, 14)
    for level = 5, 13, 2 do
        entities[id].LevelUp.LevelUps[level].Upgrades.Passives[1] = {
            Class = "4a518934-644d-4120-ae6a-d922cf7cac34", Level = level, SelectorId = "GritAbility",
            Passives = {level == luckLevel and luck or "GSL_Desperado_AnteUpUnlock"}
        }
    end
    previewMessage(id, true)
    assert(Osi.HasPassive(id, fortune) == 1 and Osi.HasPassive(id, luck) == 1,
        "Luck picked at level " .. luckLevel .. " must receive temporary preview Fortune")
    previewMessage(id, false)
    ticks()
    assert(Osi.HasPassive(id, fortune) == 0 and Osi.HasPassive(id, luck) == 1,
        "Cancellation must preserve Luck picked at level " .. luckLevel)
    -- Exercise recorded-choice recovery after native level-15 removal, without a preview grant.
    Osi.RemovePassive(id, luck)
    Osi.AddPassive(id, upgrade)
    fire("LeveledUp", "after", id)
    assert(Osi.HasPassive(id, fortune) == 1 and Osi.HasPassive(id, luck) == 0 and
        interrupts[id].Interrupt_GSL_DesperadosFortune and not interrupts[id].Interrupt_GSL_DesperadosLuck,
        "Luck picked at level " .. luckLevel .. " must permanently evolve after native removal")
    assert(entities[id].LevelUp.LevelUps[luckLevel].Upgrades.Passives[1].Passives[1] == luck,
        "Upgrading must preserve the original Luck selection")
end
previewCharacter("previewCancel", true, 14)
previewMessage("previewCancel", true)
assert(Osi.HasPassive("previewCancel", fortune) == 1 and Osi.HasPassive("previewCancel", luck) == 1,
    "Preview must own Fortune before confirmation without retiring Luck early")
assert(variables.Firearms.fortunePreviews.previewCancel and not variables.Firearms.fortuneUpgrades.previewCancel)
ticks()
assert(Osi.HasPassive("previewCancel", luck) == 1, "Periodic upgrade checks must leave an unconfirmed build unchanged")
previewMessage("previewCancel", false)
ticks()
assert(Osi.HasPassive("previewCancel", fortune) == 0 and Osi.HasPassive("previewCancel", luck) == 1,
    "Cancelling must revoke temporary Fortune and preserve Luck")
assert(not interrupts.previewCancel.Interrupt_GSL_DesperadosFortune)
previewMessage("previewCancel", true)
events.SessionLoaded()
events.Tick()
assert(Osi.HasPassive("previewCancel", fortune) == 0, "Loading must clear saved unconfirmed grants")

previewCharacter("previewConfirm", true, 14)
previewMessage("previewConfirm", true)
Osi.AddPassive("previewConfirm", upgrade)
Osi.RemovePassive("previewConfirm", luck)
fire("LeveledUp", "after", "previewConfirm")
previewMessage("previewConfirm", false)
ticks()
assert(Osi.HasPassive("previewConfirm", fortune) == 1 and Osi.HasPassive("previewConfirm", luck) == 0,
    "Confirmation must retain Fortune and retire Luck")
assert(variables.Firearms.fortuneUpgrades.previewConfirm and not variables.Firearms.fortunePreviews.previewConfirm)

previewCharacter("previewWithoutLuck", false, 14)
previewMessage("previewWithoutLuck", true)
assert(Osi.HasPassive("previewWithoutLuck", fortune) == 0, "The server must reject preview ownership without Luck")
previewCharacter("previewTooEarly", true, 13)
previewMessage("previewTooEarly", true)
assert(Osi.HasPassive("previewTooEarly", fortune) == 0, "The server must reject preview ownership below class level 14")
previewCharacter("previewOwned", true, 14)
Osi.AddPassive("previewOwned", fortune)
previewMessage("previewOwned", true)
previewMessage("previewOwned", false)
ticks()
assert(Osi.HasPassive("previewOwned", fortune) == 1, "Cancellation must never revoke pre-existing Fortune")
previewCharacter("previewDisconnect", true, 14)
previewMessage("previewDisconnect", true)
for _ = 1, 601 do events.Tick() end
assert(Osi.HasPassive("previewDisconnect", fortune) == 0 and Osi.HasPassive("previewDisconnect", luck) == 1,
    "A lost client must not leave an unconfirmed Fortune grant behind")
previewCharacter("previewHeartbeat", true, 14)
previewMessage("previewHeartbeat", true)
for _ = 1, 450 do events.Tick() end
previewMessage("previewHeartbeat", true)
for _ = 1, 450 do events.Tick() end
assert(Osi.HasPassive("previewHeartbeat", fortune) == 1, "Renewal must keep Fortune owned while the chooser stays open")
fire("StartRespec", "before", "previewHeartbeat")
assert(Osi.HasPassive("previewHeartbeat", fortune) == 0, "Starting respec must clear any unrelated preview grant")
fire("RespecCancelled", "after", "previewHeartbeat")
Osi.ApplyStatus("alice", "GSL_HOT_STREAK_COUNTER", 12, 1, "alice")
variables.Firearms.hotStreaks = {alice = 3}
Osi.ApplyStatus("alice", "GSL_HOT_STREAK", -1, 1, "alice")
fire("StatusApplied", "after", "alice", "GSL_HOT_STREAK", "", 0)
assert(not listeners["KilledBy:after"], "Hot Streak recasts must not use a kill counter")
assert(hotStreakStacks.alice == nil, "Starting redesigned Hot Streak must clear the old counter")
assert(variables.Firearms.hotStreaks.alice == nil, "Starting redesigned Hot Streak must clear saved kill counts")
Osi.ApplyStatus("alice", "GSL_HOT_STREAK_ADVANCED", -1, 1, "alice")
fire("UsingSpell", "before", "alice", "Projectile_MainHandAttack", "", "", 201)
assert(Osi.HasActiveStatus("alice", "GSL_HOT_STREAK_ADVANCED") == 0,
    "Regular attacks must re-arm Hot Streak's once-per-attack advancement")
Osi.ApplyStatus("alice", "GSL_HOT_STREAK_COUNTER", 12, 1, "alice")
Osi.RemoveStatus("alice", "GSL_HOT_STREAK")
fire("StatusRemoved", "after", "alice", "GSL_HOT_STREAK", "", 0)
assert(hotStreakStacks.alice == nil, "Ending Hot Streak must clear any legacy counter")
print("Fortune preview ownership passed: eligibility, ownership before confirmation, cancellation, confirmation, load cleanup, existing ownership, lost client and renewal")
print("Removed All In cleanup passed: saved passive, native variant, dynamic container, ready marker and idempotence")
print("Grit runtime mocks passed: stats, ammo, dual wield, repair, breakage, transfer, reload state, rest, cancellation, counter, violent shot, double or nothing, roll the bones, cheat death's odds, reload costs, grit recovery, arcane reload, longarm range, double load break, refresh recovery, conditional Fortune upgrade, delayed progression, save-load recovery, respec and persistent Luck diagnostics")
