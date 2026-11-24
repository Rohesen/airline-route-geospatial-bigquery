-- Turn latitude/longitude columns into a GEOGRAPHY point per airport.
-- ST_GEOGPOINT takes (longitude, latitude), in that order.
CREATE OR REPLACE TABLE `{project}.{dataset}.airports_geo`
CLUSTER BY country AS
SELECT
  airport_id,
  iata,
  icao,
  name,
  city,
  country,
  latitude,
  longitude,
  altitude_ft,
  timezone,
  ST_GEOGPOINT(longitude, latitude) AS location
FROM `{project}.{dataset}.airports_raw`;
