from napalm import get_network_driver
import login
from pprint import pprint

driver = get_network_driver ('ios')

enable_pass = {'secret': login.password }

ios = driver ('10.87.80.14', login.username, login.password, optional_args = enable_pass)
ios.open()

output = ios.get_lldp_neighbors()

pprint (output)



ios.close()
