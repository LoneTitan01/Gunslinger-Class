-- The client edits its own copy of the stats with the same firearm requirements as the server, without syncing.
local root = "GunslingerClass\\Mods\\GunslingerClass\\ScriptExtender\\Lua\\"
local spells = {
    Projectile_SneakAttack_Rakish = {RequirementConditions = "HasActionResource('SneakAttack_Charge',1,0,false,false,context.Source)",
        SpellType = "Projectile", SpellRoll = {Default = "Attack(AttackType.RangedWeaponAttack)"}, WeaponTypes = {"Ammunition"}},
    Projectile_ArrowOfFire = {RequirementConditions = "", SpellType = "Projectile",
        SpellRoll = {Default = "Attack(AttackType.RangedWeaponAttack)"}, WeaponTypes = {"Ammunition"}},
    Target_Bless = {RequirementConditions = "", SpellType = "Target", WeaponTypes = {}}
}
local interrupts = {}
for _, name in ipairs({"Interrupt_GSL_HairTrigger", "Interrupt_GSL_CloseCall", "Interrupt_GSL_QuickOnTheDraw",
    "Interrupt_GSL_DoubleOrNothing", "Interrupt_GSL_ReturnFire"}) do interrupts[name] = {Conditions = ""} end
local weapons = {WPN_GSL_Musket = {BoostsOnEquipMainHand = ""}}
local printed = {}
local handlers = {}
Ext = {
    Require = function(file)
        if file == "BootstrapClient.lua" then return dofile(root .. file) end
        if file == "FirearmStats.lua" or file == "GritRules.lua" then return dofile(root .. file) end
        if file == "FortuneChooserOwned.lua" then return function() end end
        return nil
    end,
    Events = setmetatable({}, {__index = function(events, name)
        local event = {Subscribe = function(_, handler) handlers[name] = handler end}
        rawset(events, name, event)
        return event
    end}),
    Stats = {
        GetStats = function(kind)
            local names = {}
            for name in pairs(kind == "Weapon" and weapons or kind == "SpellData" and spells or {}) do names[#names + 1] = name end
            return names
        end,
        Get = function(name) return spells[name] or interrupts[name] or weapons[name] end,
        Sync = function() error("A client must not sync stats") end
    },
    Utils = {Print = function(message) printed[#printed + 1] = message end}
}
local Stats = dofile(root .. "FirearmStats.lua")
local changed, failed = Stats.Apply("client")
assert(failed == 0 and changed == 2 + 5 + 1, "The Rakish shot, the arrow, the interrupts and the gun are edited")
local rakish = spells.Projectile_SneakAttack_Rakish.RequirementConditions
assert(rakish:find("GunslingerFirearmReady(false)", 1, true), "The client copy needs a loaded gun too")
assert(not spells.Projectile_ArrowOfFire.RequirementConditions:find("HasActionResource", 1, true) and
    not spells.Projectile_ArrowOfFire.RequirementConditions:find("GunslingerFirearmReady", 1, true) and
    spells.Projectile_ArrowOfFire.RequirementConditions:find("GunslingerFirearmWorking(false)", 1, true),
    "Arrows only need a working gun")
assert(spells.Target_Bless.RequirementConditions == "", "Spells that do not need a ranged weapon are unchanged")
assert(printed[1] == "[Gunslinger] Firearm requirements added to 8 stats (client).")
Stats.Apply("client")
assert(spells.Projectile_SneakAttack_Rakish.RequirementConditions == rakish, "Applying twice adds nothing")
print("Client firearm stats passed: requirements, arrows, unchanged spells, no sync and idempotence")
