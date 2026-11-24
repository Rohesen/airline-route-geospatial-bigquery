-- Enrich every direct route with both airport locations, the great-circle
-- distance and the route itself as a GEOGRAPHY line.
-- ST_DISTANCE returns metres on the WGS84 spheroid; ST_MAKELINE builds a
-- geodesic edge, so the line follows the Earth's curve.
CREATE OR REPLACE TABLE `{project}.{dataset}.routes_geo`
CLUSTER BY source_country, dest_country AS
SELECT
  r.airline,
  r.source_iata,
  r.dest_iata,
  r.codeshare,
  r.equipment,
  s.country AS source_country,
  d.country AS dest_country,
  s.country = d.country AS is_domestic,
  ROUND(ST_DISTANCE(s.location, d.location) / 1000, 1) AS distance_km,
  ST_MAKELINE(s.location, d.location) AS route_line
FROM `{project}.{dataset}.routes_raw` AS r
JOIN `{project}.{dataset}.airports_geo` AS s ON r.source_iata = s.iata
JOIN `{project}.{dataset}.airports_geo` AS d ON r.dest_iata = d.iata;
