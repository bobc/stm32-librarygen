#!/usr/bin/env/python

# -*- coding: utf-8 -*-

import sys,os,math
import re
import datetime
import requests

from lxml import etree
from str_utils import *

# Generate a symgen script
opt_symgen = True
verbose = False

lib_name = "MCU_ST_STM32"
num_devices = 0
num_warnings = 0
num_errors = 0

SPECIAL_PIN_MAPPING = {"VSS/TH"         : ["VSS/TH"],
                       "PC13-ANTI_TAMP" : ["PC13", "ANTI_TAMP"],
                       "PB2/BOOT1"      : ["PB2", "BOOT1"],
                       "PC14OSC32_IN"   : ["PC14"],
                       "PC15OSC32_OUT"  : ["PC15"], 
                       "PF11BOOT0"      : ["PF11"],
                       #"OSC_IN"     : [""],
                       #"OSC_OUT"    : [""]
                       }

PIN_REMAP = {"PC14OSC32_IN"   : "PC14-OSC32_IN",
             "PC15OSC32_OUT"  : "PC15-OSC32_OUT"}

SPECIAL_TYPES_MAPPING = {"RCC_OSC_IN": "Clock", "RCC_OSC_OUT": "Clock"}

PIN_TYPES_MAPPING = {"Power": "W", "I/O": "B", "Reset": "I", "Boot": "I", 
                     "MonoIO": "B", "NC": "N N", "Clock": "I"}

BOOT1_FIX_PARTS = {r"^STM32F10\d.+$", r"^STM32F2\d\d.+$", r"^STM32F4\d\d.+$", 
                   r"^STM32L1\d\d.+$"}

POWER_PAD_FIX_PACKAGES = {"UFQFPN28", "UFQFPN32", "UFQFPN48", "VFQFPN36"}

PIN_TYPES_MAPPING_SYMGEN = {"Power": "PI",
     "I/O": "B",
     "Reset": "I",
     "Boot": "I",
     "MonoIO": "B",
     "NC": "NN",
     "Clock": "I"}

# Mapping to KiCad packages
PACKAGES = {
    "LQFP32"  : "Package_QFP:LQFP-32_7x7mm_P0.8mm",
    "LQFP48"  : "Package_QFP:LQFP-48_7x7mm_P0.5mm",
    "LQFP64"  : "Package_QFP:LQFP-64_10x10mm_P0.5mm",
    "LQFP100" : "Package_QFP:LQFP-100_14x14mm_P0.5mm",
    "LQFP144" : "Package_QFP:LQFP-144_20x20mm_P0.5mm",
    "LQFP176" : "Package_QFP:LQFP-176_24x24mm_P0.5mm",
    "LQFP208" : "Package_QFP:LQFP-208_28x28mm_P0.5mm",

    "TSSOP14"  : "Package_SSOP:TSSOP-14_4.4x5mm_P0.65mm",
    "TSSOP20"  : "Package_SSOP:TSSOP-20_4.4x6.5mm_P0.65mm",

    "UFQFPN20" : "Package_DFN_QFN:QFN-20_3x3mm_P0.5mm",
    "UFQFPN28" : "Package_DFN_QFN:QFN-28_4x4mm_P0.5mm",
    "UFQFPN32" : "Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm",
    "UFQFPN48" : "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm",

    "VFQFPN36" : "Package_DFN_QFN:QFN-36-1EP_6x6mm_P0.5mm",

    "EWLCSP49" : "EWLCSP49",
    "EWLCSP66" : "EWLCSP66",

    "WLCSP25"  : "WLCSP25",
    "WLCSP36"  : "WLCSP36",
    "WLCSP49"  : "WLCSP49",
    "WLCSP63"  : "WLCSP63",
    "WLCSP64"  : "WLCSP64",
    "WLCSP66"  : "WLCSP66",
    "WLCSP72"  : "WLCSP72",
    "WLCSP81"  : "Package_CSP:WLCSP-81_4.41x3.76mm_P0.4mm",
    "WLCSP90"  : "WLCSP90",
    "WLCSP100" : "WLCSP100",
    "WLCSP104" : "WLCSP104",
    "WLCSP143" : "WLCSP143",
    "WLCSP144" : "WLCSP144",
    "WLCSP168" : "WLCSP168",
    "WLCSP180" : "WLCSP180",

    "LFBGA100" : "Package_BGA:BGA-100_10.0x10.0mm_Layout10x10_P0.8mm", 
    "LFBGA144" : "Package_BGA:BGA-144_10.0x10.0mm_Layout12x12_P0.8mm", 

    "TFBGA64"  : "Package_BGA:BGA-64_5.0x5.0mm_Layout8x8_P0.5mm",
    "TFBGA100" : "Package_BGA:BGA-100_8.0x8.0mm_Layout10x10_P0.8mm",
    "TFBGA216" : "Package_BGA:BGA-216_13.0x13.0mm_Layout15x15_P0.8mm",
    "TFBGA240" : "Package_BGA:BGA-265_14.0x14.0mm_Layout17x17_P0.8mm",

    "UFBGA64"  : "Package_BGA:BGA-64_5.0x5.0mm_Layout8x8_P0.5mm",
    "UFBGA100" : "Package_BGA:BGA-100_7.0x7.0mm_Layout10x10_P0.5mm",
    "UFBGA132" : "Package_BGA:BGA-132_7.0x7.0mm_Layout12x12_P0.5mm",
    "UFBGA144" : "UFBGA144",  # Package_BGA:BGA-144_7.0x7.0mm_Layout12x12_P0.5mm 
                              # Package_BGA:BGA-144_10.0x10.0mm_Layout12x12_P0.8mm 
    "UFBGA169" : "Package_BGA:BGA-169_7.0x7.0mm_Layout13x13_P0.5mm",
    "UFBGA176" : "Package_BGA:BGA-201_10.0x10.0mm_Layout15x15_P0.65mm"

    }

