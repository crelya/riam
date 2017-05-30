#!/usr/bin/python
import time
import json
from bluetooth import *

VIRTUAL_SIMULATION = True

if not VIRTUAL_SIMULATION:
    from controllers import proximity_sensor
    from controllers import motors


RIAM_1 = "00:0A:3A:6F:45:91"
RIAM_2 = "00:1A:7D:DA:71:14"
MEUBUNTU = "08:D4:0C:ED:C2:30"
NORTH = "north"
EAST = "east"
SOUTH = "south"
WEST = "west"

WAITING = "waiting"
RUNNING = "running"

MASTER = "master"
SLAVE = "slave"

SLAVE_COUNT = 1
MASTER_BT = {
    "uuid": "00000000-0000-0000-0000-000000000001",
    "addr": RIAM_1
}
SLAVE_BTS = [
    {
        "uuid": "00000000-0000-0000-0000-000000000002",
        "addr": RIAM_2
    }
]

MONITOR_BT = {
    "uuid": "0003",
    "addr": "C0:EE:FB:24:B7:B8"
}

# Distance limit to obstacle in cm
DISTANCE_LIMIT = 20

STEP_TIME = 2
ROBOT_ID = 1

robot = {
    "id": ROBOT_ID,
    "tile": None,
    "direction": NORTH,
    "status": WAITING,
    "type": MASTER if ROBOT_ID == 1 else SLAVE,
    "uuid": "00000000-0000-0000-0000-00000000000%d" % (ROBOT_ID),
    "map": {
        "modified": [],
        "tiles": [
            {
                "position": [0, 0],
                "begin": True,
                "end": False,
                "input_dir": [],
                "output_dirs": [],
                "taken_dirs": [],
                "possible_dirs": [NORTH],
                "forbidden_dirs": [WEST, SOUTH, EAST]
            }
        ]
    }
}

server_sock=BluetoothSocket( RFCOMM )
server_sock.bind(("",PORT_ANY))
server_sock.listen(1)

port = server_sock.getsockname()[1]


advertise_service( server_sock, "RIAM_1",
                   service_id = robot["uuid"],
                   service_classes = [ robot["uuid"], SERIAL_PORT_CLASS ],
                   profiles = [ SERIAL_PORT_PROFILE ],
                  )


# robot["tile"] = robot["map"]["tiles"][0]
def start():
    data = None
    if (robot["type"] is MASTER):
        while True:
            print("Waiting for connection on RFCOMM channel %d" % port)
            client_sock, client_info = server_sock.accept()
            print(client_info)
            try:
                # while data is not None:
                data = client_sock.recv(1024)
                if len(data) == 0:
                    break
                print("received [%s]" % data)

            except IOError as e:
                print "I/O error({0}): {1}".format(e.errno, e.strerror)

            print("disconnected")

            client_sock.close()
            command = json.loads(data)
            print(command)
            execute_command(command)
    else:
        execute_command({"tag": "ACT"})


def execute_command(command):
    tag = command["tag"]
    print("EXECUTING COMMAND %s" % tag)

    if tag == 'ACT':
        act([0,0])
    elif tag == 'MOVE_FORWARD':
        motors.forward(command["value"])
    elif tag == 'MOVE_BACKWARDS':
        motors.backwards(command["value"])
    elif tag == 'CHECK_OBSTACLE':
        proximity_sensor.check_distance()
        #TODO send distance to monitor
    else:
        print("I am doing nothing")


def act(position):
    print(position)
    if not position in robot["map"]["modified"]:
        robot["map"]["modified"].append(position)
    robot["tile"] = tile(position)
    if robot["tile"]["end"] is True:
        # notify_finish() TODO
        return True
    else:
        while len(robot["map"]["tiles"]) < robot["id"]:
            print(len(robot["map"]["tiles"]))
            notify_and_wait()
        while len(robot["tile"]["possible_dirs"]) > 0:
            direction = robot["tile"]["possible_dirs"].pop(0)
            if check(direction):
                robot["tile"]["output_dirs"].append(direction)
                robot["tile"]["taken_dirs"].append(direction)
                move()

                notify_and_wait()
                if act(next_position(position, direction)):
                    return True
            else:
                robot["tile"]["forbidden_dirs"].append(direction)
        for output_dir in robot["tile"]["output_dirs"]:
            if not output_dir in robot["tile"]["taken_dirs"]:
                if check(output_dir):
                    robot["tile"]["taken_dirs"].append(output_dir)
                    move()
                    notify_and_wait()
                    if act(next_position(position, output_dir)):
                        return True
                    # TODO add forbidden time


        look_at(robot["tile"]["input_dir"])
        move()
        notify_and_wait()
        return False


def next_position(position, direction):
    if direction is NORTH:
        return [position[0], position[1] + 1]
    elif direction is EAST:
        return [position[0] + 1, position[1]]
    elif direction is SOUTH:
        return [position[0], position[1] - 1]
    else:
        return [position[0] - 1, position[1]]


