-- Second Glance: garment catalog, demand predicates, level definitions.
-- Garment catalog (28 items). Categories in order: top, bottom, shoes,
-- hat, extra. Each item: name, color, style.
-- Demands (clues that describe the reference; every level's reference
-- MUST satisfy all three, enforced by the load-time check below):
--   Gran (WARM): any cozy-style item, or a hat/scarf worn.
--   Friend (BOLD): any red or purple item, or a bold-style item.
--   Photographer (MATCHED): no more than 3 distinct colors.
-- Reference outfit = one garment per category (5 slots), stored as
-- {top, bottom, shoes, hat, extra} indices (1-based, 0 = empty).
-- Mission types: "match" (reach a match target), "critics" (please all
-- 3 critics), "perfect" (exact 5/5 match), "score" (reach a score target).
local M = {}

M.CATS = { "top", "bottom", "shoes", "hat", "extra" }
M.CAT_LABELS = { top = "TOP", bottom = "BOTTOM", shoes = "SHOES",
                 hat = "HAT", extra = "EXTRA" }

M.GARMENTS = {
  top = {
    { name = "Red Tee", color = "red", style = "casual" },
    { name = "Blue Blouse", color = "blue", style = "smart" },
    { name = "Green Sweater", color = "green", style = "cozy" },
    { name = "Black Jacket", color = "black", style = "smart" },
    { name = "Yellow Shirt", color = "yellow", style = "casual" },
    { name = "Purple Hoodie", color = "purple", style = "sporty" },
  },
  bottom = {
    { name = "Blue Jeans", color = "blue", style = "casual" },
    { name = "Red Skirt", color = "red", style = "bold" },
    { name = "Black Trousers", color = "black", style = "smart" },
    { name = "Yellow Shorts", color = "yellow", style = "sporty" },
    { name = "Green Skirt", color = "green", style = "casual" },
    { name = "Brown Cargo", color = "brown", style = "casual" },
  },
  shoes = {
    { name = "White Sneakers", color = "white", style = "sporty" },
    { name = "Brown Boots", color = "brown", style = "cozy" },
    { name = "Red Heels", color = "red", style = "smart" },
    { name = "Yellow Sandals", color = "yellow", style = "casual" },
    { name = "Blue Trainers", color = "blue", style = "sporty" },
  },
  hat = {
    { name = "Red Cap", color = "red", style = "sporty" },
    { name = "Green Beanie", color = "green", style = "cozy" },
    { name = "Yellow Sunhat", color = "yellow", style = "casual" },
    { name = "Purple Beret", color = "purple", style = "smart" },
    { name = "Black Fedora", color = "black", style = "smart" },
  },
  extra = {
    { name = "Red Scarf", color = "red", style = "cozy" },
    { name = "Gold Necklace", color = "gold", style = "smart" },
    { name = "Black Glasses", color = "black", style = "smart" },
    { name = "Blue Bag", color = "blue", style = "casual" },
    { name = "Brown Belt", color = "brown", style = "casual" },
    { name = "Pink Earrings", color = "pink", style = "bold" },
  },
}

function M.garment(cat, idx)
  local list = M.GARMENTS[cat]
  if not list or not idx or idx < 1 or idx > #list then return nil end
  return list[idx]
end

function M.count(cat)
  return #M.GARMENTS[cat]
end

-- Demand predicates. outfit is {top=n, bottom=n, shoes=n, hat=n, extra=n}.
function M.warm(outfit)
  if outfit.hat and outfit.hat > 0 then return true end
  if outfit.extra and outfit.extra == 1 then return true end -- red scarf
  for _, cat in ipairs(M.CATS) do
    local g = M.garment(cat, outfit[cat])
    if g and g.style == "cozy" then return true end
  end
  return false
end

function M.bold(outfit)
  for _, cat in ipairs(M.CATS) do
    local g = M.garment(cat, outfit[cat])
    if g and (g.color == "red" or g.color == "purple"
              or g.style == "bold") then
      return true
    end
  end
  return false
end

function M.matched(outfit)
  local seen = {}
  local n = 0
  for _, cat in ipairs(M.CATS) do
    local g = M.garment(cat, outfit[cat])
    if g and not seen[g.color] then
      seen[g.color] = true
      n = n + 1
    end
  end
  return n <= 3
end

function M.demands(outfit)
  return { warm = M.warm(outfit), bold = M.bold(outfit),
           matched = M.matched(outfit) }
end

function M.satisfies_all(outfit)
  return M.warm(outfit) and M.bold(outfit) and M.matched(outfit)
end

local function ref(t, b, s, h, e)
  return { top = t, bottom = b, shoes = s, hat = h, extra = e }
end