package_map = {
    "STM32F100" : "",
}

all_packages = []
missing_packages = []

def unique(items):
    found = set([])
    keep = []

    for item in items:
        if item not in found:
            found.add(item)
            keep.append(item)

    return keep

def istr (val):
    return str(int(val))

def textlen (s):
    return len(s) * 50

def round_to (val, grid):
    return int(int((val+grid-1)/grid)*grid)

def get_key(x):
    if "_" in x:
        return int(before(x,"_"))*10 +1
    else:
        return int(x)*10

def get_filter_package (package, package_name):
    if package == PACKAGES[package]:
        package = re.sub ("\d", "", package_name) + "?" + re.sub ("\D", "", package_name) + "*"
    else:
        package = after (package_name, ":")
        package = package.replace ("-", "?")
        package = package.replace ("_", "*") + "*"
    return package

def scan_for_footprints (path, files):

    all = []

    for pdffile in files:
        pdffile = os.path.join(path, pdffile)
        
        if pdffile.endswith(".par"):
            # print ("Scanning %s" % pdffile)
            f = open (pdffile)
            line = f.readline ()
            while line:
                line = line.strip()
                for package in PACKAGES:
                    if package in line and "pitch" in line :
                        line = package + after (line, package)
                        line = line.replace (u'\xd7'.encode('utf-8'), "x")
                        line = line.replace (u"\u2013".encode('utf-8'), "-")
                        line = before (line, "pitch")
                        line = line.replace(" ", "")
                        # add to list
                        line += "P"
                        if not line in all:
                            # print (line)
                            all.append (line)
                        break
                line = f.readline()
            f.close()

    print ("All footprints")
    for line in sorted(all):
        print (line)


class Pin:
    def __init__(self, pinnumber, name, pintype):
        # print ("%s %s" % (pinnumber, name))

        # PA13 (JTMS-SWDIO)
        # PA13 (JTMS/SWDIO)
        # VSSA/VREF-
        # PC14/OSC32_IN
        # PC14 / OSC32_IN
        # PC14 - OSC32_IN
        # PC14-OSC32_IN (PC14)

        if '(' in name:
            name = before (name, '(')

        if not (name in SPECIAL_PIN_MAPPING):
            if '-' in name and '/' in name and not name.endswith('-'): 
                print name

            split_name = name.split("/");
            realname = split_name[0]
            splname2 = split_name[0].split("-")
            if (len(splname2) > 1 and splname2[1] != ""):
                realname = splname2[0]
            altf = []
        else:
            realname = SPECIAL_PIN_MAPPING[name][0]
            altf = SPECIAL_PIN_MAPPING[name][1:]

        self.pinnumber = pinnumber
        self.name = realname
        self.altNames = []
        self.fullname = name
        self.pintype = pintype
        self.altfunctions = altf
        self.drawn = False  # Whether this pin has already been included in the component or not
        self.x = 0;
        self.y = 0;
        self.placed = False

        # fix bogus NC type labeling
        if self.name == "NC":
            self.pintype = "NC"

        # print ("%s %s %s %s" % (self.pinnumber, self.name, self.fullname, self.altfunctions) )

    def createPintext_orig(self, left):
        if (left):
            if (self.name == ""):
                s = "/".join(self.altfunctions + self.altNames)
            else:
                s = "/".join(self.altfunctions + self.altNames + [self.name])
        else:
            if (self.name == ""):
                s = "/".join(self.altNames + self.altfunctions)
            else:
                s = "/".join([self.name] + self.altNames + self.altfunctions)
        self.pintext = s.replace(" ","")

    def createPintext(self, left):
        if (left):
            if (self.name == ""):
                s = "/".join(self.altNames)
            else:
                s = "/".join(self.altNames + [self.name])
        else:
            if (self.name == ""):
                s = "/".join(self.altNames)
            else:
                s = "/".join([self.name] + self.altNames)
        self.pintext = s.replace(" ","")

        if not s:
            print "oops"

    def createPintext2(self, left):
        s = self.fullname + '/'.join(self.altNames)
        self.pintext = s.replace(" ","")

