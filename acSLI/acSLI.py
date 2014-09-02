#######################################################
#
#    AC SLI - USB Interface for use with arduino    
#
#    Author: Turnermator13
#
#    Please find this on github at:
#    -https://github.com/Turnermator13/ArduinoRacingDash
#
#    Thanks to @Rombik for "SimInfo"
#
#    Uses pySerial 2.7 library
#    -http://pyserial.sourceforge.net/
#
#######################################################

import sys
sys.path.insert(0, 'apps/python/acSLI/dll')

import ac
import acsys
import math
import serial
import serial.tools.list_ports
from libs.sim_info import SimInfo
from libs.utils import Config

Version = "1.5"

sim_info = SimInfo()
appPath = "apps/python/acSLI/"
appWindow = 0
ser = 0
ticker = 0

cfg = 0
cfg_Path = "config.ini"
cfg_Port = "AUTO"
cfg_SpeedUnit = "MPH"

max_rpm = 0
max_fuel = 0

def acMain(ac_version):
    global appWindow, ser, cfg_Port, ticker
    appWindow=ac.newApp("AC SLI")
    ac.setSize(appWindow,150,100)
    ac.drawBorder(appWindow,0)
    ac.setBackgroundOpacity(appWindow,0)
    
    loadConfig()
    
    portValid = False
    for port, desc, hwid in sorted(serial.tools.list_ports.comports()):
        if cfg_Port == "AUTO":
            if "Arduino" in desc:
                ac.console("%s: %s [%s]" % (port, desc, hwid))
                cfg_Port = port
                portValid = True
        else:
            if cfg_Port == port:
                ac.console("%s: %s [%s]" % (port, desc, hwid))
                portValid = True
        
        if portValid:
            break
        
        
    if portValid:
        ser = serial.Serial(cfg_Port, 9600)
        ac.console("AC SLI v" + Version + " loaded, using: " + cfg_Port)
    else:
        ticker = 3
        if cfg_Port == "AUTO": 
            ac.console("No Arduino Detected")
        else:
            ac.console("Invalid COM Port")
        
    return "AC SLI"

    
def acUpdate(deltaT):   
    global ticker, ser, max_rpm, max_fuel, sim_info, cfg_SpeedUnit
    
    if ticker == 2:
        ac_gear = ac.getCarState(0, acsys.CS.Gear)
        ac_speed = round(ac.getCarState(0, acsys.CS.SpeedMPH)) if cfg_SpeedUnit == "MPH" else round(ac.getCarState(0, acsys.CS.SpeedKMH))
        rpms = ac.getCarState(0, acsys.CS.RPM)
        max_rpm = sim_info.static.maxRpm if max_rpm == 0 else max_rpm
        
        
        shift = 0
        if max_rpm > 0:
            thresh = max_rpm*0.65
            if rpms >= thresh:
                shift = round(((rpms-thresh)/(max_rpm-thresh))*16)
        
        current_fuel = sim_info.physics.fuel
        max_fuel = sim_info.static.maxFuel if max_fuel == 0 else max_fuel
        fuel = int((current_fuel/max_fuel)*100)
        
        lapCount = sim_info.graphics.completedLaps
        
        engine = 0x00
        if sim_info.physics.pitLimiterOn and not sim_info.graphics.isInPit:
            engine = 0x10 

        boost = round(ac.getCarState(0, acsys.CS.TurboBoost), 1)
        b1 = math.floor(boost)
        b2 = (boost - b1)*10
            
        key = bytes([255,ac_gear,ac_speed,((int(rpms) >> 8) & 0x00FF),(int(rpms) & 0x00FF),fuel,shift,engine,lapCount, int(b1), int(b2)])
        x = ser.write(key)
        
        ticker = 0
    else:
        if ticker < 3:
            ticker = ticker + 1
    
       
def acShutdown():
    global ser
    ser.close()
    
    
def loadConfig():
    global appPath, cfg, cfg_Path, cfg_Port, cfg_SpeedUnit
    
    try:
        cfg = Config(appPath + cfg_Path)
        cfg_Port = cfg.getOption("SETTINGS", "port").upper()
        cfg_SpeedUnit = cfg.getOption("SETTINGS", "speed_unit").upper()
    
    except Exception as e:
        ac.console("acSLI: Error in loading Config File: %s" % e)
        ac.log("acSLI: Error in loading Config File: %s" % e)