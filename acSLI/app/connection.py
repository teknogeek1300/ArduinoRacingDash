import serial
import serial.tools.list_ports
import re
import acSLI
import threading
from app.logger import Logger
import app.loader as Config
import app.error as Error

Log = Logger()
instance = 0


class Connection:
    ser = 0
    port = 0
    handshake = False
    dispSelect = False
    dispSelectMsg = 0

    def __init__(self):
        global instance
        instance = self

    def send(self, msg):
        self.ser.write(msg)

    def close(self):
        self.ser.close()


def _findConnect():
    global instance
    portValid = False
    instance.handshake = False
    instance.dispSelect = False

    for sPort, desc, hwid in sorted(serial.tools.list_ports.comports()):
        Log.log("%s: %s [%s]" % (sPort, desc, hwid))

        if Config.instance.cfgPort == "AUTO":
            if "Arduino" in desc:
                instance.port = sPort
                portValid = True
        else:
            if Config.instance.cfgPort == sPort:
                instance.port = sPort
                portValid = True

        if portValid:
            break

    if portValid:
        instance.ser = serial.Serial(instance.port, 9600, timeout=5)
        arduinoVer = instance.ser.read(3)

        if str(arduinoVer) == "b''":
            instance.port = "----"
            Log.warning("No Response From Arduino. Please Ensure Arduino is running at least v" +
                        acSLI.App.ArduinoVersion)
            instance.dispSelect = True
            instance.dispSelectMsg = "No Response from Arduino"
        else:
            aV = re.findall(r"\'(.+?)\'", str(arduinoVer))[0]
            if "".join(acSLI.App.ArduinoVersion.split(".")) > aV:
                instance.port = "----"
                Log.warning("Arduino Code Outdated. Please Update Arduino to at least v" +
                            acSLI.App.ArduinoVersion)
                Error.ErrorBox("Arduino Code Outdated. Please Update Arduino to at least v" +
                               acSLI.App.ArduinoVersion + " and then Reconnect")
            else:
                instance.handshake = True
                Log.info("Connected to Arduino running v"
                         + aV[0] + '.' + aV[1] + '.' + aV[2] + " on port " + instance.port)
    else:
        instance.port = "----"
        if Config.instance.cfgPort == "AUTO":
            Log.warning("No Arduino Detected")
            instance.dispSelect = True
            instance.dispSelectMsg = "No Arduino Detected"
        else:
            Log.warning("Invalid COM Port Configured")
            instance.dispSelect = True
            instance.dispSelectMsg = "Invalid COM Port Configured"

            # ac.setText(lbConnectedPort, "Connected COM Port: {}".format(port))


class findConnection (threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        #Log.info("Start Port Search")
        _findConnect()