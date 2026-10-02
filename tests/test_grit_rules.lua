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
    assert(rules.Repair(state) and not state.misfire)
    rules.Misfire(state, true)
    assert(state.broken and not rules.Repair(state))
    rules.LongRest(state)
    assert(not state.broken and not state.misfire and state.mode == nil)
    assert(state.ammo == firearm.capacity)
end
for rarity, dc in pairs({[0] = 12, [1] = 12, [2] = 13, [3] = 14, [4] = 15, [5] = 16}) do
    assert(rules.RepairDC(rarity) == dc)
end
assert(not pcall(rules.RepairDC, 6), "Unsupported rarity must be explicit")
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
assert(first.mode == "Range" and not first.broken)
assert(second.mode == nil and second.broken)
print("Grit rule tests passed: tiers, rarity, independent guns, replacement, repair and long rest")
