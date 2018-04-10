#!/usr/bin/env python3
# based on cantldr.py by jerkey
# opens ks_can2serial canbus logs generated by https://github.com/jerkey/ks_can/blob/teslalog/ks_can2serial.ino
inFile = open('/tmp/can2serial.txt')
RESET  = '\033[0m' # https://misc.flogisoft.com/bash/tip_colors_and_formatting
GREEN  = '\033[32m'
RED    = '\033[31m'
YELLOW = '\033[33m'

ids = [530,546,770,924,930] # list of CAN IDs we care about
lastMsg = ['                                                                                                                                                                                                                                               '] * len(ids) # empty so it's not too short to compare with

def parseCan(id,data):
    if id==530:
        BMS_contactorState = int(data[5],16) # lower 4 bits of third byte
        BMS_state = int(data[4],16) # high 4 bits of third byte
        BMS_contactorStateText = {6:"BMS_CTRSET_CLEANING",5:"BMS_CTRSET_WELD",4:"BMS_CTRSET_SNA",3:"BMS_CTRSET_OPENING",2:"BMS_CTRSET_CLOSED",1:"BMS_CTRSET_PRECHARGE",0:"BMS_CTRSET_OPEN"}
        BMS_stateText = {15:"BMS_SNA",8:"BMS_WELD",7:"BMS_FAULT",6:"BMS_CLEARFAULT",5:"BMS_CHARGERVOLTAGE",4:"BMS_FASTCHARGE",3:"BMS_CHARGER",2:"BMS_SUPPORT",1:"BMS_DRIVE",0:"BMS_STANDBY"}
        message = 'BMS_contactorState:'+BMS_contactorStateText.get(BMS_contactorState,' ').ljust(20) + ' BMS_state:' + BMS_stateText.get(BMS_state,' ').ljust(18)
    elif id==546:
        BMS_chargeCommand = int(data[2:4]+data[0:2],16) * 0.001 #: 0|16@1+ (0.001,0) [0|40]               "kW" CHG "BMS Commanded AC power";
        BMS_chargeVoltageLimit = int(data[6:8]+data[4:6],16) * 0.01 #: 16|16@1+ (0.01,0) [0|600]         "V" CHG "BMS Pack voltage limit";
        BMS_chargeLineCurrentLimit = int(data[10]+data[8:10],16) % 512 * 0.16666 #: 32|9@1+ (0.16666,0) [0|85.16] "A" CHG "BMS Line current limit";
        message = 'BMS_chargeCommand:'+('%.0f' % BMS_chargeCommand).rjust(2)+'kW  BMS_chargeVoltageLimit:'+('%.0f' % BMS_chargeVoltageLimit).rjust(3)+'V  BMS_chargeLineCurrentLimit:'+('%.0f' % BMS_chargeLineCurrentLimit).rjust(2)+'A '+data[10:12]
        message += ' BMS_chargeClearFaults' if int(data[11],16) & 4 else ''# : 42|1@1+ (1,0) [0|0] aka 4          "" CHG "BMS Clear Faults";
        message += ' BMS_fcRequest' if int(data[11],16) & 8 else ''#: 43|1@1+ (1,0) [0|0]             8          "" CP,CHG "The BMS requests the charger to enable the FC sequence and turn on the BMS FC CAN Relay.";
        message += ' BMS_chgVLimitMode' if int(data[10],16) & 1 else ''# : 44|1@1+ (1,0) [0|0]         16         "" CHG "Tells the charger to either follow the BMS_chargeLimit or to track the pack voltage to prevent current spikes";
        BMS_chargeEnable = (int(data[10],16) & 6) >> 1 #: 45|2@1+ (1,0) [0|0]          32         "" CP,CHG "BMS Charge Enable";
        message += ' BMS_chargeEnable:'+str(BMS_chargeEnable) if BMS_chargeEnable else ''
        #BMS_chargeFC_statusCode : 48|4@1+ (1,0) [0|0] "" CHG 15 "PT_FC_STATUS_NODATA" 14 "PT_FC_STATUS_MALFUNCTION" 13 "PT_FC_STATUS_NOTCOMPATIBLE" 6 "PT_FC_STATUS_EXT_ISOACTIVE" 5 "PT_FC_STATUS_INT_ISOACTIVE" 4 "PT_FC_STATUS_UTILITY" 3 "PT_FC_STATUS_SHUTDOWN" 2 "PT_FC_STATUS_PRELIMITEXCEEDED" 1 "PT_FC_STATUS_READY" 0 "PT_FC_STATUS_NOTREADY_SNA" ;
        #BMS_chargeFC_type : 52|3@1+ (1,0) [0|7] "" GTW,CHG 7 "PT_FC_TYPE_SNA" 6 "PT_FC_TYPE_OTHER" 3 "PT_FC_TYPE_CC_EVSE" 2 "PT_FC_TYPE_CHINAMO" 1 "PT_FC_TYPE_CHADEMO" 0 "PT_FC_TYPE_SUPERCHARGER" ;
    else:
        message = data
    return message

for line in inFile: # '268:00000000B3000000 16\n' is what a line looks like
    if line.find('CAN')!=0: # swallow the init lines from ks_can2serial.ino
        id = int(line.split(':')[0],16)
        if id in ids: # we ignore CAN IDs not in our list
            idIndex = ids.index(id)
            parsedLine = parseCan(id,line.split(' ')[0][4:20])
            if lastMsg[idIndex] != parsedLine: # ignore messages that haven't changed since we last saw them
                print(str(id)+'\t',end='')
                # print(parsedLine+';'+str(len(lastMsg[idIndex]))+':'+str(len(parsedLine)))
                for i in range(len(parsedLine)): # print character by character, colored according to same or changed
                    if lastMsg[idIndex].ljust(len(parsedLine))[i]==parsedLine[i]:
                        print(RESET+parsedLine[i],end='')
                    else:
                        print(RED+parsedLine[i],end='')
                for i in range(len(parsedLine),72): # pad data with spaces
                        print(' ',end='')
                linetime = int(line[:-1].split(' ')[1]) # get the time in milliseconds from the log
                mins = int(linetime / (1000*60))
                secs = linetime % 60000 / 1000
                lastMsg[idIndex] = parsedLine # store the latest line to compare with for next time
                print('\t'+YELLOW+str(mins).zfill(3)+':',end='') # print the number of minutes:
                if secs < 10:
                    print('0',end='')
                print(str(secs)+RESET) # print the number of seconds (a float) and ANSI RESET

