-- Migration 0008: Expand all acronyms in trivia facts
-- Show long form first, then acronym in brackets

-- Fact 5: MSS -> Meteorological Service Singapore (MSS)
UPDATE trivia
SET text = 'The Meteorological Service Singapore (MSS) routinely exchanges data with other meteorological centres around the world through a dedicated global telecommunications system.'
WHERE id = 5;

-- Fact 11: NWP -> Numerical Weather Prediction (NWP)
UPDATE trivia
SET text = 'In the Numerical Weather Prediction (NWP) model, the atmosphere is divided into many blocks of finite size. For a global weather forecast, blocks are 20 km across and a few hundred metres high.'
WHERE id = 11;

-- Fact 12: NWP -> Numerical Weather Prediction (NWP)
UPDATE trivia
SET text = 'For a local weather forecast for a single country, the Numerical Weather Prediction (NWP) model blocks are 2 km across.'
WHERE id = 12;

-- Fact 13: NWP -> Numerical Weather Prediction (NWP)
UPDATE trivia
SET text = 'The solution of the equations in Numerical Weather Prediction (NWP) models proceeds in time-steps of a few minutes, until the required length of forecast has been reached.'
WHERE id = 13;

-- Fact 15: NWP -> Numerical Weather Prediction (NWP)
UPDATE trivia
SET text = 'The final products from Numerical Weather Prediction (NWP) models are predictions of wind, temperature, humidity, rainfall and other meteorological elements.'
WHERE id = 15;

-- Fact 16: NWP -> Numerical Weather Prediction (NWP)
UPDATE trivia
SET text = 'The Numerical Weather Prediction (NWP) approach is not perfect as the equations used to simulate the atmosphere are not precise. The initial state of the atmosphere is also not completely known.'
WHERE id = 16;

-- Fact 18: NWP -> Numerical Weather Prediction (NWP)
UPDATE trivia
SET text = 'Numerical Weather Prediction (NWP) is the best approach at forecasting day-to-day weather changes. Forecasts from NWP models have shown significant improvements over the years in terms of accuracy and lead time.'
WHERE id = 18;

-- Fact 19: NWP -> Numerical Weather Prediction (NWP)
UPDATE trivia
SET text = 'Numerical Weather Prediction (NWP) models have high skills in the mid-latitudes where the weather systems tend to be large scale. However, they have relatively low skills in predicting transient, small-scale systems such as localised thunderstorms.'
WHERE id = 19;

-- Fact 27: NWP -> Numerical Weather Prediction (NWP)
UPDATE trivia
SET text = 'Current Numerical Weather Prediction (NWP) models have low skills in predicting tropical convection, and the complex dynamical processes that influence weather and climate in the tropics is still poorly understood.'
WHERE id = 27;

PRAGMA user_version=8;
