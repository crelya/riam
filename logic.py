#!/usr/bin/python
import time
import json
from bluetooth import *

import signal
import sys


if len(sys.argv) < 5:
    print("Usage: python logic.py <virtual|real> <app|noapp> <robot-id> <slave-count>")
    sys.exit(0)
else:
    if sys.argv[1] == "virtual":
        VIRTUAL_SIMULATION = True
        with open('virtual_maze.json') as data_file:
            virtual_maze = json.load(data_file)["tiles"]

        for i in range(0, len(virtual_maze)):
            tile = virtual_maze[i]
            if tile["end"] == "true":
                END_TILE = tile["position"]
                break
    elif sys.argv[1] == "real":
        VIRTUAL_SIMULATION = False
        from controllers import motors
        from controllers import proximity_sensor
        # TODO change
        END_TILE = [3,3]
    else:
        print("Usage: python logic.py <virtual|real> <app|noapp> <robot-id> <slave-count>")
        sys.exit(0)

    if sys.argv[2] == "app":

        from controllers import proximity_sensor
        APP_MODE = True
        MONITOR_COUNT = 1
    elif sys.argv[2] == "noapp":
        APP_MODE = False
        MONITOR_COUNT = 0
    else:
        print("Usage: python logic.py <virtual|real> <app|noapp> <robot-id> <slave-count>")
        sys.exit(0)

    if sys.argv[3] > 0:
        ROBOT_ID = int(sys.argv[3])
    else:
        print("Usage: python logic.py <virtual|real> <app|noapp> <robot-id> <slave-count>")
        sys.exit(0)

    SLAVE_COUNT = int(sys.argv[4])


RIAM_1 = "00:0A:3A:6F:45:91"
RIAM_2 = "00:1A:7D:DA:71:14"

NORTH = "NORTH"
EAST = "EAST"
SOUTH = "SOUTH"
WEST = "WEST"

WAITING = "waiting"
RUNNING = "running"

MASTER = "master"
SLAVE = "slave"

# SLAVE_COUNT = 1

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
DISTANCE_LIMIT = 10

STEP_TIME = 0.38
# ROBOT_ID = 1

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

app = {
    "server": None,
    "client": None
}

def init_bluetooth():

    server_sock=BluetoothSocket( RFCOMM )
    server_sock.bind(("",PORT_ANY))
    server_sock.listen(1)

    port = server_sock.getsockname()[1]


    advertise_service( server_sock, "RIAM_1",
                       service_id = robot["uuid"],
                       service_classes = [ robot["uuid"], SERIAL_PORT_CLASS ],
                       profiles = [ SERIAL_PORT_PROFILE ],
                      )
    return server_sock

app["client"] = None
app["server"] = None
# robot["tile"] = robot["map"]["tiles"][0]
def start():
    data = None
    if (robot["type"] == MASTER) and APP_MODE:
        if app["server"] is None:
            app["server"] = init_bluetooth()
        while True:
            print("[start] Waiting for connection from App")
            if app["client"] is None:
                app["client"], client_info = app["server"].accept()
                stop_advertising(app["server"])
            print(client_info)
            try:
                # while data is not None:
                data = app["client"].recv(1024)
                if len(data) == 0:
                    break
                print("START received [%s]" % data)

            except IOError as e:
                # print "I/O error({0}): {1}".format(e.errno, e.strerror)
                pass

            # print("Disconnected")

            command = json.loads(data)
            print(command)
            execute_command(command)
    else:
        # print(virtual_maze[0]["position"])
        execute_command({"tag": "ACT"})


def execute_command(command):
    tag = command["tag"]
    print("EXECUTING COMMAND %s" % tag)

    if tag == 'ACT':
        if robot["type"] == MASTER and SLAVE_COUNT > 0:
            notify_start()
        elif robot["type"] == SLAVE:
            wait_start()
        act([0,0])
    elif tag == 'MOVE_FORWARD':
        motors.forward(command["value"])
    elif tag == 'MOVE_BACKWARDS':
        motors.backwards(command["value"])
    elif tag == 'ROTATE':
        motors.rotate(command["value"])
    elif tag == 'CHECK_OBSTACLE':
        distance = proximity_sensor.check_distance()
        app["client"].send("%s\n" % json.dumps({"distance": distance}))
    elif tag == 'STOP':
        motors.stop()
    elif tag == "FREE_MODE":
        #TODO free mode
        pass
    else:
        print("I am doing nothing")


