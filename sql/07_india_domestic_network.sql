-- India's domestic network by distance band. Run this in BigQuery Geo Viz
-- with route_line selected to see the routes drawn on a map.
SELECT
  source_iata,
  dest_iata,
  distance_km,
  CASE
    WHEN distance_km < 500 THEN '1. under 500 km'
    WHEN distance_km < 1000 THEN '2. 500-1,000 km'
    WHEN distance_km < 1500 THEN '3. 1,000-1,500 km'
    ELSE '4. over 1,500 km'
  END AS distance_band,
  COUNT(DISTINCT airline) AS airlines,
  ANY_VALUE(route_line) AS route_line
FROM `{project}.{dataset}.routes_geo`
WHERE is_domestic AND source_country = 'India' AND source_iata < dest_iata
GROUP BY source_iata, dest_iata, distance_km
ORDER BY distance_km DESC;
