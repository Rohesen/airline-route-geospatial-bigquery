-- Group Indian airports into regional clusters with DBSCAN: points within
-- 150 km of each other join a cluster if it has at least 3 airports.
-- Each cluster gets its centre point and the polygon that encloses it.
WITH clustered AS (
  SELECT
    iata,
    city,
    location,
    ST_CLUSTERDBSCAN(location, 150000, 3) OVER () AS cluster_id
  FROM `{project}.{dataset}.airports_geo`
  WHERE country = 'India'
)
SELECT
  cluster_id,
  COUNT(*) AS airports,
  STRING_AGG(iata, ', ' ORDER BY iata) AS members,
  ST_CENTROID_AGG(location) AS cluster_centre,
  ST_CONVEXHULL(ST_UNION_AGG(location)) AS cluster_area,
  ROUND(ST_AREA(ST_CONVEXHULL(ST_UNION_AGG(location))) / 1e6) AS area_km2
FROM clustered
WHERE cluster_id IS NOT NULL  -- NULL means noise: an isolated airport
GROUP BY cluster_id
ORDER BY airports DESC;
