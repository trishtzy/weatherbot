-- Migration 0006: Seed trivia table with facts from forecasting-2 page
-- Source: https://www.weather.gov.sg/forecasting-2/
-- 1-2 sentences each, excludes weather descriptors, intensity, duration, distribution, time descriptors

INSERT INTO trivia (id, text, source_url) VALUES
(1, 'Weather forecasting involves observations, communications, analysis, prediction, and dissemination. These are all essential components of a weather forecast service.', 'https://www.weather.gov.sg/forecasting-2/'),
(2, 'To prepare a weather forecast, meteorologists must first obtain a detailed picture of present weather conditions over a specific region. Accurate observations of the current weather are the basis of a good weather forecast.', 'https://www.weather.gov.sg/forecasting-2/'),
(3, 'Routine and accurate measurements of the lower and upper atmosphere are collected or observed at ground and upper air stations and from remote sensing systems.', 'https://www.weather.gov.sg/forecasting-2/'),
(4, 'Meteorological observations spanning countries and continents are required because the natural forces that drive the weather do not recognise national boundaries.', 'https://www.weather.gov.sg/forecasting-2/'),
(5, 'MSS routinely exchanges data with other meteorological centres around the world through a dedicated global telecommunications system.', 'https://www.weather.gov.sg/forecasting-2/'),
(6, 'The vast amount of meteorological observations over a large region are plotted on a map with different symbols representing wind, temperature, cloud and other components.', 'https://www.weather.gov.sg/forecasting-2/'),
(7, 'The meteorologist can quickly identify all the weather elements at a certain location, analyse the wind patterns and locate significant weather systems such as storms.', 'https://www.weather.gov.sg/forecasting-2/'),
(8, 'Charts are prepared for the surface and different upper levels of the atmosphere to give a three-dimensional picture of the weather situation.', 'https://www.weather.gov.sg/forecasting-2/'),
(9, 'Temperature profiles are plotted from upper air data so that the vertical stability of the atmosphere can be assessed.', 'https://www.weather.gov.sg/forecasting-2/'),
(10, 'Observation data is used as inputs to numerical weather prediction (NWP) models. These computer models incorporate complex mathematical equations representing well-established physical laws to predict the behaviour of the atmosphere.', 'https://www.weather.gov.sg/forecasting-2/'),
(11, 'In the NWP model, the atmosphere is divided into many blocks of finite size. For a global weather forecast, blocks are 20 km across and a few hundred metres high.', 'https://www.weather.gov.sg/forecasting-2/'),
(12, 'For a local weather forecast for a single country, the NWP model blocks are 2 km across.', 'https://www.weather.gov.sg/forecasting-2/'),
(13, 'The solution of the equations in NWP models proceeds in time-steps of a few minutes, until the required length of forecast has been reached.', 'https://www.weather.gov.sg/forecasting-2/'),
(14, 'Very fast high-performance computers are required to carry out the enormous number of calculations required by NWP models.', 'https://www.weather.gov.sg/forecasting-2/'),
(15, 'The final products from NWP models are predictions of wind, temperature, humidity, rainfall and other meteorological elements.', 'https://www.weather.gov.sg/forecasting-2/'),
(16, 'The NWP approach is not perfect as the equations used to simulate the atmosphere are not precise. The initial state of the atmosphere is also not completely known.', 'https://www.weather.gov.sg/forecasting-2/'),
(17, 'There are many observation gaps especially over the oceans and remote areas, which limit the accuracy of weather forecasts.', 'https://www.weather.gov.sg/forecasting-2/'),
(18, 'NWP is the best approach at forecasting day-to-day weather changes. Forecasts from NWP models have shown significant improvements over the years in terms of accuracy and lead time.', 'https://www.weather.gov.sg/forecasting-2/'),
(19, 'NWP models have high skills in the mid-latitudes where the weather systems tend to be large scale. However, they have relatively low skills in predicting transient, small-scale systems such as localised thunderstorms.', 'https://www.weather.gov.sg/forecasting-2/'),
(20, 'Using data analyses, NWP model products, radar and satellite images, climatology of the area and personal experience, the meteorologist prepares the forecast of how the weather would change in the next few hours and days.', 'https://www.weather.gov.sg/forecasting-2/'),
(21, 'Deadlines have to be met for the media, airline flights and many other user sectors of daily weather information.', 'https://www.weather.gov.sg/forecasting-2/'),
(22, 'Tropical weather is difficult to forecast compared to mid-latitude weather. The tropics have a relatively homogenous air mass and fairly uniform distribution of surface temperature and air pressure.', 'https://www.weather.gov.sg/forecasting-2/'),
(23, 'In the tropics, local and mesoscale effects such as sea breezes are more dominant than synoptic (large-scale) influences, except for tropical cyclones.', 'https://www.weather.gov.sg/forecasting-2/'),
(24, 'Strong convection and moist air in the tropics gives rise to frequent development of rain showers and heavy thunderstorms. These convective weather systems tend to develop and dissipate quickly, often within one or two hours.', 'https://www.weather.gov.sg/forecasting-2/'),
(25, 'As the prevailing winds in the tropics are generally light, predicting the movement of localised storms can be difficult.', 'https://www.weather.gov.sg/forecasting-2/'),
(26, 'The short lifespan and small size of tropical storms presents a forecasting challenge in terms of accuracy and lead time.', 'https://www.weather.gov.sg/forecasting-2/'),
(27, 'Current NWP models have low skills in predicting tropical convection, and the complex dynamical processes that influence weather and climate in the tropics is still poorly understood.', 'https://www.weather.gov.sg/forecasting-2/'),
(28, 'This is an important area of research that is being undertaken at the Centre for Climate Research Singapore (CCRS) and other research centres around the world.', 'https://www.weather.gov.sg/forecasting-2/');

PRAGMA user_version=6;
