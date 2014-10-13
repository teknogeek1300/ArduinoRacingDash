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

import serial
import serial.tools.list_ports
from libs.sim_info import SimInfo
from libs.utils import Config

#################
Version = "1.8.3"
#################

sim_info = SimInfo()
appPath = "apps/python/acSLI/"
appWindow = 0
ser = 0
ticker = 0
run = 0
port = 0
oldComPortText = 0
oldStartPageText = 0

cfg = 0
cfg_Path = "apps/python/acSLI.cfg"
cfg_Port = "AUTO"
cfg_SpeedUnit = "MPH"
cfg_StartPage = 0
cfg_Intensity = 0

max_rpm = 0
max_fuel = 0

lbConnectedPort = 0
lbComPortSetting = 0
lbStartPageSetting = 0
btnSpeedUnits = 0
btnReconnect = 0
txtComPort = 0
txtStartPage = 0
spnIntensity = 0


def acMain(ac_version):
    global appWindow, cfg_SpeedUnit, cfg_Port, oldComPortText, oldStartPageText, btnSpeedUnits, btnReconnect, lbConnectedPort, lbComPortSetting, lbStartPageSetting, txtComPort, txtStartPage, spnIntensity
    appWindow=ac.newApp("AC SLI " + Version)
    ac.setSize(appWindow,250,244)
    ac.drawBorder(appWindow,0)
    ac.setBackgroundOpacity(appWindow,0) 
    
    loadConfig() 
    checkVersion()
    
    lbConnectedPort = ac.addLabel(appWindow, "Connected COM Port: {}".format(cfg_Port))
    ac.setPosition(lbConnectedPort,15,40)
    ac.setSize(lbConnectedPort,220,20)
    ac.setFontAlignment(lbConnectedPort, "center")
    
    btnReconnect = ac.addButton(appWindow, "Reconnect/Re-Scan COM Port(s)")
    ac.addOnClickedListener(btnReconnect, bFunc_ReconnectCOM)
    ac.setPosition(btnReconnect,15,68)
    ac.setSize(btnReconnect,220,20)     
       
    lbComPortSetting = ac.addLabel(appWindow, "COM Port Setting: ")
    ac.setPosition(lbComPortSetting,30,96)
    ac.setSize(lbComPortSetting,220,20)
        
    txtComPort = ac.addTextInput(appWindow,"COMx")
    ac.setPosition(txtComPort,157,97)
    ac.setSize(txtComPort,51,20)
    ac.setFontAlignment(txtComPort, "center")
    ac.setText(txtComPort, cfg_Port)
    oldComPortText = cfg_Port
    
    
    btnSpeedUnits = ac.addButton(appWindow, "Speed Units: {}".format(cfg_SpeedUnit))
    ac.addOnClickedListener(btnSpeedUnits, bFunc_SpeedUnits)
    ac.setPosition(btnSpeedUnits,15,138)
    ac.setSize(btnSpeedUnits,220,20)
    
    lbStartPageSetting = ac.addLabel(appWindow, "Default Dash Page: ")
    ac.setPosition(lbStartPageSetting,30,166)
    ac.setSize(lbStartPageSetting,220,20)
        
    txtStartPage = ac.addTextInput(appWindow,"Page")
    ac.setPosition(txtStartPage,160,167)
    ac.setSize(txtStartPage,21,20)
    ac.setFontAlignment(txtStartPage, "center")
    ac.setText(txtStartPage, cfg_StartPage)
    oldStartPageText = cfg_StartPage
    
    spnIntensity = ac.addSpinner(appWindow, "Display Intensity")
    ac.setPosition(spnIntensity,15,212)
    ac.setSize(spnIntensity,220,20)
    ac.setRange(spnIntensity, 0,7)
    ac.setValue(spnIntensity, cfg_Intensity)
    ac.addOnValueChangeListener(spnIntensity, bFunc_ChangeIntensity)
    
    connectCOM()
    
    ac.console("AC SLI v" + Version + " loaded")
    return "AC SLI"


