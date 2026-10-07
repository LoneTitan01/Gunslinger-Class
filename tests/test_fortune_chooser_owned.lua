local fortuneHandle = "h00000027g0000g4000g8000g000000000001"
local function context(values)
    local result = {TypeInfo = function() return {Properties = {}, DependencyProperties = {}} end}
    return setmetatable(result, {
        __index = values,
        __newindex = function() error("Native row properties are read-only") end
    })
end
-- Exact properties captured from the live game, including the untranslated Name.
local native = context({
    Type = "ls.VMCharacterCreationPassive", Name = fortuneHandle, IconName = "GSL_DesperadosFortune",
    Blocked = false, Replaced = false, Value = 0, Enabled = true
})
local evolution = context({
    Type = "ls.VMCharacterCreationPassive", Name = "h31000002g0000g4000g8000g000000000001",
    IconName = "GSL_DesperadosFortune", Value = 0, Enabled = true
})
local interrupt = context({
    Type = "ls.VMInterrupt", Name = fortuneHandle, IconName = "GSL_DesperadosFortune", Enabled = true
})
local visits = 0
local function widget(model, children)
    return {
        Type = "Noesis.ContentControl", DataContext = model, IsEnabled = true,
        VisualChildrenCount = #children,
        TypeInfo = function() return {
            Properties = {}, DependencyProperties = {{Name = "DataContext"}, {Name = "IsEnabled"}}
        } end,
        VisualChild = function(_, index)
            visits = visits + 1
            assert(index >= 1)
            return children[index]
        end
    }
end
local fortuneRow = widget(native, {})
fortuneRow.IsEnabled = nil
local tooltip = {
    Type = "ls.LSTooltip", Content = native,
    TypeInfo = function() return {
        Properties = {}, DependencyProperties = {{Name = "Content"}, {Name = "DataContext"}}
    } end
}
local text = widget(nil, {})
text.Type = "Noesis.TextBlock"
text.ToolTip = tooltip
text.TypeInfo = function() return {
    Properties = {}, DependencyProperties = {{Name = "ToolTip"}}
} end
fortuneRow.VisualChildrenCount = 1
fortuneRow.VisualChild = function(_, index) assert(index == 1); return text end
local presenter = {
    Type = "Noesis.ContentPresenter", DataContext = native, VisualChildrenCount = 1,
    TypeInfo = function() return {
        Properties = {}, DependencyProperties = {{Name = "DataContext"}}
    } end,
    VisualChild = function(_, index) assert(index == 1); return fortuneRow end
}
local noticeRow = widget(evolution, {})
local interruptRow = widget(interrupt, {})
local root = widget(nil, {widget(true, {}), widget(42, {}), widget({}, {}), noticeRow, interruptRow, presenter})
local registrations = 0
local time, step = 0, 0
Ext = {
    UI = {
        GetRoot = function() return root end,
        RegisterType = function(name, properties, wrapped)
            assert(name == "GSL_OwnedFortuneBindings" and wrapped == "ls.VMCharacterCreationPassive")
            assert(properties.Value.Notify and properties.Enabled.Notify)
            assert(properties.OriginalWidgetEnabled == nil, "Widget IsEnabled must not be saved in the wrapper")
            registrations = registrations + 1
            return true
        end,
        Instantiate = function(name, original)
            return setmetatable({Type = name}, {
                __index = original,
                __newindex = function(object, key, value)
                    if key == "OriginalWidgetEnabled" or key == "Enabled" then
                        assert(type(value) == "boolean", "boolean expected, got " .. type(value))
                    end
                    rawset(object, key, value)
                end
            })
        end
    },
    Timer = {MicrosecTime = function() time = time + step; return time end}
}
local update = dofile("GunslingerClass\\Mods\\GunslingerClass\\ScriptExtender\\Lua\\FortuneChooserOwned.lua")
update(false)
assert(visits == 0, "No ownership must not start a UI scan")
update(true)
assert(fortuneRow.DataContext.Value == 1 and not fortuneRow.DataContext.Enabled and fortuneRow.IsEnabled == nil,
    "The live row's localization handle must match and receive selected-before bindings")
assert(native.Value == 0 and native.Enabled, "Read-only native state must be forwarded, not overwritten")
assert(noticeRow.DataContext == evolution and interruptRow.DataContext == interrupt,
    "The shared Fortune icon/name must not match notices or interrupts")
assert(fortuneRow.DataContext.Blocked == false, "Unchanged properties must forward to the original row")
assert(tooltip.Content == native and tooltip.DataContext == native,
    "Hover descriptions must receive the native passive model rather than the wrapper type")
assert(presenter.DataContext == native and presenter.IsEnabled == nil,
    "Presentation-only elements must not be overridden or prevent discovery of the interactive child")
tooltip.Content = fortuneRow.DataContext
tooltip.DataContext = fortuneRow.DataContext
update(true)
assert(tooltip.Content == native and tooltip.DataContext == native,
    "A refreshed template must not render se::GSL_OwnedFortuneBindings as its tooltip")
local cachedVisits = visits
for _ = 1, 50 do update(true) end
assert(visits - cachedVisits == 50 and registrations == 1,
    "An unchanged chooser must check only its cached row, without wrapping repeatedly")
update(false)
assert(fortuneRow.DataContext == native and fortuneRow.IsEnabled == nil,
    "Cancellation must restore the original row without inventing an IsEnabled value")
assert(tooltip.Content == native, "Cancellation must preserve the native Fortune tooltip")
local children = {}
for _ = 1, 1000 do children[#children + 1] = widget(nil, {}) end
local last = widget(native, {})
children[#children + 1] = last
root = widget(nil, children)
step = 200
for _ = 1, 510 do
    local before = visits
    update(true)
    assert(visits - before <= 2, "A wide tree must yield at the elapsed-time limit")
end
assert(last.DataContext.Value == 1 and not last.DataContext.Enabled and last.IsEnabled,
    "Budgeted discovery must change only model bindings, not widget dependency properties")
update(false)
assert(last.DataContext == native and last.IsEnabled, "Cached row restoration must not wait for a full rescan")
for _ = 1, 510 do update(false) end
cachedVisits = visits
update(false)
assert(visits == cachedVisits, "A closed chooser must stop inspecting the UI")
print("Fortune chooser ownership passed: live handle/type matching, read-only wrapper, scoped restoration, cached row checks and elapsed-time budget")
