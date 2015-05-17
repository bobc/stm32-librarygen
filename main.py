#!/usr/bin/env python3

import sys
import xml.etree.ElementTree as ET
from lxml import etree
import os

class pin:
    def __init__(self, pinnumber, name, pintype):
        self.pinnumber = pinnumber
        self.name = name
        self.pintype = pintype
        self.altfunctions = []
        self.drawn = False  # Whether this pin has already been included in the component or not

    def createPintext(self):
        s = ""
        for alt in self.altfunctions:
            s += alt + "/"
        s += self.name
        self.pintext = s
        
class device:
    def __init__(self, xmlfile):
        self.xmlfile = xmlfile
        self.name = ""
        self.package = ""
        self.pins = []

        self.readxml()
        self.createComponent()

    def readxml(self):
        self.tree = etree.parse(self.xmlfile)
        self.root = self.tree.getroot()

        self.ns = {"a": self.root.nsmap[None]}  # I hate XML

        self.name = self.root.get("RefName")
        self.package = self.root.get("Package")

        for child in self.root.xpath("a:Pin",namespaces=self.ns):
            # Create object and read attributes
            newpin = pin(child.get("Position"), child.get("Name"), child.get("Type"))
            for signal in child.xpath("a:Signal",namespaces=self.ns):
                altfunction = signal.get("Name")
                if(not altfunction == "GPIO"):   # No need to add GPIO as alt function
                    newpin.altfunctions.append(altfunction)
            newpin.createPintext()  # Have the pins generate their text
            self.pins.append(newpin)

    def createComponent(self):
        # s contains the entire component in a single string

        ports = {}
        portpins = {}
        pincount = 0
        portcount = 0
        # Count amount of different Ports and how many I/O pins they contain
        for pin in self.pins:
            if(pin.pintype == "I/O" and len(pin.name) == 3):    # Avoid counting oscillator pins
                pincount += 1
                port = pin.name[1]
                try:
                    ports[port] += 1    # Increment pincount for this port
                except KeyError:
                    ports[port] = 1     # Key doesn't yet exist, create it
                    portcount += 1
                    portpins[port] = {} # Same as above
                portpins[port][pin.name[2]] = pin
        
        
        padding = 400   # 200 mils top and bottom as padding
        boxheight = (pincount - 1) * 100 + (portcount - 1) * 100 + padding * 2  # height in mils 
        
        maxstringlen = 0
        for pin in self.pins:
            maxstringlen = max(maxstringlen, len(pin.pintext))

        boxwidth = maxstringlen * 50 
        
        
        s = ""
        s += "#\r\n"
        s += "# " + self.name.upper() + "\r\n"
        s += "#\r\n"
        s += "DEF " + self.name + " U 0 40 Y Y 1 L N\r\n"
        s += "F0 \"U\" -1550 1600 50 H V C CNN\r\n"
        s += "F1 \"" + self.name + "\" 1300 -1600 50 H V C C\r\n"
        s += "F2 \"~\" 0 -100 50 H V C CIN\r\n"
        s += "F3 \"~\" 0 0 50 H V C CNN\r\n"
        s += "DRAW\r\n"
        # Start drawing rectangles and pins
        # Start to iterate through ports alphabetically
        positioncounter = 0
        portkeys = sorted(list(ports.keys()))
        for port in portkeys:
            pinnumbers = sorted(list(portpins[port].keys()))
            for pinnumber in pinnumbers:
                pin = portpins[port][pinnumber]
                s+= "X " + pin.pintext + " " + str(pin.pinnumber) + " " + str(round(boxwidth/2 + 100)) + " " + str(round(boxheight/2 - positioncounter*100 - padding)) + " 100 L 50 50 1 1 I\r\n"
                positioncounter += 1
                pin.drawn = True
            positioncounter += 1    # Create gap between 2 ports


        print(powerpins)

        s += "S -" + str(round(boxwidth/2)) + " -" + str(round(boxheight/2)) + " " + str(round(boxwidth/2)) + " " + str(round(boxheight/2)) + " 0 1 10 f\r\n"
        s += "ENDDRAW\r\n"
        s += "ENDDEF\r\n"

        self.componentstring = s
        print(s)  

def main():
    args = sys.argv
    
    pins = []

    if(not len(args) == 2 or args[1] == "help"):
        printHelp()
    elif(os.path.isfile(args[1])):
        test = device(args[1])
        f = open("test.lib", "w")
        header = '''EESchema-LIBRARY Version 2.3
#encoding utf-8
'''
        f.write(header + test.componentstring + "#\r\n# End Library\r\n")
        f.close()
    else:
        printHelp()
    



def printHelp():
    print("Usage: main.py path/to/file.xml")

if __name__ == "__main__":
    main()
