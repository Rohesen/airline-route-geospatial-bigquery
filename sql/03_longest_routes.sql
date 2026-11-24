-- The 20 longest direct airport pairs in the world, with how many airlines fly them.
SELECT
  source_iata,
  dest_iata,
  source_country,
  dest_country,
  distance_km,
  COUNT(DISTINCT airline) AS airlines
FROM `{project}.{dataset}.routes_geo`
WHERE source_iata < dest_iata  -- count each pair once, not once per direction
GROUP BY source_iata, dest_iata, source_country, dest_country, distance_km
ORDER BY distance_km DESC
LIMIT 20;