-- ref: {top,bottom,shoes,hat,extra}. glance: seconds the reference is
-- shown. peeks: peek count. time: level time limit (s). threshold:
-- minimum match (of 500) to win. critics: critics that must be pleased.
-- stars: total-score thresholds for 1/2/3 stars.
M.LEVELS = {
  { ref = ref(3, 5, 2, 2, 1), glance = 6.0, peeks = 2, time = 150,
    threshold = 250, critics = 2,
    client = "Maya", occasion = "Market day in Kathmandu",
    mission = { type = "match", target = 300,
                text = "Match 300 of the look!" },
    stars = { 400, 600, 750 } },
  { ref = ref(1, 1, 5, 1, 4), glance = 5.7, peeks = 2, time = 150,
    threshold = 250, critics = 2,
    client = "Arun", occasion = "First day at the studio",
    mission = { type = "score", target = 600,
                text = "Score 600 points" },
    stars = { 600, 700, 780 } },
  { ref = ref(2, 3, 3, 5, 3), glance = 5.4, peeks = 2, time = 160,
    threshold = 300, critics = 2,
    client = "Sita", occasion = "Evening at the tea house",
    mission = { type = "match", target = 350,
                text = "Match 350 of the look!" },
    stars = { 500, 650, 750 } },
  { ref = ref(6, 2, 3, 4, 1), glance = 5.1, peeks = 2, time = 160,
    threshold = 300, critics = 3,
    client = "Bikash", occasion = "Photo shoot by the stupa",
    mission = { type = "critics", target = 3,
                text = "Please all 3 critics!" },
    stars = { 550, 700, 780 } },
  { ref = ref(5, 4, 4, 3, 6), glance = 4.8, peeks = 1, time = 170,
    threshold = 500, critics = 3,
    client = "Anisha", occasion = "Festival afternoon",
    mission = { type = "perfect", target = 500,
                text = "A perfect 5/5 match!" },
    stars = { 650, 750, 800 } },
  { ref = ref(3, 6, 2, 2, 1), glance = 4.5, peeks = 1, time = 170,
    threshold = 350, critics = 3,
    client = "Deepak", occasion = "Hike above the valley",
    mission = { type = "score", target = 700,
                text = "Score 700 points" },
    stars = { 700, 760, 800 } },
  { ref = ref(4, 3, 3, 5, 2), glance = 4.2, peeks = 1, time = 180,
    threshold = 350, critics = 3,
    client = "Priya", occasion = "Gallery opening night",
    mission = { type = "match", target = 400,
                text = "Match 400 of the look!" },
    stars = { 600, 720, 790 } },
  { ref = ref(2, 1, 5, 1, 4), glance = 3.9, peeks = 1, time = 180,
    threshold = 350, critics = 3,
    client = "Rohan", occasion = "Busking at the square",
    mission = { type = "critics", target = 3,
                text = "Please all 3 critics!" },
    stars = { 600, 720, 790 } },
  { ref = ref(1, 2, 3, 4, 6), glance = 3.6, peeks = 1, time = 190,
    threshold = 375, critics = 3,
    client = "Laxmi", occasion = "Dance recital",
    mission = { type = "score", target = 750,
                text = "Score 750 points" },
    stars = { 750, 780, 800 } },
  { ref = ref(6, 5, 3, 2, 1), glance = 3.4, peeks = 1, time = 190,
    threshold = 500, critics = 3,
    client = "Nima", occasion = "Winter market stroll",
    mission = { type = "perfect", target = 500,
                text = "A perfect 5/5 match!" },
    stars = { 650, 750, 800 } },
  { ref = ref(5, 2, 3, 1, 2), glance = 3.2, peeks = 1, time = 200,
    threshold = 400, critics = 3,
    client = "Kiran", occasion = "Rooftop dinner",
    mission = { type = "critics", target = 3,
                text = "Please all 3 critics!" },
    stars = { 650, 750, 800 } },
  { ref = ref(4, 6, 2, 5, 6), glance = 3.0, peeks = 1, time = 210,
    threshold = 400, critics = 3,
    client = "Tara", occasion = "The grand opening",
    mission = { type = "perfect", target = 500,
                text = "A perfect 5/5 match!" },
    stars = { 700, 780, 800 } },
}

M.ENDLESS = { glance = 4.0, peeks = 1, time = 210,
  threshold = 300, critics = 2,
  mission = { type = "endless", text = "Clients keep coming - 3 fails ends it!" },
  stars = { 0, 0, 0 } }

M.ENDLESS_CLIENTS = {
  { name = "Maya", occasion = "Market day" },
  { name = "Arun", occasion = "Studio visit" },
  { name = "Sita", occasion = "Tea house evening" },
  { name = "Bikash", occasion = "Photo shoot" },
  { name = "Anisha", occasion = "Festival day" },
  { name = "Deepak", occasion = "Valley hike" },
  { name = "Priya", occasion = "Gallery night" },
  { name = "Rohan", occasion = "Street performance" },
  { name = "Laxmi", occasion = "Dance recital" },
  { name = "Nima", occasion = "Winter market" },
  { name = "Kiran", occasion = "Rooftop dinner" },
  { name = "Tara", occasion = "Grand opening" },
}

-- A random reference that satisfies all three demands (rejection sample).
function M.random_ref()
  for _ = 1, 200 do
    local r = ref(math.random(6), math.random(6), math.random(5),
                  math.random(5), math.random(6))
    if M.satisfies_all(r) then return r end
  end
  -- Fallback: a known-good reference (level 1).
  return ref(3, 5, 2, 2, 1)
end

function M.get(n)
  return M.LEVELS[math.max(1, math.min(#M.LEVELS, n))]
end

-- Load-time check: every level's reference must satisfy all 3 demands.
for i, lv in ipairs(M.LEVELS) do
  local d = M.demands(lv.ref)
  if not d.warm then
    print("WARNING second-glance levels: level " .. i ..
      " reference fails Gran (WARM)")
  end
  if not d.bold then
    print("WARNING second-glance levels: level " .. i ..
      " reference fails Friend (BOLD)")
  end
  if not d.matched then
    print("WARNING second-glance levels: level " .. i ..
      " reference fails Photographer (MATCHED)")
  end
end

return M