def tile(position):
    exists = False
    for i in range(0, len(robot["map"]["tiles"])):
        tile = robot["map"]["tiles"][i];
        if tile["position"][0] is position[0] and tile["position"][1] is position[1]:
            exists = True
            break


    if not exists:
        tile = {
            "position": position,
            "begin": False,
            "end": False,
            "input_dir": [opposite(robot["direction"])],
            "output_dirs": [],
            "taken_dirs": [],
            "possible_dirs": possible_directions(robot["direction"]),
            "forbidden_dirs": []
        }
        robot["map"]["tiles"].append(tile)
    return tile


def possible_directions(input_dir):
    return [input_dir, left(input_dir), right(input_dir)]


def opposite(direction):
    if direction is NORTH:
        return SOUTH
    elif direction is EAST:
        return WEST
    elif direction is SOUTH:
        return NORTH
    else:
        return EAST

def left(direction):
    if direction is NORTH:
        return WEST
    elif direction is EAST:
        return NORTH
    elif direction is SOUTH:
        return EAST
    else:
        return SOUTH

def right(direction):
    if direction is NORTH:
        return EAST
    elif direction is EAST:
        return SOUTH
    elif direction is SOUTH:
        return WEST
    else:
        return NORTH


def notify_and_wait():
    if robot["type"] is SLAVE:
        notify(MASTER_BT)
    robot["status"] = WAITING

    count = 0 #TODO modify with unique array of ids to avoid duplication
    while (robot["type"] is SLAVE and count < 1) or (robot["type"] is MASTER and count < SLAVE_COUNT):
        print("Waiting for connection on RFCOMM channel %d" % port)
        client_sock, client_info = server_sock.accept()
        print(client_info)
        try:
            while True:
                data = client_sock.recv(1024)
                if len(data) == 0:
                    break
                print("received [%s]" % data)
        except IOError as e:
            print "I/O error({0}): {1}".format(e.errno, e.strerror)

        print("disconnected")

        client_sock.close()
        update_data(json.loads(data))
        count += 1

    count = 0
    while robot["type"] is MASTER and count < SLAVE_COUNT:
        notify(SLAVE_BTS[count])
        count += 1

    clear_modified()
    robot["status"] = RUNNING


def update_data(data):
    for new_tile in data:
        t = tile(new_tile["position"])
        t["end"] = t["end"] or new_tile["end"]
        t["input_dir"] = new_tile["input_dir"]
        for direction in new_tile["output_dirs"]:
            if not direction in t["output_dirs"]:
                t["output_dirs"].append(direction)
        for direction in t["possible_dirs"]:
            if not direction in new_tile["possible_dirs"]:
                t["possible_dirs"].remove(direction)
        for direction in new_tile["forbidden_dirs"]:
            if not direction in t["forbidden_dirs"]:
                t["forbidden_dirs"].append(direction)
        if not t["position"] in robot["map"]["modified"]:
            robot["map"]["modified"].append(t["position"])

def clear_modified():
    robot["map"]["modified"] = []


def notify(bt_info):
    uuid = bt_info["uuid"]
    addr = bt_info["addr"]
    while True:
        service_matches = find_service(uuid=uuid, address=addr)

        if len(service_matches) == 0:
            print("Couldn't notify. Retrying...")
            time.sleep(0.2)
        else:

            first_match = service_matches[0]
            port = first_match["port"]
            name = first_match["name"]
            host = first_match["host"]

            print("connecting to \"%s\" on %s" % (name, host))

            # Create the client socket
            sock=BluetoothSocket( RFCOMM )
            sock.connect((host, port))

            modified_map = []
            for position in robot["map"]["modified"]:
                modified_map.append(tile(position))

            sock.send(json.dumps(modified_map)) #'{"foo": "bar"}'

            sock.close()
            break


def move(steps=1):
    return True if VIRTUAL_SIMULATION else motors.forward(steps * STEP_TIME)


def rotate(degrees):
    return True if VIRTUAL_SIMULATION else motors.rotate(degrees)


def check(direction):
    look_at(direction)
    return path_clear()


def path_clear():

    #TODO gpio check if front is blocked
    # obstacle_distance = proximity_sensor.check_distance()
    # return obstacle_distance < DISTANCE_LIMIT
    return True


def look_north():
    if robot["direction"] is EAST:
        rotate(90)
    elif robot["direction"] is SOUTH:
        rotate(180)
    elif robot["direction"] is WEST:
        rotate(-90)
    robot["direction"] = NORTH


def look_east():
    if robot["direction"] is SOUTH:
        rotate(90)
    elif robot["direction"] is WEST:
        rotate(180)
    elif robot["direction"] is NORTH:
        rotate(-90)
    robot["direction"] = EAST


def look_south():
    if robot["direction"] is WEST:
        rotate(90)
    elif robot["direction"] is NORTH:
        rotate(180)
    elif robot["direction"] is EAST:
        rotate(-90)
    robot["direction"] = SOUTH


def look_west():
    if robot["direction"] is SOUTH:
        rotate(90)
    elif robot["direction"] is EAST:
        rotate(180)
    elif robot["direction"] is NORTH:
        rotate(-90)
    robot["direction"] = WEST


def look_at(direction):
    if direction is NORTH:
        look_north()
    elif direction is EAST:
        look_east()
    elif direction is SOUTH:
        look_south()
    else:
        look_west()

start()

# notify(MONITOR_BT)
server_sock.close()

print("Execution terminated")
