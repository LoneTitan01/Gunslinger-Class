local Rules = {}

Rules.ModuleUUID = "27bc37d3-66c2-436d-8d69-f7407a1e676e"
Rules.Firearms = {
    Flintlock = {capacity = 3, dice = "2d4", rangeBonus = 6,
        resource = "c4aa9fee-c3c7-4730-bb2b-6f5b4617967e", shotSound = "Projectiles_Grn_Impact_Bomb"},
    Blunderbuss = {capacity = 2, dice = "1d12", rangeBonus = 3,
        resource = "7ca831c6-8a2b-4d1e-a9dd-f46fabb4f391", shotSound = "Gale_Explosion_Boom"},
    Musket = {capacity = 1, dice = "1d10", rangeBonus = 12,
        resource = "6c4658a0-74d6-4bec-851f-d91ee914484d", shotSound = "Projectiles_Grn_Impact_Bomb"}
}

-- A firing spell's CastSound is the gunshot of the gun it fires; shared grit shots need the equipped gun's.
function Rules.ShotSound(current, kind)
    local firearm = kind and Rules.Firearms[kind]
    if not firearm then return nil end
    for _, gun in pairs(Rules.Firearms) do
        if gun.shotSound == current then
            return firearm.shotSound ~= current and firearm.shotSound or nil
        end
    end
    return nil
end
Rules.OffhandResource = "6ba4dcd7-6927-4e6d-a79f-7f997840c51c"
-- Craft spells apply these markers; the server creates ordinary items, since summoned ones vanish
-- when their summoner dies or respecs.
Rules.CraftTemplates = {
    GSL_CRAFT_FLINTLOCK = "3d8b177d-89db-4826-8068-9f2d777faf04",
    GSL_CRAFT_BLUNDERBUSS = "4a7854fd-718a-4a4e-b9db-3875b5788065",
    GSL_CRAFT_MUSKET = "1da91e88-3f0e-4ccc-ac25-0bdf00426880",
    GSL_CRAFT_ASSEMBLY_KIT = "4f9578e8-e638-447a-835b-cd7aa282d921",
    GSL_CRAFT_DISASSEMBLY_KIT = "69a4dba2-7023-4f78-8509-dff4201821ad"
}

-- Gunsmith's notes describing each firearm's upgrade path, given the first time a character crafts that firearm.
Rules.CraftNotes = {
    GSL_CRAFT_FLINTLOCK = "9af6bb3b-0a2a-43ee-8513-f02e2a2b6132",
    GSL_CRAFT_BLUNDERBUSS = "f0c60a0e-b975-4bed-bc4e-8cec8a8fc36e",
    GSL_CRAFT_MUSKET = "17f36477-9a3b-450b-b6ee-81d52322ddff"
}

local tinkerHands = {MAIN = "Main", OFF = "Off"}
local tinkerModes = {CAPACITY = "Capacity", DAMAGE = "Damage", RANGE = "Range", REMOVE = "Remove"}

-- Tinkerer spells mark the chosen gun with GSL_TINKER_<HAND>_<MODE>; the server turns that into the gun's record.
function Rules.ParseTinkererStatus(status)
    local hand, mode = status:match("^GSL_TINKER_(%u+)_(%u+)$")
    if not tinkerHands[hand] or not tinkerModes[mode] then return nil end
    return tinkerHands[hand], tinkerModes[mode]
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
    if state.kind == "Musket" then return "1d10+" .. upgrades .. "d4" end
    error("Unknown firearm kind: " .. tostring(state.kind))
end

-- Meters Longarm Specialist adds to a held musket.
Rules.LongarmRange = 6

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
