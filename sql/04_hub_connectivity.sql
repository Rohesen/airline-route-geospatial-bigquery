-- Rank airports as hubs: direct destinations, countries reached and the
-- average and longest distance flown from them.
SELECT
  a.iata,
  a.name,
  a.country,
  COUNT(DISTINCT r.dest_iata) AS destinations,
  COUNT(DISTINCT r.dest_country) AS countries_served,
  ROUND(AVG(r.distance_km)) AS avg_route_km,
  MAX(r.distance_km) AS longest_route_km
FROM `{project}.{dataset}.routes_geo` AS r
JOIN `{project}.{dataset}.airports_geo` AS a ON r.source_iata = a.iata
GROUP BY a.iata, a.name, a.country
ORDER BY destinations DESC
LIMIT 20;
