local rules = dofile("GunslingerClass\\Mods\\GunslingerClass\\ScriptExtender\\Lua\\GritRules.lua")

for kind, firearm in pairs(rules.Firearms) do
    local state = {kind = kind, ammo = firearm.capacity}
    rules.Modify(state, "Capacity")
    assert(rules.Capacity(state) == firearm.capacity + 2)
    assert(state.ammo == firearm.capacity, "A capacity upgrade must not create ammunition")
    state.ammo = rules.Capacity(state)
    rules.Modify(state, "Damage")
    assert(rules.Capacity(state) == firearm.capacity)
    assert(state.ammo == firearm.capacity, "Replacing capacity must clamp ammunition")
    rules.Misfire(state, false)
    assert(state.misfire and not state.broken)
    assert(rules.Repair(state) and not state.misfire)
    rules.Misfire(state, false)
    rules.Misfire(state, false)
    assert(state.broken, "A second misfire before repair must break the gun")
    rules.LongRest(state)
    rules.Misfire(state, true)
    assert(state.broken and not rules.Repair(state))
    rules.LongRest(state)
    assert(not state.broken and not state.misfire and #rules.Mods(state) == 0)
    assert(state.ammo == firearm.capacity)
end
for _, hand in ipairs({"Main", "Off"}) do
    for _, mode in ipairs({"Capacity", "Damage", "Range"}) do
        local parsedHand, parsedMode = rules.ParseTinkerer("Shout_GSL_Tinkerer_" .. hand .. mode)
        assert(parsedHand == hand and parsedMode == mode)
    end
end
assert(rules.ParseTinkerer("Shout_GSL_Tinkerer") == nil)
assert(rules.ParseTinkerer("Shout_GSL_Tinkerer_BadCapacity") == nil)
local first = {kind = "Flintlock", ammo = 2}
local second = {kind = "Flintlock", ammo = 1}
rules.Modify(first, "Range")
rules.Misfire(second, true)
assert(rules.HasMod(first, "Range") and not first.broken)
assert(not rules.HasMod(second, "Range") and second.broken)
local master = {kind = "Musket", ammo = 1}
rules.Modify(master, "Capacity", 2)
rules.Modify(master, "Capacity", 2)
assert(#master.mods == 1, "Repeating a modification must not fill both slots")
rules.Modify(master, "Damage", 2)
assert(rules.HasMod(master, "Capacity") and rules.HasMod(master, "Damage"))
assert(rules.Capacity(master) == 3)
rules.Modify(master, "Range", 2)
assert(not rules.HasMod(master, "Capacity") and rules.HasMod(master, "Damage") and rules.HasMod(master, "Range"))
assert(master.ammo == 1 and rules.Capacity(master) == 1)
local legacy = {kind = "Flintlock", ammo = 3, mode = "Damage"}
rules.Modify(legacy, "Range", 2)
assert(legacy.mode == nil and rules.HasMod(legacy, "Damage") and rules.HasMod(legacy, "Range"))
assert(not pcall(rules.Modify, {kind = "Flintlock", ammo = 0}, "Range", 3))
assert(rules.ViolentMisfire(2, 2) and not rules.ViolentMisfire(2, 3) and rules.ViolentMisfire(3, 1))
assert(rules.RollTheBones(1) == "BUST" and rules.RollTheBones(2) == "HIT" and rules.RollTheBones(5) == "HIT")
assert(rules.RollTheBones(6) == "JACKPOT")
assert(rules.GritCost("ActionPoint:1;GunslingerGrit:3;GunslingerFlintlockAmmo:1") == 3)
assert(rules.GritCost("BonusActionPoint:1") == 0 and rules.GritCost(nil) == 0)
assert(rules.CheatDeathRefund(2, 0.49) and not rules.CheatDeathRefund(1, 0.1) and not rules.CheatDeathRefund(3, 0.5))
assert(rules.DoubleOrNothing(11) and rules.DoubleOrNothing(20) and not rules.DoubleOrNothing(10))
print("Grit rule tests passed: tiers, rarity, independent guns, replacement, two-mod limit, repair, long rest and gamble rolls")
