#import configparser
import requests
import json
import foglight.asp

import foglight.logging



#imported from ASP
hostname   = foglight.asp.get_properties().get("hostname")
port= foglight.asp.get_properties().get("port")

#used to be apiPath="/api/v1"
apiPath= foglight.asp.get_properties().get("api_version")

logger = foglight.logging.get_logger("Foglight-Agent")


CONNECTION_URL_PREFIX = 'http://' + hostname + ':' + port + apiPath


def executeget( path , param={}):
    response = requests.get(CONNECTION_URL_PREFIX + path,
                            params=param,
                            headers={"Content-Type":"application/json",
                                     "Auth-Token":config['Global']['api.token']})
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print('request failed: ' + response.text)
    return

def executelogin( username="", password="", authToken=""):
    json_data = {}
    if not authToken:
        logger.info('Connecting to {0}. Username: {1}, password : ****** ', hostname, username)
        json_data = {"username":username, "pwd":password}
    else:
        json_data = {"authToken":authToken}
        logger.info('Connecting to {0} using Auth-Token: ' + authToken[:4]+'...', hostname)
    response = requests.post(CONNECTION_URL_PREFIX + '/security/login',
                             data=json_data,
                             headers={"Content-Type":"application/x-www-form-urlencoded"})
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print('ERROR   [Foglight-Agent]: Agent failed to authenticate to {0} failed: ' + response.text +  CONNECTION_URL_PREFIX, hostname)
    return

def executepost(path , data={}, current_token=""):
    response = requests.post(CONNECTION_URL_PREFIX + path,
                             json=data,
                             headers={'Content-Type':'application/json',
                                      "Auth-Token": current_token})
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print('ERROR   [Foglight-Agent]: Request failed: ' + response.text)
    return

