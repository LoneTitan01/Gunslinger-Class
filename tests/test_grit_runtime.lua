local root = "GunslingerClass\\Mods\\GunslingerClass\\ScriptExtender\\Lua\\"
local rules = dofile(root .. "GritRules.lua")
local listeners, events, entities, inventory, statuses = {}, {}, {}, {}, {}
local variables, passives, rolls, durations = {}, {}, {}, {}
local spellStats = {
    GSL_MainHand_Flintlock_attack = {RequirementConditions = "Character()", SpellProperties = "", SpellRoll = ""},
    GSL_OffHand_Flintlock_attack = {RequirementConditions = "", SpellProperties = "", SpellRoll = ""},
    Projectile_GSL_Bloodletting_Flintlock = {RequirementConditions = "", SpellProperties = "",
        SpellRoll = "Attack(AttackType.RangedWeaponAttack)",
        UseCosts = "ActionPoint:1;GunslingerFlintlockAmmo:1"},
    Zone_GSL_LineEmUp = {RequirementConditions = "Character()", SpellProperties = "OriginalEffect", SpellRoll = ""},
    Projectile_GSL_InfusedRounds = {RequirementConditions = "Character()", SpellProperties = "ForceEffect", SpellRoll = ""},
    Zone_GSL_PiercingRound = {RequirementConditions = "Character()", SpellProperties = "", SpellRoll = ""},
    Shout_GSL_HailOfLead = {RequirementConditions = "Character()", SpellProperties = "", SpellRoll = ""},
    Projectile_GSL_DoubleOrNothing_Flintlock = {RequirementConditions = "", SpellProperties = "", SpellRoll = "",
        UseCosts = "ActionPoint:1;GunslingerGrit:2;GunslingerFlintlockAmmo:1"},
    Projectile_PiercingShot = {RequirementConditions = "OriginalRequirement", SpellProperties = "OriginalPiercingEffect",
        SpellRoll = "Attack(AttackType.RangedWeaponAttack)"}
}
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
    Stats = {
        GetStats = function()
            local names = {}
            for name in pairs(spellStats) do names[#names + 1] = name end
            return names
        end,
        Get = function(name) return spellStats[name] end,
        Sync = function() end
    },
    Osiris = {RegisterListener = function(name, _, phase, callback) listeners[name .. ":" .. phase] = callback end},
    Utils = {Print = function() end}
}
for _, name in ipairs({"StatsLoaded", "SessionLoaded", "Tick"}) do
    Ext.Events[name] = {Subscribe = function(_, callback) events[name] = callback end}
end
local function ammo(char, hand)
    local id = hand == "Off" and rules.OffhandResource or rules.Firearms.Flintlock.resource
    return entities[char].ActionResources.Resources[id][1]
