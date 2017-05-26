#!/usr/bin/python
import time
import json
from bluetooth import *

VIRTUAL_SIMULATION = True

if not VIRTUAL_SIMULATION:
    from controllers import proximity_sensor
    from controllers import motors



NORTH = 10
EAST = 20
SOUTH = 30
WEST = 40

WAITING = 50
RUNNING = 60

MASTER = 70
SLAVE = 80

SLAVE_COUNT = 0
MASTER_BT = {
    "uuid": "00000000-0000-0000-0000-000000000001",
    "addr": "08:D4:0C:ED:C2:30"
}
SLAVE_BTS = [
    {
        "uuid": "00000000-0000-0000-0000-000000000002",
        "addr": "00:1A:7D:DA:71:14"
    }
]

# Distance limit to obstacle in cm
DISTANCE_LIMIT = 20

STEP_TIME = 2

robot = {
    "tile": None,
    "direction": NORTH,
    "status": WAITING,
    "type": MASTER,
    "uuid": "00000000-0000-0000-0000-000000000001",
    "map": {
        "tiles": [
            {
                "position": [0, 0],
                "begin": True,
                "end": False,
                "input_dir": [],
                "output_dirs": [],
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

def act(position):
    print(position)
    robot["tile"] = tile(position)
    if robot["tile"]["end"] is True:
        # notify_finish() TODO
        return True
    else:
        while len(robot["tile"]["possible_dirs"]) > 0:
            direction = robot["tile"]["possible_dirs"].pop()
            if check(direction):
                robot["tile"]["output_dirs"].append(direction)
                move()
                notify_and_wait()
                if act(next_position(position, direction)):
                    return True
            else:
                robot["tile"]["forbidden_dirs"].append(direction)

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
            "begin": True,
            "end": False,
            "input_dir": [opposite(robot["direction"])],
            "output_dirs": [],
            "possible_dirs": directions_except(opposite(robot["direction"])),
            "forbidden_dirs": []
        }
        robot["map"]["tiles"].append(tile)
    return tile


def directions_except(except_dir):
    dirs = [NORTH, WEST, EAST, SOUTH]
    dirs.remove(except_dir)
    return dirs


def opposite(direction):
    if direction is NORTH:
        return SOUTH
    elif direction is EAST:
        return WEST
    elif direction is SOUTH:
        return NORTH
    else:
        return EAST


def notify_and_wait():
    if robot["type"] is SLAVE:
        notify(MASTER_BT)
    robot["status"] = WAITING

    count = 0
    while (robot["type"] is SLAVE and count < 1) or (robot["type"] is MASTER and count < SLAVE_COUNT):
        print("Waiting for connection on RFCOMM channel %d" % port)
        client_sock, client_info = server_sock.accept()

        try:
            while True:
                data = client_sock.recv(1024)
                if len(data) == 0: break
                print("received [%s]" % data)
        except IOError:
            pass

        print("disconnected")

        client_sock.close()
        update_data(data)
        count += 1

    count = 0
    while robot["type"] is MASTER and count < SLAVE_COUNT:
        notify(MASTER_BTS[count])
        count += 1

    robot["status"] = RUNNING


def update_data(data):
    #TODO save new info
    pass


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

            sock.send(json.dumps(robot["map"])) #'{"foo": "bar"}'

            sock.close()
            break


def move(steps=1):
    return True if VIRTUAL_SIMULATION else motors.forward(steps * STEP_TIME)


def rotate(degrees):
    return True if VIRTUAL_SIMULATION else motors.rotate(degrees)


def check(direction):
    look(direction)
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


def look_east():
    if robot["direction"] is SOUTH:
        rotate(90)
    elif robot["direction"] is WEST:
        rotate(180)
    elif robot["direction"] is NORTH:
        rotate(-90)


def look_south():
    if robot["direction"] is WEST:
        rotate(90)
    elif robot["direction"] is NORTH:
        rotate(180)
    elif robot["direction"] is EAST:
        rotate(-90)


def look_west():
    if robot["direction"] is SOUTH:
        rotate(90)
    elif robot["direction"] is EAST:
        rotate(180)
    elif robot["direction"] is NORTH:
        rotate(-90)


def look(direction):
    if direction is NORTH:
        look_north()
    elif direction is EAST:
        look_east()
    elif direction is SOUTH:
        look_south()
    else:
        look_west()

act([0,0])
client_sock.close()
server_sock.close()
