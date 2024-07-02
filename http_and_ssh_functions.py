"""
Functions for uploading and running a new protocol to the Flex and downloading a file from the Flex to a local computer
using scp.
"""

import requests
import json
import paramiko
from scp import SCPClient

# The IP of the Flex
ROBOT_IP = "10.154.3.53"
# The index at which a protocol/run ID starts. The ID is returned by requests.post()
ID_START_IDX = 17
# The string length of a protocol/run ID
ID_LENGTH = 36

"""
Uploads a new protocol to the Flex and runs it.
@param robot_ip is the Wired or Wireless IP of the Flex
@param protocol_file is the filename of the protocol to upload and run. Make sure the directory you run this script in
has the protocol_file in it
@return the status code of the post request
"""
def run_protocol(robot_ip: str, protocol_file: str):

    # Upload a new protocol to the Flex
    url = "http://" + robot_ip + ":31950/protocols"
    headers = {"Opentrons-Version": "3"}
    files = {"files": open(protocol_file, "rb")}
    response = requests.post(url, headers=headers, files=files)
    protocol_id = response.text[ID_START_IDX:(ID_START_IDX + ID_LENGTH)]

    # Create a protocol "run"
    url = "http://" + robot_ip + ":31950/runs"
    headers = {
        "Opentrons-Version": "3",
        "Content-Type": "application/json"
    }
    data = {
        "data": {
            "protocolId": protocol_id
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    run_id = response.text[ID_START_IDX:(ID_START_IDX + ID_LENGTH)]

    # Start the protocol run
    url = "http://" + robot_ip + ":31950/runs/" + run_id + "/actions"
    data = {
        "data": {
            "actionType": "play"
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.status_code


def download_file(robot_ip: str, remote_path: str, local_path: str, private_key_path: str):

    # Create the SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Load the private key
    key = paramiko.RSAKey.from_private_key_file(private_key_path)

    # Connect to the remote server
    ssh.connect(hostname=ROBOT_IP, username="root", pkey=key)

    # Create SCP client
    with SCPClient(ssh.get_transport()) as scp:
        # Copy file from remote to local
        scp.get(remote_path, local_path)

    # Close the SSH connection
    ssh.close()

remote_path = "/var/lib/jupyter/notebooks/weights/weights_first.csv"
local_path = "/Users/stephenstewart/Desktop/developer/summer-2024/opentrons/protocols"
private_key_path = "/Users/stephenstewart/Desktop/developer/summer-2024/opentrons/protocols/flex_key"
download_file(ROBOT_IP, remote_path, local_path, private_key_path)
