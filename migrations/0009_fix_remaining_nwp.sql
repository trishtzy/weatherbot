-- Migration 0009: Fix remaining NWP occurrences
-- Capitalize long form and expand any standalone NWP not in brackets

-- Fact 10: Capitalize "numerical weather prediction" to "Numerical Weather Prediction"
UPDATE trivia
SET text = 'Observation data is used as inputs to Numerical Weather Prediction (NWP) models. These computer models incorporate complex mathematical equations representing well-established physical laws to predict the behaviour of the atmosphere.'
WHERE id = 10;

-- Fact 18: Fix second NWP occurrence ("Forecasts from NWP models")
UPDATE trivia
SET text = 'Numerical Weather Prediction (NWP) is the best approach at forecasting day-to-day weather changes. Forecasts from Numerical Weather Prediction (NWP) models have shown significant improvements over the years in terms of accuracy and lead time.'
WHERE id = 18;

-- Fact 20: Expand NWP (was missed entirely)
UPDATE trivia
SET text = 'Using data analyses, Numerical Weather Prediction (NWP) model products, radar and satellite images, climatology of the area and personal experience, the meteorologist prepares the forecast of how the weather would change in the next few hours and days.'
WHERE id = 20;

PRAGMA user_version=9;
