from geopy.geocoders import Nominatim

def get_coords_from_address(address):
    driver = Nominatim(user_agent="ensae-cloud-computing-students")
    location = driver.geocode(address)
    return location.address, (location.latitude, location.longitude)

def get_address_from_coords(coords: tuple):
    driver = Nominatim(user_agent="ensae-cloud-computing-students")
    location = driver.reverse(coords)
    return location.address, (location.latitude, location.longitude)

def create_gmaps_link(coords: tuple):
    address = get_address_from_coords(coords)[0]
    return "https://maps.google.com/maps/dir//{}".format(address).replace(' ','+')


if __name__ == '__main__':
    print(get_coords_from_address('23 rue des Jeuneurs, 75002'))