def act(position):
    last_tile = robot["tile"] if robot["tile"] is not None else get_tile(position)
    print(position)
    if not position in robot["map"]["modified"]:
        robot["map"]["modified"].append(position)
    robot["tile"] = get_tile(position)

    if robot["tile"]["end"] or robot["tile"]["position"] == END_TILE:
        # notify_finish() TODO
        print("EXIT FOUND!")
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

        robot["tile"] = last_tile
        print(last_tile["position"])
        notify_and_wait()

        return False


def next_position(position, direction):
    if direction == NORTH:
        return [position[0], position[1] + 1]
    elif direction == EAST:
        return [position[0] + 1, position[1]]
    elif direction == SOUTH:
        return [position[0], position[1] - 1]
    else:
        return [position[0] - 1, position[1]]


def get_tile(position):
    exists = False
    for i in range(0, len(robot["map"]["tiles"])):
        tile = robot["map"]["tiles"][i];
        if tile["position"][0] == position[0] and tile["position"][1] == position[1]:
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

def get_tile_idx(position):
    exists = False
    idx = -1
    for i in range(0, len(robot["map"]["tiles"])):
        tile = robot["map"]["tiles"][i];
        if tile["position"][0] == position[0] and tile["position"][1] == position[1]:
            idx = i
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
        idx = len(robot["map"]["tiles"]) - 1

    return idx



def possible_directions(input_dir):
    return [input_dir, left(input_dir), right(input_dir)]


def opposite(direction):
    if direction == NORTH:
        return SOUTH
    elif direction == EAST:
        return WEST
    elif direction == SOUTH:
        return NORTH
    else:
        return EAST

def left(direction):
    if direction == NORTH:
        return WEST
    elif direction == EAST:
        return NORTH
    elif direction == SOUTH:
        return EAST
    else:
        return SOUTH

def right(direction):
    if direction == NORTH:
        return EAST
    elif direction == EAST:
        return SOUTH
    elif direction == SOUTH:
        return WEST
    else:
        return NORTH

def notify_start():
    count = 0
    while count < SLAVE_COUNT:
        print("Notify start")
        notify(SLAVE_BTS[count], "start")
        count += 1

def wait_start():
    server_sock = init_bluetooth()
    print("Waiting for start message")
    client_sock, client_info = server_sock.accept()
    print(client_info)
    try:
        while True:
            data = client_sock.recv(1024)
            if len(data) == 0:
                break
            print("received [%s]" % data)
    except IOError as e:
        # print "I/O error({0}): {1}".format(e.errno, e.strerror)
        pass

    print("disconnected")

    client_sock.close()
    server_sock.close()

def notify_and_wait():
    if robot["type"] == SLAVE:
        print("[notify_and_wait - %d] Sending info to master" % ROBOT_ID)
        notify(MASTER_BT, modified_map())
    robot["status"] = WAITING

    count = 0 #TODO modify with unique array of ids to avoid duplication
    server_sock = init_bluetooth()
    while (robot["type"] == SLAVE and count < 1) or (robot["type"] == MASTER and count < SLAVE_COUNT):
        print("[notify_and_wait - %d] Waiting for info update" % ROBOT_ID)
        client_sock, client_info = server_sock.accept()
        print(client_info)
        try:
            while True:
                data = client_sock.recv(1024)
                if len(data) == 0:
                    break
                # print("received [%s]" % data)
        except IOError as e:
            # print "I/O error({0}): {1}".format(e.errno, e.strerror)
            pass

        print("[notify_and_wait - %d] Disconnected" % ROBOT_ID)

        client_sock.close()
        update_data(json.loads(data))
        count += 1
    server_sock.close()

    if robot["type"] == MASTER:
        notify_data = modified_map()
        if MONITOR_COUNT > 0:
            print("[notify_and_wait - %d] Sending info to monitor" % ROBOT_ID)
            app["client"].send("%s\n" % json.dumps(notify_data))

        count = 0
        while count < SLAVE_COUNT:
            print("[notify_and_wait - %d] Sending info to slave" % ROBOT_ID)
            notify(SLAVE_BTS[count], notify_data)
            count += 1

    clear_modified()
    robot["status"] = RUNNING


