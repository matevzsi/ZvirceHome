import socket
import ipaddress
import struct
from netifaces import interfaces, ifaddresses, AF_INET
    
class blind_status():
    def __init__(self, ID, source):        
        self.ID = ID
        names = ["WC", "Utility", "Kuhinja S", "Kuhinja Z", "Jedilnica Z", "Jedilnica J", "Dnevna vrata", "Delovna soba", "Tija", "Soba 2", "Spalnica", "Kopalnica"]
        self.name = names[ID]
        self.parse_status(source)

    def parse_status(self, source):
        vals = struct.unpack('IIIII', source)
        self.mode = vals[0]
        self.refPos = int(vals[1] * 100 / 600000)
        self.refAngle = int(vals[2] * 100 / 10000)
        self.pos = int(vals[3] * 100 / 600000)
        self.angle = int(vals[4] * 100 / 10000)

        #print(f"{self.ID}: Blind mode={self.mode}, ref={self.refPos}/{self.refAngle} pos={self.pos}/{self.angle}")


class poled_group():
    def __init__(self, source):
        self.ID = source[0]
        self.name = source[1:21].decode("utf-8").strip('\0')
        self.type = source[30]
        self.icon = source[31]
        self.user = None

        #print(f"Group ID={self.ID}: {self.name} {self.type}/{self.icon}")

    def parse_status(self, source):
        if self.ID != source[0]:
            return False

        self.white_warm = source[1]
        self.white_cold = source[2]
        self.rgb = list(source[3:6])
        self.override = source[6]

        #print(f"Group {self.ID} status: {self.white_warm}/{self.white_cold} / {self.rgb} O:{self.override}")
        return True

class poled_user():
    def __init__(self, source):
        self.ID = source[0]
        self.name = source[1:].decode("utf-8").strip()
        self.groups = dict()
        #print(f"User ID={self.ID}: {self.name}")
        
    