class SymFile:
    def __init__(self, filename):
        self.outfile = open (filename, "w")
        self.outfile.write ("#\n")
        self.outfile.write ("# Generated by stm32-librarygen\n")
        self.outfile.write ("# %s\n" % datetime.datetime.now().replace(microsecond=0).isoformat(' '))
        self.outfile.write ("#\n")


class device:
    def __init__(self, xmlfile, pdfdir):
        if verbose:
            print(xmlfile)
        self.xmlfile = xmlfile
        self.pdfdir = pdfdir
        self.name = ""
        self.package = ""
        self.pins = []
        self.aliases = []

        self.readxml()
        self.readpdf()
        self.createComponent()
        self.createDocu()

    def readxml(self):
        self.tree = etree.parse(self.xmlfile)
        self.root = self.tree.getroot()

        self.ns = {"a": self.root.nsmap[None]}  # I hate XML

        name = self.root.get("RefName")
        self.package = self.root.get("Package")

        als = re.search(r"^(.+)\((.+)\)(.+)$", name)
        if (als):
            pre = als.group(1)
            post = als.group(3)
            s = als.group(2).split("-")
            self.name = pre + s[0] + post
            for a in s[1:]:
                self.aliases.append(pre + a + post)
        else:
            self.name = name

        if not self.package in all_packages:
            all_packages.append (self.package)

        self.bga = False
        for child in self.root.xpath("a:Pin", namespaces=self.ns):
            # Create object and read attributes
            newpin = Pin(child.get("Position"), child.get("Name"), child.get("Type"))

            try:
                int(child.get("Position"))
            except ValueError:
                self.bga = True

            for signal in child.xpath("a:Signal",namespaces=self.ns):
                altfunction = signal.get("Name")
                if(not altfunction == "GPIO"):   # No need to add GPIO as alt function
                    newpin.altfunctions.append(altfunction)
                if(altfunction in SPECIAL_TYPES_MAPPING):
                    newpin.pintype = SPECIAL_TYPES_MAPPING[altfunction]
                    
            if newpin.name == "PB2":
                for pre in BOOT1_FIX_PARTS:
                    if re.search(pre, name) and (not ("BOOT1" in newpin.altfunctions)):
                        if verbose:
                            print("info: Fixing PB2/BOOT1 for part " + name +
                                "  " + newpin.name + " " + str(newpin.altfunctions))
                        newpin.altfunctions.insert(0, "BOOT1")
                    
            self.pins.append(newpin)

        self.hasPowerPad = False

        if self.root.get("HasPowerPad") == "true":
            self.hasPowerPad = True
        else:
            if self.package in POWER_PAD_FIX_PACKAGES:
                if verbose:
                    print("info: Absent powerpad detected in part " + self.name)
                self.hasPowerPad = True

        if(self.hasPowerPad == True):    # Special case for the thermal pad
            # Some heuristic here
            packPinCountR = re.search(r"^[a-zA-Z]+([0-9]+)$", self.package)
            powerpinnumber = int(packPinCountR.group(1)) + 1
            if verbose:
                print("info: Device " + name + " with powerpad, package " + self.package + ", power pin: " + str(powerpinnumber))
            powerpadpin = Pin(powerpinnumber, "VSS", "Power")
            self.pins.append(powerpadpin)

        
        if(not self.bga):
            for apin in self.pins:
                apin.pinnumber = int(apin.pinnumber)

        # Parse information for documentation
        self.core = self.root.xpath("a:Core", namespaces=self.ns)[0].text
        self.family = self.root.get("Family")
        self.line = self.root.get("Line")
        try:
            self.freq = self.root.xpath("a:Frequency", namespaces=self.ns)[0].text
        except:
            self.freq = None    # Some devices don't have a frequency specification... thanks obama!
        self.ram = self.root.xpath("a:Ram", namespaces=self.ns)[0].text
        self.io = self.root.xpath("a:IONb", namespaces=self.ns)[0].text
        self.flash = self.root.xpath("a:Flash", namespaces=self.ns)[0].text
        try:
            self.voltage = [self.root.xpath("a:Voltage", namespaces=self.ns)[0].get("Min", default="--"), self.root.xpath("a:Voltage", namespaces=self.ns)[0].get("Max", default="--")]
        except:
            self.voltage = None # Some devices don't have a voltage specification also

    def xcompare(self, x, y):
        l = min(len(x), len(y))
        for i in range(0, l):
            if ((x[i] != 'x') and (y[i] != 'x') and (x[i] != y[i])):
                return False
        return True

    def readpdf(self):
        global num_warnings

        self.pdf = "NOSHEET"
        files = []
        for (dirpath, dirnames, filenames) in os.walk(self.pdfdir):
            files.extend(filenames)
            break

        s = self.name

        #print("NEW: " + s)
        candidatestring = {}
        for pdf in files:
            if(pdf.endswith(".pdf.par")):   # Find all processed PDF files and open them for evaluation
                if sys.version_info.major >= 3:
                    p = open(os.path.join(self.pdfdir, pdf), "r", encoding="utf8")
                else:
                    p = open(os.path.join(self.pdfdir, pdf), "r")
                for line in p:
                    if(line.find(s[:8]) >= 0):
                        # Remove newline and commas and then split string
                        # avoid maketrans() error
                        #candidatenames = line.rstrip().translate(str.maketrans(","," ")).split()
                        candidatenames = line.rstrip()
                        candidatenames = candidatenames.replace(","," ")
                        candidatenames = candidatenames.split()
                        for candidatename in candidatenames:
                            candidatestring[candidatename] = pdf    # Associate file with every device name
                    if(not line.startswith("STM32")):   # Assume that the device names are always at the beginning of file
                        break
        #print(candidatestring)  # TODO: CONTINUE HERE!!!!
        keystokeep = []
        for key in candidatestring:
            # Some heuristic here
            minussplit = key.split("-")
            variants = minussplit[0].split("/")
            if (len(minussplit) > 1):
                suffix = "x" + "x".join(minussplit[1:])
            else:
                suffix = ""
            strings = [suffix + variants[0]]
            for var in variants[1:]:
                strings.append(strings[0][:-len(var)] + var + suffix)
            for string in strings:
                if self.xcompare(s, string):
                    keystokeep.append(key)
        
        winners = []    # I got too tired of this
        for key in unique(keystokeep):
            try:
                winners.append(candidatestring.pop(key))
            except:
                pass

        #print(winners)
        if(len(winners) > 0):
            firstwinner = winners[0]
            #print(winners)
            for winner in winners:
                if(winner == firstwinner):
                    self.pdf = winner[:-4]
                else:
                    print("warning: Multiple datasheet determined for this device: " + self.name + "(" + str(winners) + ")")
                    num_warnings+=1
                    self.pdf = "NOSHEET"
                    break
        
        if(self.pdf == "NOSHEET"):
            print("warning: Datasheet could not be determined for this device: " + self.name)
            num_warnings+=1

    def runDRC(self):
        pinNumMap = {}
        removePins = []
        for pin in self.pins:
            if pin.pinnumber in pinNumMap:
                if verbose:
                    print("info: Duplicated pin " + str(pin.pinnumber) + "(%s) in part " % pin.name + self.name + ", merging")
                mergedPin = pinNumMap[pin.pinnumber]
                mergedPin.altNames.append(pin.name)
                mergedPin.altfunctions += pin.altfunctions
                removePins.append(pin)
            pinNumMap[pin.pinnumber] = pin
            
        for pin in removePins:
            self.pins.remove(pin)
    
            
    def processPins(self):
        global num_errors

        #{"TOP": [], "BOTTOM": [], "RESET": [], "BOOT": [], "PWR": [], "OSC": [], "OTHER": [], "PORT": {}}
        self.resetPins = []
        self.bootPins = []
        self.clockPins = []
        self.otherPins = []

        self.powerPins = []

        self.ports = {}

        self.leftPins = []
        self.rightPins = []
        self.topPins = []
        self.bottomPins = []

        # Classify pins
        for pin in self.pins:
            if ((pin.pintype == "I/O" or pin.pintype == "Clock") and pin.name.startswith("P")):
                port = pin.name[1]
                try:
                    # num = re.sub("\D", "", pin.name[2:])
                    num = pin.name[2:]
                    self.ports[port][num] = pin
                except KeyError:
                    self.ports[port] = {}
                    self.ports[port][num] = pin
                except ValueError, ex:
                    print ("error: not an int: %s" % repr(ex))
                    num_errors += 1

            elif (pin.pintype == "Clock"):
                self.clockPins.append(pin)  
            elif ((pin.pintype == "Power") or (pin.name.startswith("VREF"))):
                if(pin.name.startswith("VDD") or pin.name.startswith("VBAT")):
                    self.topPins.append(pin)
                elif(pin.name.startswith("VSS")):
                    self.bottomPins.append(pin)
                else:
                    self.powerPins.append(pin)
            elif (pin.pintype == "Reset"):
                self.resetPins.append(pin)
            elif (pin.pintype == "Boot"):
                self.bootPins.append(pin)
            else:
                self.otherPins.append(pin)

        #
        # ------
        #

        # Apply pins to sides
        leftGroups = [[]]
        rightGroups = [[]]

        if len(self.resetPins) > 0:
            leftGroups.append(self.resetPins)
        if len(self.bootPins) > 0:
            leftGroups.append(self.bootPins)
        if len(self.powerPins) > 0:
            leftGroups.append(self.powerPins)
        if len(self.clockPins) > 0:
            leftGroups.append(self.clockPins)
        if len(self.otherPins) > 0:
            leftGroups.append(self.otherPins)
        
        del leftGroups[0]

        leftSpace = 0
        rightSpace = 0

        for group in leftGroups:
            l = len(group)
            leftSpace += l + 1

        serviceSpace = leftSpace

        portNames = sorted(self.ports.keys())

        for portname in portNames:
            port = self.ports[portname]
            pins = []
            for pinname in sorted(port.keys(), key=get_key ):
                pins.append(port[pinname])
            l = len(pins)
            rightSpace += l + 1
            rightGroups.append(pins)

        del rightGroups[0]

        maxSize = max(leftSpace, rightSpace)
        movedSpace = 0

        movedGroups = []

        while(True):
            groupToMove = rightGroups[-1]
            newLeftSpace = leftSpace + len(groupToMove) + 1
            newRightSpace = rightSpace - len(groupToMove) - 1
            newSize = max(newLeftSpace, newRightSpace)
            if newSize >= maxSize:
                break;
            maxSize = newSize
            leftSpace = newLeftSpace
            rightSpace = newRightSpace

            movedSpace += len(groupToMove) + 1

            movedGroups.append(groupToMove)
            rightGroups.pop()

        for group in movedGroups:
            i = 0
            for pin in group:
                pin.y = - (movedSpace - 1) + i
                i += 1
            movedSpace -= i + 1
            leftGroups.append(group)
            
        movedSpace = 0
        for group in reversed(rightGroups):
            movedSpace += len(group) + 1
            i = 0
            for pin in group:
                pin.y = - (movedSpace - 1) + i
                i += 1

        y = 0
        for group in leftGroups:
            for pin in group:
                if pin.placed:
                    continue
                if pin.y < 0:
                    pin.y = maxSize + pin.y - 1
                else:
                    pin.y = y
                pin.placed = True
                self.leftPins.append(pin)
                y += 1
            y += 1

        y = 0
        for group in rightGroups:
            for pin in group:
                if pin.placed:
                    continue
                if pin.y < 0:
                    pin.y = maxSize + pin.y - 1
                else:
                    pin.y = y
                pin.placed = True
                self.rightPins.append(pin)
                y += 1
            y += 1

        maxXSize = 0
        for i in range(maxSize):
            size = 0
            for pin in self.pins:
                if (pin.placed == True) and (int(pin.y) == i):
                    pin.createPintext(False)
                    size += len(pin.pintext)

            if (maxXSize < size):
                maxXSize = size

        topMaxLen = 0
        self.topPins = sorted(self.topPins, key=lambda p: p.name)
        topX = - int(len(self.topPins) / 2)
        for pin in self.topPins:
            pin.x = topX
            topX += 1
            pin.createPintext(False)
            if len(pin.pintext) > topMaxLen:
                topMaxLen = len(pin.pintext)

        bottomMaxLen = 0
        self.bottomPins = sorted(self.bottomPins, key=lambda p: p.name)
        bottomX = - int(len(self.bottomPins) / 2)
        for pin in self.bottomPins:
            pin.x = bottomX
            bottomX += 1
            pin.createPintext(False)
            if len(pin.pintext) > bottomMaxLen:
                bottomMaxLen = len(pin.pintext)

        a = 47
        b = 75
        self.yTopMargin = (math.ceil((topMaxLen * a + b) / 100))
        self.yBottomMargin = (math.ceil((bottomMaxLen * a + b) / 100) )

        self.boxHeight = maxSize * 100 + (self.yTopMargin + self.yBottomMargin) * 100
        self.boxHeight = math.floor(self.boxHeight / 100) * 100
        if (self.boxHeight / 2) % 100 > 0:
            self.boxHeight += 100

        #self.boxHeight = (maxSize - 2 + self.yTopMargin + self.yBottomMargin) * 100

        self.boxWidth = max ( (maxXSize + 1) * 47 + 100, 
                             max(len(self.topPins), len(self.bottomPins)) * 100 + 100)
        self.boxWidth = round_to (self.boxWidth, 200)
        #if (self.boxWidth / 2) % 100 > 0:
        #    self.boxWidth += 100
        self.boxWidth = int (self.boxWidth)

        #print(self.rightPins)
        self.yTopMargin += 1

    def createComponent(self):
        self.runDRC()
        self.processPins()

        # s contains the entire component in a single string
        if (len(self.pins) < 100):
            pinlength = 100
        else:
            pinlength = 200

        #yOffset = math.ceil(self.boxHeight / 100 / 2) * 100
        yOffset = self.boxHeight / 2
        #yOffset = int(yOffset)

        if self.package in PACKAGES:
            self.package_name = PACKAGES[self.package]
        else:
            self.package_name = self.package
            if not self.package in missing_packages:
                missing_packages.append (self.package)
            print ("error: Unknown package %s" % self.package)
            num_errors += 1

        s = ""
        s += "#\n"
        s += "# " + self.name.upper() + "\n"
        s += "#\n"
        s += "DEF " + self.name + " U 0 40 Y Y 1 L N\n"
        s += "F0 \"U\" " + istr(round(- self.boxWidth / 2)) + " " + istr(yOffset + 50) + " 50 H V C CNN\n"
        s += "F1 \"" + self.name + "\" " + istr(round(-self.boxWidth / 2)) + " " + istr(yOffset-self.boxHeight-50) + " 50 H V C CNN\n"
        if self.package != PACKAGES[self.package]:
            s += "F2 \"" + self.package_name + "\" " + "0" + " " + "0" + " 50 H I C CNN\n"
        else:
            s += "F2 \"\" 0 0 50 H I C CNN\n"
        s += "F3 \"\" 0 0 50 H I C CNN\n"
        if (len(self.aliases) > 0):
            s += "ALIAS " + " ".join(self.aliases) + "\n"

        #
        
        s += "$FPLIST\n"
        s += " " + get_filter_package(self.package, self.package_name) + "\n"
        s += "$ENDFPLIST\n"

        s += "DRAW\n"


        for pin in self.rightPins:
            pin.createPintext(True)
            s += "X " + pin.pintext + " " + str(pin.pinnumber) + " " + str(int(self.boxWidth / 2 + pinlength)) + " " + istr(round(yOffset - (pin.y + self.yTopMargin) * 100)) + " " + str(pinlength) + " L 50 50 1 1 " + PIN_TYPES_MAPPING[pin.pintype] + "\n"

        for pin in self.leftPins:
            pin.createPintext(False)
            s += "X " + pin.pintext + " " + str(pin.pinnumber) + " " + str(int(- self.boxWidth / 2 - pinlength)) + " " + istr(round(yOffset - (pin.y + self.yTopMargin) * 100)) + " " + str(pinlength) + " R 50 50 1 1 " + PIN_TYPES_MAPPING[pin.pintype] + "\n"

        for pin in self.topPins:    
            s += "X " + pin.pintext + " " + str(pin.pinnumber) + " " + str(int(pin.x * 100)) + " " + str(int(yOffset + pinlength)) + " " + str(pinlength) + " D 50 50 1 1 " + PIN_TYPES_MAPPING[pin.pintype] + "\n"

        #lowerY = yOffset - self.boxHeight
        lowerY = - self.boxHeight / 2

        for pin in self.bottomPins:
            s += "X %s %s %d %d %d U 50 50 1 1 %s\n" % (
                pin.pintext,
                str(pin.pinnumber),
                pin.x * 100,
                    lowerY - pinlength,
                pinlength,
                PIN_TYPES_MAPPING[pin.pintype])
        
        s += "S -%s %s %s %s 0 1 10 f\n"  % (
            istr(round(self.boxWidth / 2)),
                istr(lowerY),
            str(int(self.boxWidth / 2)),
                istr(yOffset) )

        s += "ENDDRAW\n"
        s += "ENDDEF\n"

        self.componentstring = s

    def createDocu(self):
        pdfprefix = "http://www.st.com/st-web-ui/static/active/en/resource/technical/document/datasheet/"
        
        #pdfprefix = "http://www.st.com/resource/en/datasheet/"
        #self.pdf = pdfprefix + self.name[:-2] + ".pdf"
        #if requests.head(self.pdf, allow_redirects=True).status_code != 200:
        #    print("URL invalid: " + self.pdf)
        #    self.pdf = ""
        
        if(self.pdf == "NOSHEET"):
            self.pdf = ""
        else:
            self.pdf = pdfprefix + self.pdf

        names = [self.name] + self.aliases
        s = ""
        for name in names:
            s += "$CMP " + name + "\n"
            
            s += "D Core: " + self.core + " Package: " + self.package + " Flash: " + self.flash + "KB Ram: " + self.ram + "KB "
            if self.freq:
                s += "Frequency: " + self.freq + "MHz "
            if self.voltage:
                s += "Voltage: " + self.voltage[0] + ".." + self.voltage[1] + "V "
            s += "IO-pins: " + self.io + "\n"
            
            s += "K " + " ".join([self.core, self.family, self.line]) + "\n"

            if self.pdf:
                s += "F " + self.pdf + "\n"   # TODO: Add docfiles to devices, maybe url to docfiles follows pattern?
            
            s += "$ENDCMP\n"
        self.docustring = s

    def writePins (self, f, pins, pos):
        for pin in pins:
            if pin.pintype == ' ':
                f.write ("SPC %s\n" % (pos))
            else:
                f.write ("%s %s %s %s\n" % (pin.pinnumber, 
                                            pin.fullname, 
                                            PIN_TYPES_MAPPING_SYMGEN[pin.pintype], pos))


    def writeSymgen (self, f):

        if (len(self.pins) < 100):
            pinlength = 100
        else:
            pinlength = 200

        f.write ("#\n")
        f.write ("# %s\n" % self.name.upper())
        f.write ("#\n")

        f.write ("COMP %s U\n" % self.name)

        f.write ("%%pinlen %d U\n" % pinlength)

        if self.package != PACKAGES[self.package]:
            f.write ("FIELD $FOOTPRINT \"%s\"\n" % self.package_name) # Package_DIP:DIP-24_W7.62mm"

        f.write ("FPLIST\n")
        f.write ("%s\n" % get_filter_package(self.package, self.package_name))

        desc = "%s, %s KB Flash, %s KB RAM, %s IO Pins" % (
            self.core, self.flash, self.ram, self.io)
            
        if self.freq:
            desc += ", %s MHz" % self.freq

        if self.voltage:
            desc += ", %sV-%sV" % (self.voltage[0], self.voltage[1])
            
        desc += ", %s" % self.package

        keywords = " ".join([self.core, self.family, self.line])

        f.write ("DESC %s\n" % desc)
        f.write ("KEYW %s\n" % keywords)

        if self.pdf != "NOSHEET":
            pdfprefix = "http://www.st.com/st-web-ui/static/active/en/resource/technical/document/datasheet/"
            doc = pdfprefix + self.pdf   # TODO: Add docfiles to devices, maybe url to docfiles follows pattern?
            f.write ("DOC %s\n" % doc)


        if (len(self.aliases) > 0):
            for name in self.aliases:
                f.write ("ALIAS %s\n" % name)
                f.write ("DESC %s\n" % desc)
                f.write ("KEYW %s\n" % keywords)
                if self.pdf != "NOSHEET":
                    f.write ("DOC %s\n" % doc)
           
        # width = 300 * 2 + max(len(self.topPins), len(self.bottomPins))*100

        space = Pin ("~", "~", " ")

        # self.writePins (f, self.pins + [space], "L")

        portNames = sorted(self.ports.keys())

        width = 800

        port_offset = 0
        while port_offset < len (portNames):

            num_ports = min(len(portNames)-port_offset, 6)

            max_left = 0
            max_right = 0
            for port_num in range (0,  num_ports):

                portname = portNames[port_offset + port_num]
                port = self.ports[portname]
                for pinname in sorted(port.keys()):
                    pin = port[pinname]

                    pin.fullname = pin.fullname if pin.fullname else pin.pintext
                    pin.fullname = pin.fullname.replace (' ','')
                    if pin.fullname in PIN_REMAP:
                        pin.fullname = PIN_REMAP[pin.fullname]

                    if port_num < num_ports/2:
                        max_left = max (max_left, textlen(pin.fullname))
                    else:
                        max_right = max (max_right, textlen(pin.fullname))

            width = max_left + max_right + 50
            width = round_to (width, 200)

            f.write ("UNIT WIDTH %d\n" % width)

            for port_num in range (0,  num_ports):

                portname = portNames[port_offset + port_num]
                port = self.ports[portname]

                pins = []
                f.write ("# Port %s\n" % portname)
                for pinname in sorted(port.keys()):
                    pins.append(port[pinname])
                dir = "L" if port_num < num_ports/2 else "R"
                self.writePins (f, pins, dir)
                if port_num != len(portNames)-1 :
                    self.writePins (f, [space], dir)
            port_offset += 6

        width = 300 * 2 + max(len(self.topPins), len(self.bottomPins))*100
        f.write ("UNIT WIDTH %d\n" % width)

        if self.resetPins:
            self.writePins (f, self.resetPins + [space], "L")
        if self.bootPins:
            self.writePins (f, self.bootPins + [space], "L")
        if self.clockPins:
            self.writePins (f, self.clockPins + [space], "L")
        if self.otherPins:
            self.writePins (f, self.otherPins + [space], "L")

        if self.powerPins:
            self.writePins (f, self.powerPins + [space], "L")

        for pin in self.topPins:
            f.write ("%s %s %s TC\n" % (pin.pinnumber, pin.name, PIN_TYPES_MAPPING_SYMGEN[pin.pintype]))

        for pin in self.bottomPins:
            f.write ("%s %s %s BC\n" % (pin.pinnumber, pin.name, PIN_TYPES_MAPPING_SYMGEN[pin.pintype]))

        #
        f.write ("END\n")

