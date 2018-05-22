# This file subscribes to studentreport/# 
# and attempts to parse the results and provides averages, min and max values
#
# Written by Sebastian Van Den Dungen. u5561028

import paho.mqtt.client as mqtt
import sys
import time


#print("This is the name of the script: ", sys.argv[0])
#print("Number of arguments: ", len(sys.argv))
#print("The arguments are: " , str(sys.argv))

auth = {
    'username': '3310student',
    'password': 'comp3310'
}

data = {
    0: {
        # Results handled in iterations
        "rec": 0,
        "latest": 0,
        "missing" : [],
        "received": [],
        "dupes": 0,
        "outoforder": 0,
        # Results carried over between iterations
        "recv" : 0,
        "loss" : 0,
        "ooo" : 0,
        "dupe": 0
    },
    1: {
        # Results handled in iterations
        "rec": 0,
        "latest": 0,
        "missing" : [],
        "received": [],
        "dupes": 0,
        "outoforder": 0,
        # Results carried over between iterations
        "recv" : 0,
        "loss" : 0,
        "ooo" : 0,
        "dupe": 0
    },
    2: {
        # Results handled in iterations
        "rec": 0,
        "latest": 0,
        "missing" : [],
        "received": [],
        "dupes": 0,
        "outoforder": 0,
        # Results carried over between iterations
        "recv" : 0,
        "loss" : 0,
        "ooo" : 0,
        "dupe": 0
    }
}


# NOTE: rc values correspond as follows:
rcval = {  
    0: "Connection successful",
    1: "Connection refused - incorrect protocol version",
    2: "Connection refused - invalid client identifier",
    3: "Connection refused - server unavailable",
    4: "Connection refused - bad username or password",
    5: "Connection refused - not authorised"
    #  6-255: Currently unused.
}


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("[DEBUG] %s" % rcval[rc]) # print the result of the connection attempt

    if (rc == 0):
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.

        #Subscribe to topics here.
        #Subscribe all at once and sort it out as the messages come in
        print("[DEBUG] subscribing")
        client.subscribe("counter/fast/q0", 0)
        client.subscribe("counter/fast/q1", 1)
        client.subscribe("counter/fast/q2", 2)
    else:
        print("[FATAL] Did not connect, cannot subscribe")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    payload = str(msg.payload)
    #print(msg.topic+" : " + payload)

    try:
        number = int(payload[2:-1])

        QoS = int(msg.topic[len(msg.topic)-1:])
        
        dataSet = data[QoS]
        #Assume received count includes duplicates
        dataSet["rec"] += 1
        # check if after last recieved message, or first message.
        if (dataSet["latest"] == 0 or number == 1):
            # Catch case when we are starting.
            # Catch edge case when circling around, probably wont come up but w/e
            dataSet["latest"] = number
        elif (dataSet["latest"] > number):
            # Message is before most recently received message
            if (number in dataSet["missing"]):
                dataSet["missing"].remove(number)
                dataSet["outoforder"] += 1
        elif (dataSet["latest"] < number):
            # Skipping vals, we missed some messages
            for num in range(dataSet["latest"]+1, number):
                # Interpolate missing messages. Check if they have already been received.
                if (number not in dataSet["received"]): 
                    # Haven't received the message yet, add it to the list of messages we are waiting for
                    dataSet["missing"].append(num)

            dataSet["latest"] = number
        
        if (number in dataSet["received"]):
            #Count the dupes
            dataSet["dupes"] += 1
        else:
            dataSet["received"].append(number)
        
        data[QoS] = dataSet
    except ValueError:
        print("[WARN]  Unexpected string: '%s'" % payload)

# Initiate client with correct ID
client = mqtt.Client("3310-u5561028")


#sub.callback(on_message, 
#             "counter/fast/q1", 
#             qos=1, 
#             userdata=None, 
#             hostname="3310exp.hopto.org", 
#             port=1883, 
#             client_id="3310-u5561028", 
#             keepalive=60, 
#             will=None, 
#             auth=auth, 
#             tls=None, 
#             protocol=mqtt.MQTTv311)

#pub.single("studentreport/u5561028/test",
#               payload="this was a triumph",
#               retain = True,
#               qos=2,
#               hostname="3310exp.hopto.org",
#               port = 1883,
#               client_id="3310-u5561028",
#               auth=auth)

client.username_pw_set(auth['username'], auth['password'])

client.on_connect = on_connect
client.on_message = on_message

client.connect("3310exp.hopto.org", port=1883, keepalive=60)

init = int(time.time())
print("[DEBUG] executing")
for iter in range(1, 11):
    # Collect data every minute for 10 minutes.

    client.loop_start()
    end = time.time()
    start = time.time()

    print("[DEBUG] starting set #" + str(iter))
    while (end - start < 60): 
        # Wait 60 seconds before collating data
        end = time.time()


    # Adjust stored data
    # number of items received over the minute
    # Assuming rate = messages/min.
    client.loop_stop()
    for id in (0, 1, 2):
        if (data[id]["recv"] < data[id]["rec"]):
            data[id]["recv"] = data[id]["rec"]

        #Assume if still missing then was lost
        if (data[id]["loss"] < len(data[id]["missing"])):
            data[id]["loss"] = len(data[id]["missing"])
        
        if (data[id]["dupe"] < data[id]["dupes"]):
            data[id]["dupe"] = data[id]["dupes"]

        if (data[id]["ooo"] < data[id]["outoforder"]):
            data[id]["ooo"] = data[id]["outoforder"]

        # Reset data cache
        data[id]["rec"] = 0
        data[id]["latest"] = 0
        data[id]["dupes"] = 0
        data[id]["outoforder"] = 0
        data[id]["missing"] = []
        data[id]["received"] = []

print("[DEBUG] unsubscribing")
client.unsubscribe("counter/fast/q0")
client.unsubscribe("counter/fast/q1")
client.unsubscribe("counter/fast/q2")

print("[INFO]  publishing Results")
baseTopic = "studentreport/u5561028/"

client.loop_start()
client.publish(baseTopic + "language", payload="python", qos=2, retain=True).wait_for_publish()
client.publish(baseTopic + "timestamp", payload=init, qos=2, retain=True).wait_for_publish()
# Results calculated over 1 minute interval, 
for id in (0, 1, 2):
    print("[INFO]  Results for QoS " + str(id))
    # Best receive rate over 1 min
    client.publish(baseTopic + str(init) + "/"+str(id)+"/recv", payload=data[id]["recv"], qos=2, retain=True).wait_for_publish()
    print("[INFO]   recv: "+str(data[id]["recv"]))
    # Worst loss rate over 1 min
    client.publish(baseTopic + str(init) + "/"+str(id)+"/loss", payload=data[id]["loss"], qos=2, retain=True).wait_for_publish()
    print("[INFO]   loss: "+str(data[id]["loss"]))
    # Worst dupe rate over 1 min
    client.publish(baseTopic + str(init) + "/"+str(id)+"/dupe", payload=data[id]["dupe"], qos=2, retain=True).wait_for_publish()
    print("[INFO]   dupe: "+str(data[id]["dupe"]))
    # Worst Out of order rate over 1 min
    client.publish(baseTopic + str(init) + "/"+str(id)+"/ooo", payload=data[id]["ooo"], qos=2, retain=True).wait_for_publish()
    print("[INFO]    ooo: "+str(data[id]["ooo"]))

client.loop_stop()

print("[DEBUG] done")

client.disconnect()