class poled_interface():
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.client_pk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.connected = False

        self.POLED_PORT_DISCOVERY = 20020    
        self.POLED_PORT_COM = 20021
        self.POLED_PORT_COM_POKEYS = 20055

        self.users = []
        self.blinds = dict()
        
        self.requestID = 0

    def discover_gateway(self, findFirst = False):
        for a in self.get_broadcast_addresses():
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP
            # Enable broadcasting mode
            client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            #print("Sending from " + a['addr'] + " via " + a['broadcast'])
            client.bind((a['addr'], self.POLED_PORT_DISCOVERY))
            client.settimeout(0.1)            
            client.sendto(b'', (a['broadcast'], self.POLED_PORT_DISCOVERY))            

            for i in range(5):
                try:
                    data, addr = client.recvfrom(1024)
                    if len(data) >= 8 and data[0] == 0x07 and data[1] == 0x3D:                        
                        #print(f"Gateway detected at {addr} (FW: {1+int(data[2]/16)}.{data[2]%16}.{data[3]})")
                        yield (addr, f"{1+int(data[2]/16)}.{data[2]%16}.{data[3]}")                                                

                except socket.timeout as t:
                    break

    def get_broadcast_addresses(self):        
        for ifaceName in interfaces():      
            addresses = ifaddresses(ifaceName).setdefault(AF_INET, [{'broadcast':None, 'addr': None}])
            if (addresses[0]['addr'] != None):    
                yield addresses[0]

    def connect(self, gateway):
        if gateway == None:
            return False
        print("Connecting to " + gateway)
        self.client.connect((gateway, self.POLED_PORT_COM))
        self.client.settimeout(0.2)
        self.client_pk.connect((gateway, self.POLED_PORT_COM_POKEYS))
        self.client_pk.settimeout(0.2)
        self.connected = True
        return True

    def disconnect(self):
        self.client.close()
        self.client_pk.close()
        return

    def prepare_command(self, cmdID, param, data):
        self.requestID = (self.requestID + 1) % 256

        req = bytearray(64)
        req[0] = 0xBB
        req[1] = 0xE6
        req[2] = cmdID
        req[3] = param
        req[6] = self.requestID
        req[7] = sum(req[0:7]) % 256
        
        l = len(data)
        if l > 0:
            req[8:8+l] = bytearray(data)
        return req

    def send_request_control_node(self, command):
        if not self.connected:
            return None
        try:
            for rety in range(3):
                #print(f"Request: {command}")
                self.client_pk.sendall(bytes(command))            
                response = self.client_pk.recv(1024)
                if response[6] == command[6]:
                    #print(f"Response: {response}")
                    return response
        except socket.timeout as t:
            print("Timeout - no response!")
            return None
        return None


    # Send request to the gateway
    def send_request(self, command, parameters):
        if not self.connected:
            return False

        req = bytearray(16)
        req[0] = command
        if parameters != None:
            L = len(parameters)
            req[1:1+L] = parameters            

        #print(f"Sending request {req}")
        self.client.sendall(bytes(req))
        return True

    # Get response from the gateway
    def get_response(self):
        if not self.connected:
            return None

        try:
            response = self.client.recv(1024)
        except socket.timeout as t:
            print("Timeout - no response!")
            return None
        return response


    def get_users(self):
        self.users = []

        if not self.connected:
            return None

        if not self.send_request(0x10, None):
            return None

        respData = self.get_response()
        if respData == None or len(respData) < 4 or respData[0] != 0x10:
            return None

        # Parse the users list
        for i in range(4, len(respData), 32):
            self.users.append(poled_user(respData[i:i+32]))
        
        # Filter the users 
        self.users = list(filter(lambda u: u.ID != 0, self.users))        

        for u in self.users:     
            i = 0
            while True:                       
                if self.get_configuration(u, i, 20) != 20:
                    break
                i += 20


    def get_configuration(self, user, group_start, group_count):

        if not self.connected:
            return None

        #print(f"Reading configuration starting at {group_start} for {group_count}")

        if not self.send_request(0x20, [ user.ID, group_count, group_start ]):
            return None

        respData = self.get_response()
        if respData == None or len(respData) < 4 or respData[0] != 0x20:
            return None

        code = respData[1]
        if code == 1:
            print("Invalid user ID")
            return None
        elif code == 2:
            print("Inactive user")
            return None
            
        if respData[2] != user.ID:
            print("Invalid user data")
            return None        

        groupsCount = int((len(respData) - 4) / 32)
        startGroup = respData[3]

        #print(f"Got configuration starting at {startGroup} for {groupsCount}")

        for i in range(startGroup, startGroup + groupsCount):    
            offset = 4 + (i - startGroup) * 32
            ng = poled_group(respData[offset:offset+32])
            user.groups[ng.ID] = ng

        return groupsCount

    def get_status(self, user):
        if not self.connected:
            return None

        if not self.send_request(0x30, [ user.ID, 0, 0 ]):
            return None

        respData = self.get_response()
        if respData == None or len(respData) < 4 or respData[0] != 0x30:
            return None
    
        code = respData[1]
        if code == 1:
            print("Invalid user ID")
            return None
        elif code == 2:
            print("Inactive user")
            return None
            
        if respData[2] != user.ID:
            print("Invalid user data")
            return None        
    
        groupsCount = int((len(respData) - 4) / 8)                

        for i in range(groupsCount):    
            offset = 4 + i * 8

            if respData[offset] in user.groups:
                user.groups[respData[offset]].parse_status(respData[offset:offset+8])
            else:
                print(f"Unknown group {respData[offset]} status")
        return groupsCount

    def set_status(self, user, group):
        if not self.connected:
            return None

        #print(f"Setting group {group.name} [{group.ID}] to O={group.override} {group.white_warm}/{group.white_cold} {group.rgb}")
        if not self.send_request(0x40, [ user.ID, group.ID, group.override,     \
                                    group.white_warm, group.white_cold,         \
                                    group.rgb[0], group.rgb[1], group.rgb[2]]):
            return None

        respData = self.get_response()
        if respData == None or len(respData) < 4 or respData[0] != 0x40:
            return None
    
        code = respData[1]
        if code == 1:
            print("Invalid user ID")
            return None
        elif code == 2:
            print("Inactive user")
            return None
            
        if respData[2] != user.ID:
            print("Invalid user data")
            return None        
    
        groupsCount = int((len(respData) - 4) / 8)        

        if groupsCount != 1:
            print("Incorrect group status")
            return None

        if not group.parse_status(respData[4:12]):
            print("Error parsing group status response")
            return None

        return group

    def set_default(self, user, group, default_value):
        if not self.connected:
            return None

        if not self.send_request(0x41, [ user.ID, group.ID, default_value]):
            return None

        return group

    def get_blind_position(self, ID):
        # Send request and get the blinds position
        resp = self.send_request_control_node(self.prepare_command(0x52, ID, []))

        if resp != None:
            if ID in self.blinds:
                self.blinds[ID].parse_status(resp[8:28])
            else:                
                self.blinds[ID] = blind_status(ID, resp[8:28])
            return self.blinds[ID]
        
        return None

    def set_blind_position(self, blind):
        p = struct.pack("II", int(blind.refPos * 600000 / 100), int(blind.refAngle * 10000 / 100))
        resp = self.send_request_control_node(self.prepare_command(0x50, blind.ID, p))        
    
    def stop_blind(self, blind):
        resp = self.send_request_control_node(self.prepare_command(0x51, blind.ID, []))        


if __name__ == "__main__":
    # Test the interface
    print("PoLED interface test...")
    pli = poled_interface()
    g = pli.discover_gateway()

    gd = next(g, None)
    if gd is not None:
        print(gd)
        result = pli.connect(gd[0][0])
        if result == False:
            print("Gateway not detected!")
        else:            
            pli.blinds[0].refAngle = 0
            pli.set_blind_position(pli.blinds[0])
            [pli.get_blind_position(i) for i in range(12)]

            pli.get_users()
            pli.get_status(pli.users[0])
            u = pli.users[0]
            g = u.groups[4]
            g.white_warm = 0
            g.white_cold = 0
            g.rgb[0] = 0
            g.override = 1
            #pli.set_status(u, g)
    else:
        print("Gateway not detected")

            