end
Osi = {
    GetEquippedItem = function(char, slot) return inventory[char] and inventory[char][slot] end,
    GetEquippedWeapon = function(char) return inventory[char]["Ranged Main Weapon"] end,
    GetTemplate = function(item) return entities[item].template end,
    HasActiveStatus = function(id, status) return statuses[id] and statuses[id][status] and 1 or 0 end,
    ApplyStatus = function(id, status, duration)
        durations[status] = duration
        statuses[id] = statuses[id] or {}
        statuses[id][status] = true
    end,
    RemoveStatus = function(id, status) if statuses[id] then statuses[id][status] = nil end end,
    AddBoosts = function(char, boost)
        local hand = boost:find("Offhand", 1, true) and "Off" or "Main"
        local entry = ammo(char, hand)
        entry.MaxAmount = entry.MaxAmount + 2
        entry.Amount = entry.Amount + 2
    end,
    RemoveBoosts = function(char, boost)
        local hand = boost:find("Offhand", 1, true) and "Off" or "Main"
        local entry = ammo(char, hand)
        entry.MaxAmount = entry.MaxAmount - 2
        entry.Amount = math.min(entry.Amount, entry.MaxAmount)
    end,
    IsDead = function() return 0 end,
    HasPassive = function(char, passive) return passives[char] and passives[char][passive] and 1 or 0 end,
    UseSpell = function(char, spell, target)
        assert(char == "alice" and spell == "Projectile_GSL_ReactionShot" and target == "bob")
    end
}
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
gun("first")
entities.first.template = "a710ad68-179b-4b0e-8ef2-3b37609a3f12"
gun("second")
inventory.alice["Ranged Main Weapon"] = "first"
inventory.alice["Ranged Offhand Weapon"] = "second"
dofile(root .. "BootstrapServer.lua")
events.StatsLoaded()
events.StatsLoaded()
assert(spellStats.GSL_MainHand_Flintlock_attack.RequirementConditions:find("GSL_FIREARM_MAIN_DISABLED", 1, true))
assert(spellStats.GSL_OffHand_Flintlock_attack.RequirementConditions:find("GSL_FIREARM_OFF_DISABLED", 1, true))
assert(spellStats.Projectile_GSL_Bloodletting_Flintlock.RequirementConditions:find("GSL_FIREARM_MAIN_DISABLED", 1, true))
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
assert(ammo("alice", "Main").MaxAmount == 5 and ammo("alice", "Main").Amount == 3)
assert(ammo("alice", "Off").MaxAmount == 3, "Primary capacity must not modify the other gun")
fire("UsingSpell", "before", "alice", "Shout_GSL_Reload_Flintlock", "", "", 11)
ammo("alice", "Main").Amount = 5
fire("CastedSpell", "after", "alice", "Shout_GSL_Reload_Flintlock", "", "", 11)
assert(variables.Firearms.weapons.first.ammo == 5, "Reload must snapshot upgraded capacity")
cast("Shout_GSL_Tinkerer_MainRange", 2)
assert(ammo("alice", "Main").MaxAmount == 3)
assert(entities.first.Weapon.WeaponRange == 19.5 and entities.second.Weapon.WeaponRange == 13.5)
cast("Shout_GSL_Tinkerer_OffDamage", 3)
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_DAMAGE_FLINTLOCK") == 1)
assert(Osi.HasActiveStatus("first", "GSL_TINKERER_DAMAGE_FLINTLOCK") == 0)
cast("Shout_GSL_Tinkerer_OffRange", 31)
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_DAMAGE_FLINTLOCK") == 0, "Below level 10 a new mod replaces the old one")
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_OFF_RANGE") == 1)
passives.alice = {GSL_MasterTinkerer = true}
cast("Shout_GSL_Tinkerer_OffDamage", 32)
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_DAMAGE_FLINTLOCK") == 1, "Master Tinkerer keeps two mods")
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_OFF_RANGE") == 1)
fire("UsingSpell", "before", "alice", "GSL_OffHand_Flintlock_attack", "", "", 4)
ammo("alice", "Off").Amount = 2
fire("StatusApplied", "after", "alice", "GSL_MISFIRE", "alice", 4)
assert(variables.Firearms.weapons.second.misfire and not variables.Firearms.weapons.first.misfire)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_DISABLED") == 0, "A misfire must not stop the gun firing")
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_MISFIRED") == 1)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_MAIN_MISFIRED") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_OFF_12") == 1)
fire("UsingSpell", "before", "alice", "Shout_GSL_FieldRepair_Off10", "", "", 45)
fire("CastedSpell", "after", "alice", "Shout_GSL_FieldRepair_Off10", "", "", 45)
assert(variables.Firearms.weapons.second.misfire, "A failed field repair must leave the firearm misfired")
fire("CastedSpell", "after", "alice", "GSL_OffHand_Flintlock_attack", "", "", 4)
fire("UsingSpell", "before", "alice", "Shout_GSL_RapidRepair_Off12", "", "", 5)
fire("StatusApplied", "after", "alice", "GSL_REPAIR_OFF_DONE", "alice", 5)
fire("CastedSpell", "after", "alice", "Shout_GSL_RapidRepair_Off12", "", "", 5)
assert(not variables.Firearms.weapons.second.misfire)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_MISFIRED") == 0)
fire("UsingSpell", "before", "alice", "GSL_MainHand_Flintlock_attack", "", "", 43)
fire("StatusApplied", "after", "alice", "GSL_MISFIRE", "alice", 43)
assert(Osi.HasActiveStatus("alice", "GSL_FIELD_REPAIR_MAIN_10") == 1)
fire("CastedSpell", "after", "alice", "GSL_MainHand_Flintlock_attack", "", "", 43)
fire("UsingSpell", "before", "alice", "Shout_GSL_FieldRepair_Main10", "", "", 44)
fire("StatusApplied", "after", "alice", "GSL_FIELD_REPAIR_MAIN_DONE", "alice", 44)
fire("CastedSpell", "after", "alice", "Shout_GSL_FieldRepair_Main10", "", "", 44)
assert(not variables.Firearms.weapons.first.misfire)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_MAIN_MISFIRED") == 0)
for action = 41, 42 do
    fire("UsingSpell", "before", "alice", "GSL_OffHand_Flintlock_attack", "", "", action)
    fire("StatusApplied", "after", "alice", "GSL_MISFIRE", "alice", action)
    fire("CastedSpell", "after", "alice", "GSL_OffHand_Flintlock_attack", "", "", action)
