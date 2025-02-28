import platform
import subprocess
import pprint

from src.mcm.api import Call

pp = pprint.PrettyPrinter(indent=4)

# test = Call()
# pp.pprint(test.get_channels())
# pp.pprint(test.monitor_all_channels("70", "on"))

# print(test.get("6551.2.3.0"))
# for i in range(8):



#     print(test.post({f"6501.{i}.0":f"232.0.3.10{i}"}))
    
#     print(test.post({f"6601.{i}.0":f"232.48.3.10{i}"}))
#     for ch in range(4):
#         print(test.post({f"6551.{i}.{ch}.0":f"232.16.9.1{ch}{i}"}))

import os

def ping(host):
  """
  Pings a host and returns True if the host is reachable, False otherwise.
  """
  response = os.system("ping -c 1 " + host)
  if response == 0:
    return True
  else:
    return False

# Get the IP address to ping from the user
ip_address = "10.244.169.64"

# Ping the IP address
if ping(ip_address):
  print(ip_address + " is reachable")
else:
  print(ip_address + " is unreachable")