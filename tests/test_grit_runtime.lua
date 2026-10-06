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
    Zone_GSL_PiercingRound = {RequirementConditions = "Character()", SpellProperties = "", SpellRoll = ""},
    Shout_GSL_HailOfLead = {RequirementConditions = "Character()", SpellProperties = "", SpellRoll = ""},
    Projectile_GSL_DoubleOrNothing = {RequirementConditions = "", SpellProperties = "", SpellRoll = "", UseCosts = ""},
    Projectile_GSL_DazingShot = {RequirementConditions = "", SpellProperties = "", SpellRoll = "",
        UseCosts = "ActionPoint:1;GunslingerGrit:2"},
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
    GetEquippedWeapon = function() return "melee" end,
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
assert(Osi.HasActiveStatus("first", "GSL_TINKERER_CAPACITY") == 1, "Capacity must show on the modified gun")
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_CAPACITY") == 0)
fire("UsingSpell", "before", "alice", "Shout_GSL_Reload_Flintlock", "", "", 11)
ammo("alice", "Main").Amount = 5
fire("CastedSpell", "after", "alice", "Shout_GSL_Reload_Flintlock", "", "", 11)
assert(variables.Firearms.weapons.first.ammo == 5, "Reload must snapshot upgraded capacity")
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
fire("UsingSpell", "before", "alice", "GSL_OffHand_Flintlock_attack", "", "", 4)
ammo("alice", "Off").Amount = 2
fire("StatusApplied", "after", "alice", "GSL_MISFIRE", "alice", 4)
assert(variables.Firearms.weapons.second.misfire and not variables.Firearms.weapons.first.misfire)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_DISABLED") == 0, "A misfire must not stop the gun firing")
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_MISFIRED") == 1)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_MAIN_MISFIRED") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_OFF") == 1, "A misfired gun gets its own Repair menu")
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_OFF_RAPID") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_MAIN") == 0, "Only the misfired hand shows a Repair menu")
fire("UsingSpell", "before", "alice", "Shout_GSL_FieldRepair_Off", "", "", 45)
fire("CastedSpell", "after", "alice", "Shout_GSL_FieldRepair_Off", "", "", 45)
assert(variables.Firearms.weapons.second.misfire, "A failed field repair must leave the firearm misfired")
fire("CastedSpell", "after", "alice", "GSL_OffHand_Flintlock_attack", "", "", 4)
passives.alice.GSL_RapidRepairUnlock = true
fire("UsingSpell", "before", "alice", "Shout_GSL_RapidRepair_Off", "", "", 5)
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_OFF_RAPID") == 1, "Rapid Repair joins the hand's Repair menu")
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_OFF") == 0)
fire("StatusApplied", "after", "alice", "GSL_REPAIR_OFF_DONE", "alice", 5)
fire("CastedSpell", "after", "alice", "Shout_GSL_RapidRepair_Off", "", "", 5)
assert(not variables.Firearms.weapons.second.misfire)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_MISFIRED") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_OFF_RAPID") == 0, "Repairing removes the Repair menu")
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
end
assert(variables.Firearms.weapons.second.broken, "Misfiring a misfired gun must break it")
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_DISABLED") == 1)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_MISFIRED") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_FIREARM_OFF_DESTROYED") == 1, "Breaking must replace Misfired with the visible Broken condition")
assert(Osi.HasActiveStatus("second", "GSL_FIREARM_ITEM_DESTROYED") == 1 and Osi.HasActiveStatus("second", "GSL_FIREARM_ITEM_MISFIRED") == 0)
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_OFF_RAPID") == 0, "A broken gun cannot be repaired")
assert(Osi.HasActiveStatus("alice", "GSL_REPAIR_MENU_OFF") == 0)
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
assert(Osi.HasActiveStatus("bob", "GSL_TINKERER_MAIN_RANGE_FLINTLOCK") == 1, "Range must follow the physical gun")
assert(Osi.HasActiveStatus("alice", "GSL_TINKERER_MAIN_RANGE_FLINTLOCK") == 0)
statuses.first.GSL_TINKERER_RANGE_FLINTLOCK = nil
variables.Firearms.weapons.second.baseRange = 13.5
entities.second.Weapon.WeaponRange = 19.5
events.SessionLoaded()
assert(Osi.HasActiveStatus("first", "GSL_TINKERER_RANGE_FLINTLOCK") == 1, "Saved modification must be reapplied")
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
assert(Osi.HasActiveStatus("second", "GSL_TINKERER_RANGE_FLINTLOCK") == 0)
assert(ammo("bob", "Main").Amount == 3 and ammo("alice", "Off").Amount == 3)
fire("Unequipped", "before", "first", "bob")
inventory.bob["Ranged Main Weapon"] = nil
fire("Unequipped", "after", "first", "bob")
inventory.alice["Ranged Main Weapon"] = "first"
fire("Equipped", "after", "first", "alice")
ticks()
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
ticks()
Osi.ApplyStatus("alice", "GSL_LASTWORD_PENDING")
fire("StatusApplied", "after", "alice", "GSL_LASTWORD_PENDING", "alice", 12)
assert(lastWordShots == 2, "Stale attackers from earlier ticks are ignored")
Osi.RemoveStatus("alice", "GSL_LASTWORD_PENDING")
Osi.UseSpell = useSpell
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
shot("Projectile_GSL_ViolentShot_2", 50, 3)
assert(not variables.Firearms.weapons.first.misfire, "Violent Shot misfires only on d20 <= grit")
shot("Projectile_GSL_ViolentShot_2", 51, 2)
assert(variables.Firearms.weapons.first.misfire and Osi.HasActiveStatus("alice", "GSL_FIREARM_MAIN_MISFIRED") == 1)
fire("LongRestFinished", "after")
rolls[1] = 11
fire("UsingSpell", "before", "alice", "Projectile_GSL_DoubleOrNothing", "", "", 52)
assert(Osi.HasActiveStatus("alice", "GSL_DOUBLE_OR_NOTHING_WIN") == 1, "A win doubles the shot")
fire("CastedSpell", "after", "alice", "Projectile_GSL_DoubleOrNothing", "", "", 52)
assert(Osi.HasActiveStatus("alice", "GSL_DOUBLE_OR_NOTHING_WIN") == 0 and not variables.Firearms.weapons.first.misfire)
shot("Projectile_GSL_DoubleOrNothing", 53, 10)
assert(variables.Firearms.weapons.first.misfire, "A losing Double or Nothing misfires")
assert(Osi.HasActiveStatus("alice", "GSL_CHEAT_DEATHS_ODDS_REFUND") == 0)
fire("LongRestFinished", "after")
fire("UsingSpell", "before", "alice", "Projectile_GSL_AllIn_4", "", "", 54)
assert(Osi.HasActiveStatus("alice", "GSL_ALL_IN") == 1)
fire("CastSpellFailed", "after", "alice", "Projectile_GSL_AllIn_4", "", "", 54)
assert(Osi.HasActiveStatus("alice", "GSL_ALL_IN") == 0)
ammo("alice", "Main").Amount = 3
fire("UsingSpell", "before", "alice", "Projectile_GSL_AllIn_4", "", "", 60)
fire("CastedSpell", "after", "alice", "Projectile_GSL_AllIn_4", "", "", 60)
assert(ammo("alice", "Main").Amount == 2, "All In spends exactly one bullet per cast")
fire("UsingSpell", "before", "alice", "Projectile_GSL_AllIn_10", "", "", 600)
fire("CastedSpell", "after", "alice", "Projectile_GSL_AllIn_10", "", "", 600)
assert(ammo("alice", "Main").Amount == 1, "The 10-grit All In variant also spends one bullet")
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
assert(Osi.HasActiveStatus("carol", "GSL_FIREARM_MAIN_DESTROYED") == 1, "Double Load must show the Broken condition")
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
print("Grit runtime mocks passed: stats, ammo, dual wield, repair, breakage, transfer, reload state, rest, cancellation, counter, violent shot, double or nothing, all in, roll the bones, cheat death's odds, reload costs, grit recovery, arcane reload, longarm range, double load break, refresh recovery")