end
assert(variables.Firearms.weapons.second.broken, "Misfiring a misfired gun must break it")
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_DISABLED") == 1)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_MISFIRED") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_OFF_12") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_FIELD_REPAIR_OFF_10") == 0)
fire("UsingSpell", "before", "alice", "Projectile_GSL_DoubleLoad_Flintlock", "", "", 6)
fire("StatusApplied", "after", "alice", "GSL_DOUBLE_LOAD_BROKEN", "alice", 6)
fire("CastedSpell", "after", "alice", "Projectile_GSL_DoubleLoad_Flintlock", "", "", 6)
assert(variables.Firearms.weapons.first.broken)
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MAIN_12") == 0)
fire("Unequipped", "before", "first", "alice")
inventory.alice["Ranged Main Weapon"] = nil
fire("Unequipped", "after", "first", "alice")
inventory.bob["Ranged Main Weapon"] = "first"
fire("Equipped", "after", "first", "bob")
ticks()
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_MAIN_DISABLED") == 0)
assert(Osi.HasActiveStatus("bob", "GSL_FIREARM_MAIN_DISABLED") == 1, "Broken state must follow the physical gun")
assert(entities.first.Weapon.WeaponRange == 19.5)
entities.first.Weapon.WeaponRange = 13.5
events.SessionLoaded()
assert(entities.first.Weapon.WeaponRange == 19.5, "Saved modification must be reapplied")
fire("LongRestFinished", "after")
assert(not variables.Firearms.weapons.first.broken and not variables.Firearms.weapons.second.broken)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_DISABLED") == 0)
assert(entities.first.Weapon.WeaponRange == 13.5)
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_DAMAGE_FLINTLOCK") == 0)
assert(ammo("bob", "Main").Amount == 3 and ammo("alice", "Off").Amount == 3)
fire("Unequipped", "before", "first", "bob")
inventory.bob["Ranged Main Weapon"] = nil
fire("Unequipped", "after", "first", "bob")
inventory.alice["Ranged Main Weapon"] = "first"
fire("Equipped", "after", "first", "alice")
ticks()
fire("UsingSpell", "before", "alice", "Projectile_GSL_FanningFire_Flintlock_2", "", "", 7)
assert(Osi.HasActiveStatus("alice", "GSL_FANNING_FIRE_2") == 1)
fire("CastSpellFailed", "after", "alice", "Projectile_GSL_FanningFire_Flintlock_2", "", "", 7)
assert(Osi.HasActiveStatus("alice", "GSL_FANNING_FIRE_2") == 0)
assert(variables.Firearms.weapons.first.ammo == ammo("alice", "Main").Amount)
Osi.ApplyStatus("alice", "GSL_LASTWORD_PENDING")
fire("StatusApplied", "after", "alice", "GSL_LASTWORD_PENDING", "alice", 8)
fire("AttackedBy", "after", "alice", "bob", "bob", "Piercing", 10, "Attack", 9)
assert(Osi.HasActiveStatus("alice", "GSL_LASTWORD_PENDING") == 1, "Unrelated damage must not consume the counter")
fire("AttackedBy", "after", "alice", "bob", "bob", "Piercing", 10, "Attack", 8)
assert(Osi.HasActiveStatus("alice", "GSL_LASTWORD_PENDING") == 0)
for _, name in ipairs({"Zone_GSL_PiercingRound", "Shout_GSL_HailOfLead"}) do
    local _, count = spellStats[name].SpellProperties:gsub("UseActionResource", "")
    assert(count == 3, name .. " must spend main-hand ammunition")
    assert(spellStats[name].RequirementConditions:find("GSL_FIREARM_MAIN_DISABLED", 1, true))
