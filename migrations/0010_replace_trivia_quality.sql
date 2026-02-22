-- Migration 0010: Replace trivia with higher quality, standalone facts
-- Each fact should be surprising, educational, and self-contained

-- Delete all existing trivia
DELETE FROM trivia;

-- Insert new high-quality trivia
INSERT INTO trivia (id, text, source_url) VALUES
(1, 'For global weather forecasts, Numerical Weather Prediction (NWP) models divide the atmosphere into blocks that are 20 km across and a few hundred metres high. For local forecasts in Singapore, these blocks shrink to just 2 km across for greater precision.', 'https://www.weather.gov.sg/forecasting-2/'),

(2, 'Thunderstorms in the tropics typically develop and dissipate within just one to two hours, making them extremely difficult to predict compared to weather systems in other parts of the world.', 'https://www.weather.gov.sg/forecasting-2/'),

(3, 'Weather prediction models perform well in mid-latitude regions where weather systems are large-scale, but they have relatively low accuracy in tropical regions like Singapore where small, localised thunderstorms are common.', 'https://www.weather.gov.sg/forecasting-2/'),

(4, 'In tropical regions, local effects like sea breezes have more influence on the weather than large-scale atmospheric patterns. The only exception is during tropical cyclones, when synoptic-scale forces dominate.', 'https://www.weather.gov.sg/forecasting-2/'),

(5, 'The light prevailing winds in the tropics make it difficult to predict where localised storms will move, unlike in mid-latitude regions where stronger winds provide clearer storm trajectories.', 'https://www.weather.gov.sg/forecasting-2/'),

(6, 'Numerical Weather Prediction (NWP) models solve complex mathematical equations in time-steps of just a few minutes, requiring extremely powerful supercomputers to process the enormous number of calculations.', 'https://www.weather.gov.sg/forecasting-2/'),

(7, 'The tropics have relatively uniform air masses and fairly even distribution of temperature and air pressure, which paradoxically makes weather forecasting harder because there are fewer large-scale patterns to track.', 'https://www.weather.gov.sg/forecasting-2/'),

(8, 'Weather observations from countries and continents around the world must be shared because atmospheric forces do not recognise national boundaries. Singapore''s Meteorological Service Singapore (MSS) exchanges data globally through dedicated telecommunications systems.', 'https://www.weather.gov.sg/forecasting-2/'),

(9, 'Numerical Weather Prediction (NWP) models are not perfect because the mathematical equations can only approximate atmospheric behaviour, and the initial state of the atmosphere can never be completely known due to observation gaps over oceans and remote areas.', 'https://www.weather.gov.sg/forecasting-2/'),

(10, 'Despite their limitations, Numerical Weather Prediction (NWP) models remain the best approach for forecasting day-to-day weather changes. Their accuracy and lead time have improved significantly over the decades.', 'https://www.weather.gov.sg/forecasting-2/'),

(11, 'Weather forecasters combine computer model outputs with radar imagery, satellite images, local climate knowledge, and personal experience to prepare forecasts. No single tool provides the complete picture.', 'https://www.weather.gov.sg/forecasting-2/'),

(12, 'Predicting tropical convection remains one of the most challenging problems in meteorology. The Centre for Climate Research Singapore (CCRS) is actively researching the complex processes that influence tropical weather and climate.', 'https://www.weather.gov.sg/forecasting-2/'),

(13, 'The short lifespan and small size of tropical thunderstorms create a fundamental forecasting challenge: by the time a storm is detected and analysed, it may already be dissipating.', 'https://www.weather.gov.sg/forecasting-2/'),

(14, 'Strong convection and moist air in the tropics cause rain showers and thunderstorms to develop frequently, but these systems are notoriously unpredictable because they form and disappear so rapidly.', 'https://www.weather.gov.sg/forecasting-2/'),

(15, 'To create a weather forecast, meteorologists need a three-dimensional picture of the atmosphere, with charts prepared for the surface and multiple upper levels showing temperature, wind, pressure, and humidity at each height.', 'https://www.weather.gov.sg/forecasting-2/');

PRAGMA user_version=10;
