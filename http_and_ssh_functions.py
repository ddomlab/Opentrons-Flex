"""
Functions for uploading and running a new protocol to the Flex and downloading a file from the Flex to
a local computer using scp. Make sure to change the ROBOT_IP variable if necessary.
"""

import requests
import json
import paramiko
from scp import SCPClient

# The IP of the Flex, change if necessary
ROBOT_IP = "10.154.3.53"
# The index at which a protocol/run ID starts. The ID is returned by requests.post()
ID_START_IDX = 17
# The string length of a protocol/run ID
ID_LENGTH = 36

"""
Uploads a new protocol to the Flex and runs it.
@param robot_ip is the Wired or Wireless IP of the Flex
@param file_paths is a list of the files to upload to the Flex. It should contain at least one protocol file to run and 
any amount of custom labware files needed. Each element of the list is a string containing the path to the file.
@return the status code of the post request
"""
def run_protocol(robot_ip: str, file_paths: list[str]):

    # Upload a new protocol to the Flex
    url = "http://" + robot_ip + ":31950/protocols"
    headers = {"Opentrons-Version": "3"}
    files = [("files", open(file_path, "rb")) for file_path in file_paths]
    response = requests.post(url, headers=headers, files=files)
    protocol_id = response.text[ID_START_IDX:(ID_START_IDX + ID_LENGTH)]
    # Close the files after the request
    for file in files:
        file[1].close()

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

"""
Downloads a file from the Flex to a local computer using scp.
@param robot_ip is the Wired or Wireless IP of the Flex
@param remote_path is the path to download the file from (should point to a file)
@param local_path is the path to download the file to (should point to a folder)
@param private_key_path is the path to the private key file (should point to flex_key)
"""
def download_file(robot_ip: str, remote_path: str, local_path: str, private_key_path: str):

    # Create the SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Load the private key
    key = paramiko.RSAKey.from_private_key_file(private_key_path)

    # Connect to the remote server
    ssh.connect(hostname=robot_ip, username="root", pkey=key)

    # Create SCP client
    with SCPClient(ssh.get_transport()) as scp:
        # Copy file from remote to local
        scp.get(remote_path, local_path)

    # Close the SSH connection
    ssh.close()
