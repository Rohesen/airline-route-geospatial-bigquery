-- Which destinations can you fly to directly from Delhi (DEL) within
-- 3,000 km? Combines a route lookup with a distance filter on GEOGRAPHY.
SELECT
  d.iata,
  d.city,
  d.country,
  ROUND(ST_DISTANCE(o.location, d.location) / 1000) AS distance_km
FROM `{project}.{dataset}.airports_geo` AS o
JOIN `{project}.{dataset}.routes_raw` AS r ON r.source_iata = o.iata
JOIN `{project}.{dataset}.airports_geo` AS d ON r.dest_iata = d.iata
WHERE o.iata = 'DEL'
  AND ST_DWITHIN(o.location, d.location, 3000000)
GROUP BY d.iata, d.city, d.country, distance_km
ORDER BY distance_km;
