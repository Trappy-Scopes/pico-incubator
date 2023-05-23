import time
import network
from machine import Pin
import secrets

# TODO
#1. Understand sockets
#2. Create basic browse functionality
#3. Serve webpage functionality


######### NOTES #########
## Return value of cyw43_wifi_link_status
#define CYW43_LINK_DOWN (0)
#define CYW43_LINK_JOIN (1)
#define CYW43_LINK_NOIP (2)
#define CYW43_LINK_UP (3)
#define CYW43_LINK_FAIL (-1)
#define CYW43_LINK_NONET (-2)
#define CYW43_LINK_BADAUTH (-3)

class Wifi:

    #1
    def __init__(self, secrets=None):
        """
        Create a Wifi object and establish connection if the secrets are shared.
        """
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        
        # Device Info
        self.mac = ubinascii.hexlify(self.WLAN().config('mac'),':').decode()

        if secrets != None:
            self.connect(secrets)
            
    def status(self):
        mac = ubinascii.hexlify(self.WLAN().config('mac'),':').decode()
        print(mac)

    #2   
    def connect(self, secrets):
        self.wlan.connect(secrets.SSID, secrets.PASSWORD)

        # Wait for connect or fail
        max_wait = 10
        while max_wait > 0:
            if self.wlan.status() < 0 or self.wlan.status() >= 3:
                break
            max_wait -= 1
            print('waiting for connection...')
            time.sleep(1)

        # Handle connection error
        if self.wlan.status() != 3:
            raise RuntimeError('Wifinetwork connection failed!')
        else:
            s = 3
            led = Pin("LED", Pin.OUT)
            while s > 0:
                s -= 1

                led.value(1)
                time.sleep(0.5)
                led.value(0)
                time.sleep(0.5)

            status = self.wlan.ifconfig()
            print( 'Connected to ' + secrets.SSID + '. ' + 'Device IP: ' + status[0])

            self.time_on_connected = time.time()
            self.ip = status[0]
            self.status = status

    #3
    def disconnect(self):
        """
        Disconnect from the current network
        """
        self.wlan.active(False)
        print("Wifi is disconnected!")

    #4
    def list_networks(self):
        """
        Lists all wifi networks in that can be detected by the pico board.
        """
        nets = self.wlan.scan()
        for net in nets:
            print(net)

    #5
    def create_socket():
        """
        Create and launch a sockets web server.
        Assumes that wifi is already connected.
        """
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

        self.socket = socket.socket()
        self.socket.bind(addr)
        self.socket.listen(1)

        print('listening on', addr)

        # Listen for connections
        while True:
            try:
                cl, addr = s.accept()
                print('client connected from', addr)
                request = cl.recv(1024)
                print(request)

                request = str(request)
                led_on = request.find('/light/on')
                led_off = request.find('/light/off')
                print( 'led on = ' + str(led_on))
                print( 'led off = ' + str(led_off))

                if led_on == 6:
                    print("led on")
                    led.value(1)
                    stateis = "LED is ON"

                if led_off == 6:
                    print("led off")
                    led.value(0)
                    stateis = "LED is OFF"

                response = html % stateis

                cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                cl.send(response)
                cl.close()

            except OSError as e:
                cl.close()
                print('connection closed')

    #6
    def browse(self, url):
        pass

if __name__ == "__main__":
    wifi = Wifi(secrets)
    time.sleep(5)
    wifi.disconnect()