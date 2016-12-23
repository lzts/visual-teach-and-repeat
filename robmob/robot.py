import collections
import json
import _thread
import urllib.parse
import websocket
import time
from robmob.commands import CommandPublisher, LinearMovementCommand, ResetCommand, RotationCommand, MovementCommand
from robmob.sensors import FullOdomSensor



class Robot:
    
    DISTANCE_CENTER_TO_WHEEL = 0.11

    def __init__(self, robot_ip, port=9090):
        self.ws = None
        self.publisher = None
        self.odom = None
        self.sensors = {}
        self.robot_url = 'ws://' + robot_ip + ':' + str(port)

        try:
            urllib.parse.urlparse(self.robot_url)
        except ValueError:
            print("L'adresse IP fournie est invalide") 
            print(self.robot_url)


    def connect(self):
        self.ws = websocket.WebSocketApp(self.robot_url,
                                         on_message = self._on_message,
                                         on_error = self._on_error,
                                         on_close = self._on_close)
        self.ws.on_open = self._on_open
        _thread.start_new_thread(self.ws.run_forever, ())


    def add_sensor(self, sensor):
        self.ws.send(json.dumps(sensor.subscription_message))

        if sensor.TOPIC in self.sensors:
            self.sensors[sensor.TOPIC].append(sensor)
        else:
            self.sensors[sensor.TOPIC] = [sensor]


    def send_command(self, command):
        if self.publisher:
            self.publisher.stop_publishing()
        self.publisher = CommandPublisher()
        self.publisher.start_publishing(self.ws.send, command)


    def disconnect(self):
        self.ws.keep_running = False
        
    def general_movement(self, linear, angular, duration):
        self.send_command(MovementCommand(linear, angular))
        time.sleep(duration)
        self.send_command(ResetCommand())
        
    def linear_movement(self, speed, duration):
        command = LinearMovementCommand(speed)
        
        self.send_command(command)
        time.sleep(duration)
        self.send_command(ResetCommand())
        
        
    def _moved_distance(self, initial_x, initial_y, x, y):
        return ((x - initial_x)**2 + (y - initial_y)**2)**0.5
        
        
    def linear_movement_precise(self, distance, speed):
        if not self.odom:
            self.odom = FullOdomSensor()
            self.add_sensor(self.odom)
            time.sleep(0.4)
        
        breaking_distance = speed / 0.05 * 0.0025 # Very approximative
        initial_x, initial_y, _ = self.odom.peek_data()
        x, y = initial_x, initial_y
        command = LinearMovementCommand(speed)
        self.send_command(command)
        while self._moved_distance(initial_x, initial_y, x, y) < distance - breaking_distance:
            time.sleep(0.5 / self.odom.SAMPLE_RATE)
            x, y, _ = self.odom.peek_data()
        self.send_command(ResetCommand())
            
        
    def angular_movement(self, speed, duration):
        command = RotationCommand(speed)
        
        self.send_command(command)
        time.sleep(duration)
        self.send_command(ResetCommand())

    def _on_message(self, _, raw_message):
        parsed_message = json.loads(raw_message)
        message_topic = parsed_message['topic']

        if message_topic in self.sensors:
            [s.on_message(parsed_message) for s in self.sensors[message_topic]]


    def _on_open(self, *args, **kargs):
        pass


    def _on_error(self, *args, **kargs):
        raise RuntimeError('Échec de la connexion au robot')


    def _on_close(self, *args, **kargs):
        pass
