#!/usr/bin/env python3
# based on cantldr.py by jerkey
# opens ks_can2serial canbus logs generated by https://github.com/jerkey/ks_can/blob/teslalog/ks_can2serial.ino
inFile = open('/tmp/can2serial.txt')
RESET  = '\033[0m' # https://misc.flogisoft.com/bash/tip_colors_and_formatting
GREEN  = '\033[32m'
RED    = '\033[31m'
YELLOW = '\033[33m'

ids = [530,546,770,924,930] # list of CAN IDs we care about
lastMsg = ['                                                                     '] * len(ids) # empty so it's not too short to compare with

for line in inFile: # '268:00000000B3000000 16\n' is what a line looks like
    if line.find('CAN')!=0: # swallow the init lines from ks_can2serial.ino
        id = int(line.split(':')[0],16)
        if id in ids: # we ignore CAN IDs not in our list
            idIndex = ids.index(id)
            if lastMsg[idIndex].split(' ')[0] != line.split(' ')[0]: # ignore messages that haven't changed since we last saw them
                print(str(id)+'\t',end='')
                for i in range(4,len(line.split(' ')[0])): # print character by character, colored according to same or changed
                    if lastMsg[idIndex][i]==line[i]:
                        print(RESET+line[i],end='')
                    else:
                        print(RED+line[i],end='')
                for i in range(len(line[4:].split(' ')),16): # pad data with spaces out to 16 characters
                        print(' ',end='')
                linetime = int(line[:-1].split(' ')[1]) # get the time in milliseconds from the log
                mins = int(linetime / (1000*60))
                secs = linetime % 60000 / 1000
                lastMsg[idIndex] = line # store the latest line to compare with for next time
                print('\t'+YELLOW+str(mins).zfill(3)+':',end='') # print the number of minutes:
                if secs < 10:
                    print('0',end='')
                print(str(secs)+RESET) # print the number of seconds (a float) and ANSI RESET

def parseCan(id,data):
    if id==530:
        BMS_contactorState = int(data[5],16) # lower 4 bits of third byte
        BMS_state = int(data[4],16) # high 4 bits of third byte
