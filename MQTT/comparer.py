# This file subscribes to studentreport/# 
# and attempts to parse the results and provides averages, min and max values
#
# Written by Sebastian Van Den Dungen. u5561028

import paho.mqtt.client as mqtt
import sys
import time

auth = {
    'username': '3310student',
    'password': 'comp3310'
}

data = {
    0: {
        # Summed results
        "recv" : 0,
        "max-r" : 0,
        "min-r" : 10000000000000000,
        "loss" : 0,
        "max-l" : 0,
        "min-l" : 10000000000000000,
        "ooo" : 0,
        "max-o" : 0,
        "min-o" : 10000000000000000,
        "dupe": 0,
        "max-d" : 0,
        "min-d" : 10000000000000000,
        # number of results analysed
        "num": 0
    },
    1: {
        # Summed results
        "recv" : 0,
        "max-r" : 0,
        "min-r" : 10000000000000000,
        "loss" : 0,
        "max-l" : 0,
        "min-l" : 10000000000000000,
        "ooo" : 0,
        "max-o" : 0,
        "min-o" : 10000000000000000,
        "dupe": 0,
        "max-d" : 0,
        "min-d" : 10000000000000000,
        # number of results analysed
        "num": 0
    },
    2: {
        # Summed results
        "recv" : 0,
        "max-r" : 0,
        "min-r" : 10000000000000000,
        "loss" : 0,
        "max-l" : 0,
        "min-l" : 10000000000000000,
        "ooo" : 0,
        "max-o" : 0,
        "min-o" : 10000000000000000,
        "dupe": 0,
        "max-d" : 0,
        "min-d" : 10000000000000000,
        # number of results analysed
        "num": 0
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
        client.subscribe("studentreport/#", 2)
    else:
        print("[FATAL] Did not connect, cannot subscribe")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    payload = str(msg.payload)
    #print(msg.topic+" : " + payload)

    try:
        number = int(float(payload[2:-1]))
        for id in (0, 1, 2):
            if (msg.topic.endswith(str(id) + "/recv")):
                data[id]["recv"] += number
                if (data[id]["max-r"] < number):
                    data[id]["max-r"] = number
                if (data[id]["min-r"] > number):
                    data[id]["min-r"] = number
                data[id]["num"] += 1
            if (msg.topic.endswith(str(id) + "/loss")):
                data[id]["loss"] += number
                if (data[id]["max-l"] < number):
                    data[id]["max-l"] = number
                if (data[id]["min-l"] > number):
                    data[id]["min-l"] = number
                data[id]["num"] += 1
            if (msg.topic.endswith(str(id) + "/dupe")):
                data[id]["dupe"] += number
                if (data[id]["max-d"] < number):
                    data[id]["max-d"] = number
                if (data[id]["min-d"] > number):
                    data[id]["min-d"] = number
                data[id]["num"] += 1
            if (msg.topic.endswith(str(id) + "/ooo")):
                data[id]["ooo"] += number
                if (data[id]["max-o"] < number):
                    data[id]["max-o"] = number
                if (data[id]["min-o"] > number):
                    data[id]["min-o"] = number
                data[id]["num"] += 1

    except ValueError:
        print("[WARN]  Unexpected string: '%s'" % payload[2:-1])

# Initiate client with correct ID
client = mqtt.Client("3310-u5561028")

client.username_pw_set(auth['username'], auth['password'])

client.on_connect = on_connect
client.on_message = on_message

client.connect("3310exp.hopto.org", port=1883, keepalive=60)

print("[DEBUG] executing")

start = time.time()
end = time.time()
while (end - start < 60): 
    # Wait 60 seconds before collating data
    end = time.time()
    client.loop()


print("[DEBUG] unsubscribing")
client.unsubscribe("studentreport/#")

print("[INFO]  Results")

client.loop_start()
# Results calculated over 1 minute interval, 
for id in (0, 1, 2):
    print("[INFO]  Results for QoS " + str(id) + " # results analysed: " + str(data[id]["num"]))
    # Best receive rate over 1 min
    print("[INFO]   avg recv: %s Max: %i Min: %i" % (str(data[id]["recv"] / data[id]["num"]), data[id]["max-r"], data[id]["min-r"]))
    # Worst loss rate over 1 min
    print("[INFO]   avg loss: %s Max: %i Min: %i" % (str(data[id]["loss"] / data[id]["num"]), data[id]["max-l"], data[id]["min-l"]))
    # Worst dupe rate over 1 min
    print("[INFO]   avg recv: %s Max: %i Min: %i" % (str(data[id]["dupe"] / data[id]["num"]), data[id]["max-d"], data[id]["min-d"]))
    # Worst Out of order rate over 1 min
    print("[INFO]   avg recv: %s Max: %i Min: %i" % (str(data[id]["ooo"] / data[id]["num"]), data[id]["max-o"], data[id]["min-o"]))

client.loop_stop()

print("[DEBUG] done")

client.disconnect()