def main():
    global num_devices
    global num_errors

    args = sys.argv

    if(not len(args) == 3 or args[1] == "help"):
        printHelp()
    elif(os.path.isdir(args[1]) and os.path.isdir(args[2])):

        lib = open(lib_name + ".lib", "w")
        docu = open(lib_name + ".dcm", "w")

        #TODO: Add date and time of file generation to header
        lib.write("EESchema-LIBRARY Version 2.3\n")
        lib.write("#encoding utf-8\n")

        docu.write("EESchema-DOCLIB  Version 2.0\n")
        docu.write("#\n")

        # get PDF files
        files = []
        for (dirpath, dirnames, filenames) in os.walk(args[2]):
            files.extend(filenames)
            break

        print("info: Processing PDF files")
        for pdffile in files:
            pdffile = os.path.join(args[2], pdffile)
            pdfparsedfile = pdffile + ".par"
            if(not os.path.isfile(pdfparsedfile) and pdffile.endswith(".pdf")):
                if verbose:
                    print("info: Converting: " + pdffile)
                # Note : for this to work on Windows, .py extension must be configured to run with Python
                os.system("pdf2txt.py -o " + pdfparsedfile + " " + pdffile)

        # scan_for_footprints (args[2], files)

        # get xml files
        files = []
        for (dirpath, dirnames, filenames) in os.walk(args[1]):
            files.extend(filenames)
            break

        files.sort()

        sym_file = {} # SymFile ("MCU_STM32.txt")

        counts = {}

        print("info: Processing XML files")
        for xmlfile in files:
            try:
                num_devices += 1
                mcu = device(os.path.join(args[1], xmlfile), args[2])
                if(mcu.pdf != ""):
                    lib.write(mcu.componentstring)
                    docu.write(mcu.docustring)

                    if mcu.family in counts:
                        counts[mcu.family] += 1
                    else:
                        counts[mcu.family] = 1

                if opt_symgen:
                    if not mcu.family in sym_file:
                        sym_file [mcu.family] = SymFile ("MCU_STM32_"+mcu.family + ".txt")
                    mcu.writeSymgen (sym_file[mcu.family].outfile)

            except Exception, ex:
                print ("error: error creating part: %s" % repr(ex))
                num_errors += 1

        for key in sym_file:
            sym_file[key].outfile.close ()

        lib.write("#\n")
        lib.write("# End Library\n")
        lib.close()

        docu.write("#\n")
        docu.write("#End Doc Library\n")
        docu.close()

        if missing_packages:
            print ("Missing packages:")
            for s in missing_packages:
                print ('"%s" : "%s",' % (s,s) )

        print ("Number of warnings: %d" % num_warnings)
        print ("Number of errors  : %d" % num_errors)
        print ("Number of devices : %d" % num_devices)

        for key in sorted(counts.keys()):
            print ("%s %d" % (key, counts[key]) ) 
    else:
        printHelp()

def printHelp():
    print("Usage: main.py path/to/xmldir path/to/pdfdir")
    print("   Directory should ONLY contain valid xml files, otherwise the result will be bogus.")
    print("   I haven't included any error checking, so good luck!")

if __name__ == "__main__":
    main()
