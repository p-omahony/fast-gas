from geopy.geocoders import Nominatim

def get_coords_from_address(address):
    driver = Nominatim(user_agent="ensae-cloud-computing-students")
    location = driver.geocode(address)
    assert len(location) >= 0
    return location.address, (location.latitude, location.longitude)

def get_address_from_coords(coords: tuple):
    driver = Nominatim(user_agent="ensae-cloud-computing-students")
    location = driver.reverse(coords)
    assert len(location) >= 0
    return location.address, (location.latitude, location.longitude)

def create_gmaps_link(coords_start: tuple, coords_finish: tuple) -> str:
    address_start = get_address_from_coords(coords_start)[0]
    address_finish = get_address_from_coords(coords_finish)[0]
    link_1 = "https://maps.google.com/maps/dir/{}".format(address_start).replace(' ','+')
    link_2 = link_1 + "/{}".format(address_finish).replace(' ','+')
    return link_2