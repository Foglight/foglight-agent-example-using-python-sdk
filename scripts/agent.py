# Importing foglight modules
import foglight.asp
import foglight.logging
import foglight.model

#import other libraries.
import time
import traceback
import requests.packages.urllib3

#import from __init__ module, which connects to Foglight API
from __init__ import executeget
from __init__ import executepost
from __init__ import executelogin


#ASP import
ASP_authToken = foglight.asp.get_properties().get("authToken")
ASP_user = foglight.asp.get_properties().get("username")
ASP_passw = foglight.asp.get_properties().get("password")
hostname   = foglight.asp.get_properties().get("hostname")


# All instances of this agent use this as part of their model name
# This is not required, but does help when working with the submitted
# data
MODEL_NAME_ROOT = "FoglightAgent"

# The model name *must* be unique to this one instance of this agent.
# Agents with the same model name will end up submitting their data to
# the same topology object. In this case, we'll use the host name
# to differentiate agents.
MODEL_NAME = MODEL_NAME_ROOT + "-" + hostname

# Set up a logger for this Agent.
logger = foglight.logging.get_logger("Foglight-Agent")

def collect_inventory(token):
    logger.info("Starting inventory collection")
    logger.info("Adding list of items we will collect from FMS")

    update = None
    try:
        # foglight.topology.begin_update() will throw an exception if we are unable
        # to update, so we don't need to check the value of update before we proceed.

        update = foglight.topology.begin_update()
        model = foglight.model.DataModel(MODEL_NAME, topology_update=update)

        # The container for the main object in this agent's namespace. To this,
        # we will add sub containers if needed.
        container = model.get_container("FMS instance")

        #Get fms properties
        response=executepost("/topology/query", data={"queryText":"!CatalystServer"}, current_token=token)

        logger.info("Adding container for FMS.")
        
        # Add a new container for this. This will find an existing container
        # with the same name, or create one if needed
        fms_instance = container.get_container(response['data'][0]['uniqueId'])
        logger.info("FMS instance {0}, uniqueId will be used as container".format(response['data'][0]['uniqueId']))


        # Since we have to have the structure of the data we're going to submit laid out in
        # advance, we have to prepare a place for all the properties, metrics, and observations
        # that will be required. This must be done during the inventory phase, even if
        # the actual data will not be submitted during the performance phase.
        logger.info("Preparing items...")
        fms_instance.prepare_item("build")
        fms_instance.prepare_item("agent_count")
        fms_instance.prepare_item("uuid")

        # Here is the FMS instance information.
        fms_instance.set_property_string("build", response["data"][0]["properties"]["build"])
        fms_instance.set_property_string("uuid", response['data'][0]['uniqueId'])
        logger.info("FMS release {0},  uuid : {1}".format(response["data"][0]["properties"]["build"],response['data'][0]['uniqueId'] ))

        #Getting database properties
        response=executepost("/topology/query", data={"queryText":"!CatalystDatabase"}, current_token=token)

        # Important: Decided to report database info under Existing fms_instance container.
        #database_instance = container.get_container(response['data'][0]['properties']['name'])
        #logger.info("Database instance {0}, name will be used as container".format(response['data'][0]['properties']['name']))

        logger.info("Preparing DB items...")
        fms_instance.prepare_item("db_name")
        fms_instance.prepare_item("db_type")
        fms_instance.prepare_item("db_uuid")
        fms_instance.prepare_item("db_latency_min")
        fms_instance.prepare_item("db_latency_max")
        fms_instance.prepare_item("db_latency_avg")

        # Database instance information.
        fms_instance.set_property_string("db_name", response['data'][0]['properties']['name'])
        fms_instance.set_property_string("db_type", response['data'][0]['properties']['databaseType'])
        fms_instance.set_property_string("db_uuid",  response['data'][0]['properties']['status']['uniqueId'])

        # End the update by submitting the DataModel.
        model.submit()
        update = None
    finally:
        if update:
            # The update is ended when abort() is called.
            update.abort()

    logger.info("Inventory collection completed and submitted")
