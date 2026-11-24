-- Second Glance: outfit logic (pure data, no GUI, no Defold APIs).
-- Outfit state is {top=n, bottom=n, shoes=n, hat=n, extra=n} with 0 = empty.
-- Scoring per slot vs the reference: exact garment = 100, same color
-- different garment = 40, same style different garment = 20, else 0
-- (max match 500). Each satisfied critic = +100. Each peek costs 50.
local levels = require("main.levels")

local M = {}

function M.new()
  return { top = 0, bottom = 0, shoes = 0, hat = 0, extra = 0 }
end

function M.empty(outfit)
  for _, cat in ipairs(levels.CATS) do
    if outfit[cat] and outfit[cat] ~= 0 then return false end
  end
  return true
end

function M.copy(outfit)
  local c = {}
  for _, cat in ipairs(levels.CATS) do c[cat] = outfit[cat] or 0 end
  return c
end

function M.to_string(outfit)
  return (outfit.top or 0) .. "," .. (outfit.bottom or 0) .. "," ..
    (outfit.shoes or 0) .. "," .. (outfit.hat or 0) .. "," ..
    (outfit.extra or 0)
end

-- Score one slot: 100 exact, 40 same color, 20 same style, else 0.
function M.slot_score(cat, worn, ref_idx)
  if not worn or worn == 0 or not ref_idx or ref_idx == 0 then return 0 end
  if worn == ref_idx then return 100 end
  local g = levels.garment(cat, worn)
  local r = levels.garment(cat, ref_idx)
  if not g or not r then return 0 end
  if g.color == r.color then return 40 end
  if g.style == r.style then return 20 end
  return 0
end

function M.match(outfit, ref)
  local total = 0
  local exact = 0
  for _, cat in ipairs(levels.CATS) do
    local s = M.slot_score(cat, outfit[cat], ref[cat])
    total = total + s
    if s == 100 then exact = exact + 1 end
  end
  return total, exact
end

-- Critic satisfaction for an outfit: {warm=bool, bold=bool, matched=bool}.
function M.critics(outfit)
  return levels.demands(outfit)
end

function M.critic_count(outfit)
  local d = levels.demands(outfit)
  local n = 0
  if d.warm then n = n + 1 end
  if d.bold then n = n + 1 end
  if d.matched then n = n + 1 end
  return n
end

-- Full present scoring. peeks_used: number of peeks taken this client.
-- Returns total, match, exact, critic_count.
function M.present(outfit, ref, peeks_used)
  local match, exact = M.match(outfit, ref)
  local critics = M.critic_count(outfit)
  local total = match + critics * 100 - (peeks_used or 0) * 50
  return total, match, exact, critics
end

-- Win check for a level def. mission is the level's mission table.
function M.wins(match, critics, total, def)
  if match < (def.threshold or 0) then return false end
  if critics < (def.critics or 0) then return false end
  local m = def.mission
  if not m then return true end
  if m.type == "match" then
    return match >= (m.target or 0)
  elseif m.type == "score" then
    return total >= (m.target or 0)
  elseif m.type == "perfect" then
    return match >= 500
  elseif m.type == "critics" then
    return critics >= 3
  end
  return true
end

function M.lose_reason(match, critics, total, def)
  if match < (def.threshold or 0) then
    return "Match " .. match .. " / " .. (def.threshold or 0) ..
      " - too far from the look!"
  end
  if critics < (def.critics or 0) then
    return "Only " .. critics .. " of " .. (def.critics or 0) ..
      " critics pleased!"
  end
  local m = def.mission
  if m and m.type == "match" then
    return "Match " .. match .. " - needed " .. (m.target or 0) .. "!"
  elseif m and m.type == "score" then
    return "Score " .. total .. " - needed " .. (m.target or 0) .. "!"
  elseif m and m.type == "perfect" then
    return "Not a perfect 5/5 match!"
  elseif m and m.type == "critics" then
    return "All 3 critics must be pleased!"
  end
  return "The guest left!"
end

return M
