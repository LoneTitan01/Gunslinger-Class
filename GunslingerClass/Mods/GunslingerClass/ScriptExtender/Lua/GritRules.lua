local Rules = {}

Rules.ModuleUUID = "27bc37d3-66c2-436d-8d69-f7407a1e676e"
Rules.Firearms = {
    Flintlock = {capacity = 3, dice = "2d4", rangeBonus = 6,
        resource = "c4aa9fee-c3c7-4730-bb2b-6f5b4617967e"},
    Blunderbuss = {capacity = 2, dice = "1d12", rangeBonus = 3,
        resource = "7ca831c6-8a2b-4d1e-a9dd-f46fabb4f391"},
    Musket = {capacity = 1, dice = "2d6", rangeBonus = 12,
        resource = "6c4658a0-74d6-4bec-851f-d91ee914484d"}
}
Rules.OffhandResource = "6ba4dcd7-6927-4e6d-a79f-7f997840c51c"

function Rules.ParseTinkerer(spell)
    local hand, mode = spell:match("^Shout_GSL_Tinkerer_(%a+)(Capacity)$")
    if not hand then hand, mode = spell:match("^Shout_GSL_Tinkerer_(%a+)(Damage)$") end
    if not hand then hand, mode = spell:match("^Shout_GSL_Tinkerer_(%a+)(Range)$") end
    if not hand then hand, mode = spell:match("^Shout_GSL_Tinkerer_(%a+)(Remove)$") end
    if hand ~= "Main" and hand ~= "Off" then return nil end
    return hand, mode
end

function Rules.Mods(state)
    if state.mode then
        state.mods = {state.mode}
        state.mode = nil
    end
    state.mods = state.mods or {}
    return state.mods
end

function Rules.HasMod(state, mode)
    return Rules.ModCount(state, mode) > 0
end

function Rules.ModCount(state, mode)
    local count = 0
    for _, current in ipairs(Rules.Mods(state)) do
        if current == mode then count = count + 1 end
    end
    return count
end

function Rules.Capacity(state)
    local firearm = assert(Rules.Firearms[state.kind], "Unknown firearm kind")
    return firearm.capacity * (1 + Rules.ModCount(state, "Capacity"))
end

function Rules.DamageDice(state)
    local upgrades = Rules.ModCount(state, "Damage")
    if upgrades == 0 then return nil end
    if state.kind == "Flintlock" then return (2 + upgrades) .. "d4" end
    if state.kind == "Blunderbuss" then return "1d12+" .. upgrades .. "d4" end
    if state.kind == "Musket" then return "2d6+" .. upgrades .. "d4" end
    error("Unknown firearm kind: " .. tostring(state.kind))
end

function Rules.RangeBonus(state)
    local firearm = assert(Rules.Firearms[state.kind], "Unknown firearm kind")
    return firearm.rangeBonus * Rules.ModCount(state, "Range")
end

function Rules.Modify(state, mode, limit)
    assert(mode == "Capacity" or mode == "Damage" or mode == "Range", "Invalid modification")
    assert(not state.broken, "A destroyed firearm requires a long rest")
    limit = limit or 1
    assert(limit == 1 or limit == 2, "Invalid modification limit")
    local mods = Rules.Mods(state)
    mods[#mods + 1] = mode
    while #mods > limit do table.remove(mods, 1) end
    state.ammo = math.min(state.ammo or 0, Rules.Capacity(state))
end

function Rules.RemoveModifications(state)
    state.mode = nil
    state.mods = {}
    state.ammo = math.min(state.ammo or 0, Rules.Capacity(state))
end

function Rules.Misfire(state, doubleLoad)
    state.broken = state.broken or doubleLoad or state.misfire == true
    state.misfire = true
end

function Rules.Repair(state)
    if state.broken then return false end
    state.misfire = false
    return true
end

function Rules.ViolentMisfire(tier, roll)
    return roll <= tier
end

function Rules.RollTheBones(roll)
    if roll <= 1 then return "BUST" end
    if roll >= 6 then return "JACKPOT" end
    return "HIT"
end

function Rules.GritCost(useCosts)
    return tonumber((useCosts or ""):match("GunslingerGrit:(%d+)")) or 0
end

function Rules.CheatDeathRefund(cost, healthFraction)
    return cost >= 2 and healthFraction < 0.5
end

function Rules.DoubleOrNothing(roll)
    return roll >= 11
end

function Rules.LongRest(state)
    state.misfire = false
    state.broken = false
    state.ammo = Rules.Capacity(state)
end

return Rules