end
local function shot(spell, action, ...)
    for _, roll in ipairs({...}) do rolls[#rolls + 1] = roll end
    cast(spell, action)
    assert(#rolls == 0, spell .. " consumed the wrong number of rolls")
end
shot("Projectile_GSL_ViolentShot_Flintlock_2", 50, 3)
assert(not variables.Firearms.weapons.first.misfire, "Violent Shot misfires only on d20 <= grit")
shot("Projectile_GSL_ViolentShot_Flintlock_2", 51, 2)
assert(variables.Firearms.weapons.first.misfire and Osi.HasActiveStatus("alice", "GSL_FIREARM_MAIN_MISFIRED") == 1)
fire("LongRestFinished", "after")
rolls[1] = 11
fire("UsingSpell", "before", "alice", "Projectile_GSL_DoubleOrNothing_Flintlock", "", "", 52)
assert(Osi.HasActiveStatus("alice", "GSL_DOUBLE_OR_NOTHING_WIN") == 1, "A win doubles the shot")
fire("CastedSpell", "after", "alice", "Projectile_GSL_DoubleOrNothing_Flintlock", "", "", 52)
assert(Osi.HasActiveStatus("alice", "GSL_DOUBLE_OR_NOTHING_WIN") == 0 and not variables.Firearms.weapons.first.misfire)
shot("Projectile_GSL_DoubleOrNothing_Flintlock", 53, 10)
assert(variables.Firearms.weapons.first.misfire, "A losing Double or Nothing misfires")
assert(Osi.HasActiveStatus("alice", "GSL_CHEAT_DEATHS_ODDS_REFUND") == 0)
fire("LongRestFinished", "after")
fire("UsingSpell", "before", "alice", "Projectile_GSL_AllIn_Flintlock_4", "", "", 54)
assert(Osi.HasActiveStatus("alice", "GSL_ALL_IN") == 1)
fire("CastSpellFailed", "after", "alice", "Projectile_GSL_AllIn_Flintlock_4", "", "", 54)
assert(Osi.HasActiveStatus("alice", "GSL_ALL_IN") == 0)
shot("Shout_GSL_RollTheBones", 55, 1)
assert(Osi.HasActiveStatus("alice", "GSL_RTB_BUST") == 1 and durations.GSL_RTB_BUST == 12)
shot("Shout_GSL_RollTheBones", 56, 6)
assert(Osi.HasActiveStatus("alice", "GSL_RTB_BUST") == 0 and Osi.HasActiveStatus("alice", "GSL_RTB_JACKPOT") == 1)
passives.alice.GSL_Desperado_CheatDeathsOdds = true
entities.alice.Health.Hp = 14
shot("Shout_GSL_RollTheBones", 57, 3)
assert(Osi.HasActiveStatus("alice", "GSL_CHEAT_DEATHS_ODDS_REFUND") == 0, "One-grit abilities never refund")
shot("Projectile_GSL_DoubleOrNothing_Flintlock", 58, 11)
assert(Osi.HasActiveStatus("alice", "GSL_CHEAT_DEATHS_ODDS_REFUND") == 1, "Bloodied 2-grit abilities refund 1 grit")
assert(durations.GSL_CHEAT_DEATHS_ODDS_REFUND == 0)print("Grit runtime mocks passed: stats, ammo, dual wield, repair, breakage, transfer, reload state, rest, cancellation, counter, violent shot, double or nothing, all in, roll the bones, cheat death's odds")
