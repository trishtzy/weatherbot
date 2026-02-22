-- Migration 0006: Seed trivia table with quality facts
-- Source: https://www.weather.gov.sg/forecasting-2/
-- Each fact is standalone, educational, and self-contained

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

(15, 'To create a weather forecast, meteorologists need a three-dimensional picture of the atmosphere, with charts prepared for the surface and multiple upper levels showing temperature, wind, pressure, and humidity at each height.', 'https://www.weather.gov.sg/forecasting-2/'),

-- Source: MSS Research Letters Issue #6, March 2021
-- Article 1: Seasonal Pollution Plumes over Singapore

(16, 'Singapore uses 1.4 km resolution for local air quality simulations, nested within regional (35 km) and sub-regional (7 km) domains to capture pollution patterns at different scales.', 'MSS Research Letters Issue #6, March 2021'),

(17, 'Pollution plumes from power stations in Singapore vary with monsoon seasons, with their impact on domestic air quality being more severe during the winter monsoon (December-March).', 'MSS Research Letters Issue #6, March 2021'),

(18, 'Singapore has a population of 5.6 million inhabitants in an area of only 720 km², resulting in near co-location of different polluting sources including ports, petrochemical refineries, power plants, and downtown traffic.', 'MSS Research Letters Issue #6, March 2021'),

(19, 'Regional biomass burning is the dominant contributor to Singapore''s air pollution during intense burning years, but this effect is influenced by meteorological and economic factors.', 'MSS Research Letters Issue #6, March 2021'),

(20, 'In Singapore, peak ozone concentrations typically occur around 2-3pm local time, with median values reaching approximately 18 parts per billion by volume (ppbV).', 'MSS Research Letters Issue #6, March 2021'),

-- Article 2: Heavy Rain Total Threat Score (TTS) Tool

(21, 'Heavy rain warnings in Singapore typically have a lead time of only 15 to 30 minutes before flash flood occurrence, driving the need for better predictive tools.', 'MSS Research Letters Issue #6, March 2021'),

(22, 'Weather balloons are launched twice daily from Singapore''s Upper Air Observatory in Paya Lebar - at 8am and 7pm local time - measuring atmospheric conditions up to a height of 30 km.', 'MSS Research Letters Issue #6, March 2021'),

(23, 'Thunderstorms in Singapore typically last between 30 minutes to 1.5 hours, and can occasionally bring heavy rain, lightning, and sometimes hail.', 'MSS Research Letters Issue #6, March 2021'),

(24, 'Singapore has a network of 28 real-time automatic weather stations with rain gauges that have been recording hourly rainfall data since 1980.', 'MSS Research Letters Issue #6, March 2021'),

(25, 'A heavy rain event in Singapore is defined as rainfall accumulation exceeding 45 mm over any rolling 2-hour period at any of the 28 weather stations.', 'MSS Research Letters Issue #6, March 2021'),

(26, 'The Heavy Rain Total Threat Score tool was developed using a 22-year climatological database of radiosonde soundings from 1991 to 2012.', 'MSS Research Letters Issue #6, March 2021'),

(27, 'The Suomi-NPP satellite passes over Singapore in the afternoon (1-3pm local time), providing atmospheric temperature and moisture profiles through the NUCAPS system to help predict heavy rain.', 'MSS Research Letters Issue #6, March 2021'),

(28, 'The climatological chance of heavy rain occurrence in Singapore varies by season: approximately 20% during inter-monsoons, 16% during Northeast Monsoon, and 12% during Southwest Monsoon.', 'MSS Research Letters Issue #6, March 2021'),

-- Article 3: Wet and Dry Spells Characterisation

(29, 'Singapore''s monsoon seasons follow a specific pattern: Northeast Monsoon (Dec 5 - Apr 8), Inter-Monsoon 1 (Apr 9 - Jun 12), Southwest Monsoon (Jun 13 - Oct 19), and Inter-Monsoon 2 (Oct 20 - Dec 4).', 'MSS Research Letters Issue #6, March 2021'),

(30, 'During El Niño years, dry spells are more frequent and pronounced over Singapore and the region, especially during the Southwest Monsoon season (June-October).', 'MSS Research Letters Issue #6, March 2021'),

(31, 'During La Niña years, wet spells become more frequent over Singapore, with more short wet spells observed across all monsoon seasons compared to El Niño years.', 'MSS Research Letters Issue #6, March 2021'),

(32, 'The second inter-monsoon period (late October to early December) experiences the highest mean daily precipitation of all four seasons in the Indonesia-Malaysia region.', 'MSS Research Letters Issue #6, March 2021'),

(33, 'Despite having the lowest mean daily precipitation, the Southwest Monsoon experiences more intense wet spells when they occur, with higher absolute precipitation anomalies.', 'MSS Research Letters Issue #6, March 2021'),

(34, 'From 1981 to 2017, dry spells were more frequent than wet spells over the Indonesia-Malaysia region, though wet spells tended to be more intense when they occurred.', 'MSS Research Letters Issue #6, March 2021'),

(35, 'The ratio of wet spells to dry spells differs most dramatically during the Southwest Monsoon and second inter-monsoon periods when comparing El Niño years to La Niña years.', 'MSS Research Letters Issue #6, March 2021');

PRAGMA user_version=6;
