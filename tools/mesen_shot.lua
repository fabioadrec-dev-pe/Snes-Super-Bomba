local frames = 0
local outDir = emu.getScriptDataFolder()
if outDir == nil or outDir == "" then
  outDir = "/home/fabio/Snes-Super-Bomba/tools/mesen_data"
end

local function saveShot(name)
  local png = emu.takeScreenshot()
  if png == nil or png == "" then
    emu.log("screenshot failed: " .. name)
    return
  end
  local path = outDir .. "/" .. name
  local f = io.open(path, "wb")
  if f == nil then
    emu.log("cannot write " .. path)
    return
  end
  f:write(png)
  f:close()
  emu.log("saved " .. path)
end

function onFrame()
  frames = frames + 1
  if frames == 90 then
    saveShot("menu_1p.png")
  elseif frames == 120 then
    emu.setInput(0, { down = true })
  elseif frames == 135 then
    emu.setInput(0, {})
  elseif frames == 180 then
    saveShot("menu_2p.png")
  elseif frames == 210 then
    emu.setInput(0, { down = true })
  elseif frames == 225 then
    emu.setInput(0, {})
  elseif frames == 270 then
    saveShot("menu_opt.png")
    emu.stop(0)
  end
end

emu.addEventCallback(onFrame, emu.eventType.endFrame)
emu.log("menu screenshot script started, out=" .. outDir)