def collect_performance(token):
    logger.info("Starting performance collection")

    update = foglight.topology.begin_data_collection()
    model = foglight.model.DataModel(MODEL_NAME, data_update=update)
    # foglight.topology.begin_update() will throw an exception if we are unable
    # to update, so we don't need to check the value of update before we proceed.

    # The container for the main object in this agent's namespace. To this,
    # we will add sub containers if needed.
    container = model.get_container("FMS instance")

    #Get fms properties
    response=executepost("/topology/query", data={"queryText":"!CatalystServer"}, current_token=token)

    logger.info("Adding container for FMS.")

    # Add a new container for this. This will find an existing container
    # with the same name, or create one if needed
    fms_instance = container.get_container(response['data'][0]['uniqueId'])
    logger.info("FMS instance {0}, uniqueId will be used as container".format(response['data'][0]['uniqueId']))

    #setting agent count metric.
    fms_instance.set_metric("agent_count", int(response['data'][0]['properties']['lastStampedAgentCount']))
    logger.info("Number of agents: {0}".format(response['data'][0]['properties']['lastStampedAgentCount']))

    #Getting database DB_UUID
    response=executepost("/topology/query", data={"queryText":"!CatalystDatabase"}, current_token=token)
    DB_UUID = response['data'][0]['properties']['status']['uniqueId']
    logger.info("Database uniqueId: {0}".format(response['data'][0]['properties']['status']['uniqueId']))

    #Database latency min max avg
    current_time=int(round(time.time() * 1000))
    start_time= current_time-600000 #look at the last 10 min.
    logger.info("Querying DB latency from {0} to {1}".format(start_time, current_time))

    data_to_execute={"includes":[{"ids":[DB_UUID],"observationName":"databaseLatency"}],"startTime":start_time,"endTime":current_time,"numberOfValue":1,"retrievalType":"AGGREGATE"}
    response = executepost("/topology/batchQuery", data=data_to_execute, current_token=token)

    #debugging
    #print response['data']['aggregateValues'][DB_UUID+':databaseLatency']

    fms_instance.set_metric("db_latency_min", float(response['data']['aggregateValues'][DB_UUID+':databaseLatency']['value']['min']))
    fms_instance.set_metric("db_latency_max", float(response['data']['aggregateValues'][DB_UUID+':databaseLatency']['value']['max']))
    fms_instance.set_metric("db_latency_avg", float(response['data']['aggregateValues'][DB_UUID+':databaseLatency']['value']['avg']))

    #logger.info("DB latency (min/max/avg) = {0}, {1}, {2}".format(response['data']['aggregateValues'][DB_UUID +':databaseLatency']['value']['min'],response['data']['aggregateValues'][DB_UUID +':databaseLatency']['value']['max'],response['data']['aggregateValues'][DB_UUID +':databaseLatency']['value']['avg']))

    # End the data collection by submitting the DataModel. If the data collection is not
    # successful, we don't need to abort it; The data will be automatically discarded.
    model.submit()
    logger.info("Performance collection completed and submitted")

if __name__ == "__main__":
    try:

        #Disable SSL warnings and certificate checking
        requests.packages.urllib3.disable_warnings()
        foglight.utils.disable_ssl_cert_checking()

        # Establish a REST session to FMS, get token.
        response=executelogin(username=ASP_user,  password=ASP_passw, authToken=ASP_authToken)
        temp_token=response['data']['token']
        logger.info("Received a temp token from FMS : "+ temp_token[:4]+'...')

        frequencies = foglight.asp.get_collector_frequencies()

        # Default collection frequency, in case we are not able to figure it out
        collector_seconds = 300

        # Find this script in the list of collection frequencies.
        # The keys might be slightly different depending on whether or not
        # the script is run by the Agent Manager or Script Harness
        for k in frequencies.keys():
            if k.endswith("agent.py"):
                collector_seconds = frequencies[k]
                break

        # We want inventory every 5 collection cycles
        inventory = (collector_seconds * 5)
        tracker = foglight.model.CollectionTracker(inventory / 60)
        if tracker.is_inventory_recommended():
            logger.info("Inventory collection required")
            collect_inventory(temp_token)
            tracker.record_inventory()
        else:
            collect_performance(temp_token)
            tracker.record_performance()


    except:
         logger.error("Could not perform basic agent initialization")
         logger.error(traceback.format_exc())
