-- Indian airports that sit within 100 km of another airport: overlapping
-- catchment areas. ST_DWITHIN is a spatial join that BigQuery can optimise.
SELECT
  a.iata AS airport,
  a.city,
  b.iata AS nearby_airport,
  b.city AS nearby_city,
  ROUND(ST_DISTANCE(a.location, b.location) / 1000, 1) AS distance_km
FROM `{project}.{dataset}.airports_geo` AS a
JOIN `{project}.{dataset}.airports_geo` AS b
  ON ST_DWITHIN(a.location, b.location, 100000)  -- 100 km in metres
 AND a.iata < b.iata
WHERE a.country = 'India' AND b.country = 'India'
ORDER BY distance_km;