def acUpdate(deltaT):
    global ticker, run, ser, max_rpm, max_fuel, sim_info, cfg_SpeedUnit, cfg_StartPage, cfg_Port, cfg_StartPage, oldComPortText, oldStartPageText, lbStartPageSetting

    if run == 1 and ticker % 3 == 0:
        ac_gear = ac.getCarState(0, acsys.CS.Gear)
        ac_speed = int(round(ac.getCarState(0, acsys.CS.SpeedMPH)) if cfg_SpeedUnit == "MPH" else round(ac.getCarState(0, acsys.CS.SpeedKMH)))
        rpms = int(ac.getCarState(0, acsys.CS.RPM))
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
        if lapCount > 199:
            lapCount = 199

        engine = 0x00
        if sim_info.physics.pitLimiterOn and not sim_info.graphics.isInPit:
            engine = 0x10

        boost = round(ac.getCarState(0, acsys.CS.TurboBoost), 1)
        b1 = int(boost*10)

        delta = ac.getCarState(0, acsys.CS.PerformanceMeter)
        deltaNeg = 0
        if delta <= 0:
            deltaNeg = 1
        delta = int(abs(delta) * 1000)
        if delta > 9999:
            delta = 9999

        bSetting = int(deltaNeg << 7) | int(int(ac.getValue(spnIntensity)) << 4) | int(cfg_StartPage)


        key = bytes([255,bSetting,ac_gear,((ac_speed) >> 8 & 0x00FF),(ac_speed & 0x00FF),((rpms >> 8) & 0x00FF),(rpms & 0x00FF),fuel,shift,engine,lapCount,b1,((delta >> 8) & 0x00FF),(delta & 0x00FF)])
        x = ser.write(key)


    if ticker == 30:
        ticker = 0

        text = ac.getText(txtComPort).upper()
        if not text == oldComPortText:
            cfg_Port = text
            ac.setText(txtComPort, cfg_Port)
            cfg.updateOption("SETTINGS", "port", cfg_Port, True)
            oldComPortText = text
            ac.console("Update COM Port Setting To: {}".format(cfg_Port))

        num = ac.getText(txtStartPage)
        if not num == oldStartPageText:
            if num.isdigit() and int(num) > -1 and int(num) < 8:
                cfg_StartPage = num
                ac.setText(txtStartPage, cfg_StartPage)
                cfg.updateOption("SETTINGS", "startupPage", cfg_StartPage, True)
                oldStartPageText = num
                ac.console("Update Default Page Setting To: {}".format(cfg_StartPage))
            else:
                ac.setText(txtStartPage, "")

    else:
        ticker += 1
    
    
    
def acShutdown():
    global ser
    ser.close()
    
    
def loadConfig():
    global cfg, cfg_Path, cfg_Port, cfg_SpeedUnit, cfg_StartPage, cfg_Intensity
    
    try:
        cfg = Config(cfg_Path)              
        cfg_Port = str(cfg.getOption("SETTINGS", "port", True, cfg_Port)).upper()
        cfg_SpeedUnit = str(cfg.getOption("SETTINGS", "unitSpeed", True, cfg_SpeedUnit)).upper()
        cfg_StartPage = str(cfg.getOption("SETTINGS", "startupPage", True, cfg_StartPage))
        cfg_Intensity = str(cfg.getOption("SETTINGS", "intensity", True, cfg_Intensity))
        
        if not(cfg_StartPage.isdigit() or int(cfg_StartPage.isdigit()) > -1 or int(cfg_StartPage.isdigit()) < 6):
            cfg_StartPage = 0
    
    except Exception as e:
        ac.console("acSLI: Error in loading Config File: %s" % e)
        ac.log("acSLI: Error in loading Config File: %s" % e)
        

def connectCOM():
    global ser, port, cfg_Port, ticker, run, lstComPorts
    
    portValid = False
    for sPort, desc, hwid in sorted(serial.tools.list_ports.comports()):
        ac.console("%s: %s [%s]" % (sPort, desc, hwid))
        
        if cfg_Port == "AUTO":
            if "Arduino" in desc:
                port = sPort
                portValid = True
        else:                                                                                                   
            if cfg_Port == sPort:
                port = sPort
                portValid = True
        
        if portValid:
            break
                
    if portValid:
        run = 1
        ser = serial.Serial(port, 9600)
        ac.console("acSLI: connected to {}".format(port))
    else:
        run = 0
        port = "----"
        if cfg_Port == "AUTO": 
            ac.console("acSLI: No Arduino Detected")
        else:
            ac.console("acSLI: Invalid COM Port")
    
    ac.setText(lbConnectedPort, "Connected COM Port: {}".format(port))

 
def checkVersion():
    #versionFile = urllib.request.get('http://goo.gl/BmJaXS')
    #ac.console(str(versionFile.read()))
    #ac.log(str(dir()).strip('[]'))
    pass
    
    
def bFunc_ChangeIntensity(dummy):
    global cfg, spnIntensity
    
    intensity = int(ac.getValue(spnIntensity))
    cfg.updateOption("SETTINGS", "intensity", intensity, True)
    ac.console("acSLI: update intensity to to {}".format(intensity))
    
    
def bFunc_ReconnectCOM(dummy, variables):
    global ser
    if not port == "----":
        ser.close()
    connectCOM()  
            
        
def bFunc_SpeedUnits(dummy, variables):
    global cfg, cfg_SpeedUnit, btnSpeedUnits

    if cfg_SpeedUnit == "MPH":
        cfg_SpeedUnit = "KPH"
    elif cfg_SpeedUnit == "KPH":
        cfg_SpeedUnit = "MPH"

    ac.setText(btnSpeedUnits, "Speed Units: {}".format(cfg_SpeedUnit))
    cfg.updateOption("SETTINGS", "unitSpeed", cfg_SpeedUnit, True)
    ac.console("acSLI: speed units toggle to {}".format(cfg_SpeedUnit))