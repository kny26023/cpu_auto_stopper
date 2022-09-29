import os
import subprocess
import requests
import time

#Min cpu load
MIN_CPU=5
#Max time of no util usage (sec)
MAX_SEC=1800
#For average calculation
CPU_LIST= {}
MEM_LIST= {}
#For time calculation
TIME_LIST= {}

headers = {
    'Content-type': 'application/json',
}

while(True):
    #Container name to check
    CMD="docker stats --format 'table {{.Name}}' --no-stream"
    CONTLIST= str(subprocess.run(CMD, stdout=subprocess.PIPE, shell=True).stdout).lstrip("b'").rstrip("\n'").split("\\n")
    CONTLIST.remove("NAME")
    CONTLIST.pop()
    start= time.time()
    #iterate for each container to check in list
    for CONTAINER in CONTLIST:
        if(CONTAINER not in CPU_LIST.keys()):
            CPU_LIST[CONTAINER] = 0
            MEM_LIST[CONTAINER] = 0
            TIME_LIST[CONTAINER] = 1

        #Fetch other process stats by container name

        #CPU Usage
        CPU="docker stats %s --format 'table {{.CPUPerc}}' --no-stream" %(CONTAINER)
        CPU= (str(subprocess.run(CPU, stdout=subprocess.PIPE, shell=True).stdout).split("\\n"))
        CPU= CPU[1]
        CPU = CPU.rstrip("%'")
        CPU= float(CPU)
        CPU_LIST[CONTAINER] += CPU

        #Memory Usage
        MEM="docker stats %s --format 'table {{.MemUsage}}' --no-stream" %(CONTAINER)
        MEM= (str(subprocess.run(MEM, stdout=subprocess.PIPE, shell=True).stdout).split("\\n"))[1]
        MEM = MEM.split(" / ")[0]
        if("GiB" in MEM):
            MEM= MEM.lstrip("'").rstrip("GiB'")
            MEM = float(MEM) * 1024
        else:
            MEM= MEM.lstrip("'").rstrip("MiB'")
            MEM = float(MEM)
        MEM_LIST[CONTAINER] += MEM
        
        #Stop container
        if((CPU_LIST[CONTAINER] / TIME_LIST[CONTAINER]) < MIN_CPU and (MEM_LIST[CONTAINER] / TIME_LIST[CONTAINER]) >= 30720):
            if(TIME_LIST[CONTAINER] >= MAX_SEC):
                json="{'text': 'Container %s used %.2fMiB of Memory with using average %.2fpercent of CPU Util. Container was stopped.'}" %(CONTAINER, MEM_LIST[CONTAINER] / TIME_LIST[CONTAINER], CPU_LIST[CONTAINER] / TIME_LIST[CONTAINER])
                response = requests.post('YOUR_SLACK_WEBHOOK', headers=headers, data=json) #Put your Slack webhook at YOUR_SLACK_WEBHOOK
                #Docker stop part
                stop= "docker stop %s" %(CONTAINER)
                subprocess.run(stop, shell=True)
                ##Docker kill part (optional)
                #subprocess.run("sleep 3", shell=True)
                #kill= "docker kill %s" %(CONTAINER)
                #subprocess.run(kill, shell=True)
                del(CPU_LIST[CONTAINER])
                del(MEM_LIST[CONTAINER])
                del(TIME_LIST[CONTAINER])
        else:
            if(TIME_LIST[CONTAINER] >= MAX_SEC):
                CPU_LIST[CONTAINER] = 0
                MEM_LIST[CONTAINER] = 0
                TIME_LIST[CONTAINER] = 1
            else:
                TIME_LIST[CONTAINER] += time.time() - start