def update_data(data):
    for new_tile in data:
        idx = get_tile_idx(new_tile["position"])
        robot["map"]["tiles"][idx]["end"] = robot["map"]["tiles"][idx]["end"] or new_tile["end"]
        robot["map"]["tiles"][idx]["input_dir"] = new_tile["input_dir"]
        for direction in new_tile["output_dirs"]:
            if not direction in robot["map"]["tiles"][idx]["output_dirs"]:
                robot["map"]["tiles"][idx]["output_dirs"].append(direction)
        cpy = robot["map"]["tiles"][idx]["possible_dirs"][:]
        for direction in robot["map"]["tiles"][idx]["possible_dirs"]:
            if not direction in new_tile["possible_dirs"]:
                cpy.remove(direction)
        robot["map"]["tiles"][idx]["possible_dirs"] = cpy
        for direction in new_tile["forbidden_dirs"]:
            if not direction in robot["map"]["tiles"][idx]["forbidden_dirs"]:
                robot["map"]["tiles"][idx]["forbidden_dirs"].append(direction)
        if not robot["map"]["tiles"][idx]["position"] in robot["map"]["modified"]:
            robot["map"]["modified"].append(robot["map"]["tiles"][idx]["position"])
    # print(robot["map"]["tiles"])



def clear_modified():
    robot["map"]["modified"] = []


def modified_map():
    modified_map = []
    for position in robot["map"]["modified"]:
        modified_map.append(get_tile(position))
    return modified_map

def notify(bt_info, data):
    uuid = bt_info["uuid"]
    addr = bt_info["addr"]
    while True:
        service_matches = find_service(uuid=uuid, address=addr)

        if len(service_matches) == 0:
            print("[notify - %d] Couldn't notify. Retrying..." % ROBOT_ID)
            time.sleep(0.2)
        else:

            first_match = service_matches[0]
            port = first_match["port"]
            name = first_match["name"]
            host = first_match["host"]

            print("[notify - %d] connecting to \"%s\" on %s" % (ROBOT_ID, name, host))

            # Create the client socket
            sock=BluetoothSocket( RFCOMM )
            sock.connect((host, port))

            print("[notify - %d] Sending data" % ROBOT_ID)
            sock.send(json.dumps(data)) #'{"foo": "bar"}'

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
    #TODO gpio check if front == blocked
    if VIRTUAL_SIMULATION:
        for i in range(0, len(virtual_maze)):
            tile = virtual_maze[i]
            if tile["position"][0] == robot["tile"]["position"][0] and tile["position"][1] == robot["tile"]["position"][1]:
                return True if robot["direction"] in tile["exits"] else False
        return False
    else:
        obstacle_distance = proximity_sensor.check_distance()
        return obstacle_distance > DISTANCE_LIMIT



def look_north():
    if robot["direction"] == EAST:
        rotate(90)
    elif robot["direction"] == SOUTH:
        rotate(180)
    elif robot["direction"] == WEST:
        rotate(-90)
    robot["direction"] = NORTH


def look_east():
    if robot["direction"] == SOUTH:
        rotate(90)
    elif robot["direction"] == WEST:
        rotate(180)
    elif robot["direction"] == NORTH:
        rotate(-90)
    robot["direction"] = EAST


def look_south():
    if robot["direction"] == WEST:
        rotate(90)
    elif robot["direction"] == NORTH:
        rotate(180)
    elif robot["direction"] == EAST:
        rotate(-90)
    robot["direction"] = SOUTH


def look_west():
    if robot["direction"] == SOUTH:
        rotate(90)
    elif robot["direction"] == EAST:
        rotate(180)
    elif robot["direction"] == NORTH:
        rotate(-90)
    robot["direction"] = WEST


def look_at(direction):
    if direction == NORTH:
        look_north()
    elif direction == EAST:
        look_east()
    elif direction == SOUTH:
        look_south()
    else:
        look_west()

def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    if not VIRTUAL_SIMULATION:
        motors.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
# print('Press Ctrl+C')
# signal.pause()

start()

if MONITOR_COUNT > 0:
    app["client"].close()
    app["server"].close()
# act([0,0])
# notify(MONITOR_BT)
# server_sock.close()

print("Execution terminated")
