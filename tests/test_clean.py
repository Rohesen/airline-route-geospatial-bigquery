from pathlib import Path

from geo_routes.clean import load_airports, load_routes

AIRPORTS = (
    '1,"Indira Gandhi International Airport","Delhi","India","DEL","VIDP",28.5665,77.1031,777,5.5,"N","Asia/Calcutta","airport","OurAirports"\n'
    '2,"Chhatrapati Shivaji International Airport","Mumbai","India","BOM","VABB",19.0887,72.8679,39,5.5,"N","Asia/Calcutta","airport","OurAirports"\n'
    '3,"No Code Airstrip","Nowhere","India",\\N,\\N,10.0,70.0,0,5.5,"N","Asia/Calcutta","airport","OurAirports"\n'
    '4,"Delhi Railway Station","Delhi","India","DLI",\\N,28.64,77.22,700,5.5,"N","Asia/Calcutta","station","User"\n'
)
ROUTES = (
    "AI,1,DEL,1,BOM,2,,0,320\n"
    "AI,1,DEL,1,BOM,2,,0,320\n"   # duplicate
    "AI,1,DEL,1,XXX,9,,0,320\n"   # unknown airport
    "6E,2,BOM,2,DEL,1,Y,0,321\n"
    "6E,2,BOM,2,DEL,1,,1,321\n"   # one stop, not direct
)


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text)
    return p


def test_airports_keep_only_real_airports_with_codes(tmp_path):
    airports = load_airports(_write(tmp_path, "a.dat", AIRPORTS))
    assert sorted(airports["iata"]) == ["BOM", "DEL"]


def test_routes_are_direct_known_and_unique(tmp_path):
    airports = load_airports(_write(tmp_path, "a.dat", AIRPORTS))
    routes = load_routes(_write(tmp_path, "r.dat", ROUTES), airports)
    assert len(routes) == 2
    assert set(zip(routes["source_iata"], routes["dest_iata"])) == {("DEL", "BOM"), ("BOM", "DEL")}
    assert bool(routes.loc[routes["airline"] == "6E", "codeshare"].item())
