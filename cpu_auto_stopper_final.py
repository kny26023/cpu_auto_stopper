import os
import subprocess
import requests
import time

#Min cpu load
MIN_CPU=5
MIN_CPU2=1
#Max time of no util usage (sec)
MAX_SEC=1800
MAX_SEC2=7200
#For average calculation
CPU_LIST= {}
CPU_LIST2= {}
MEM_LIST= {}
#For time calculation
TIME_LIST= {}
TIME_LIST2= {}

headers = {
    'Content-type': 'application/json',
}

while(True):
    #Container name to check
    start= time.time()
    CMD="docker stats --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}' --no-stream"
    CONTLIST= str(subprocess.run(CMD, stdout=subprocess.PIPE, shell=True).stdout).lstrip("b'").rstrip("\n'").split("\\n")
    CONTLIST.remove("NAME                         CPU %      MEM USAGE / LIMIT")
    CONTLIST.pop()
    #iterate for each container to check in list
    for LL in CONTLIST:
        LL = LL.split()
        CONTAINER = LL[0]
        if(CONTAINER not in CPU_LIST.keys()):
            CPU_LIST[CONTAINER] = 0
            MEM_LIST[CONTAINER] = 0
            TIME_LIST[CONTAINER] = 1
        if(CONTAINER not in CPU_LIST2.keys()):
            CPU_LIST2[CONTAINER] = 0
            TIME_LIST2[CONTAINER] = 1
        
        #Fetch other process stats by container name
        
        #CPU Usage
        CPU=  LL[1]
        CPU = CPU.rstrip("%'")
        CPU = float(CPU)
        CPU_LIST[CONTAINER] += CPU
        CPU_LIST2[CONTAINER] += CPU

        #Memory Usage
        MEM= LL[2]
        if("GiB" in MEM):
            MEM= MEM.lstrip("'").rstrip("GiB'")
            MEM = float(MEM) * 1024
        else:
            MEM= MEM.lstrip("'").rstrip("MiB'")
            MEM = float(MEM)
        MEM_LIST[CONTAINER] += MEM
        
        #Stop container
        if((CPU_LIST[CONTAINER] / TIME_LIST[CONTAINER]) <= MIN_CPU and (MEM_LIST[CONTAINER] / TIME_LIST[CONTAINER]) >= 30720 and TIME_LIST[CONTAINER] >= MAX_SEC):
            json="{'text': 'Container %s used %.2fMiB of Memory with using average %.2fpercent of CPU Util. Container was stopped.'}" %(CONTAINER, MEM_LIST[CONTAINER] / TIME_LIST[CONTAINER], CPU_LIST[CONTAINER] / TIME_LIST[CONTAINER])
            response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=json)
            stop= "docker stop %s" %(CONTAINER)
            subprocess.run(stop, shell=True)
            del(CPU_LIST[CONTAINER])
            del(MEM_LIST[CONTAINER])
            del(TIME_LIST[CONTAINER])
        elif((CPU_LIST2[CONTAINER] / TIME_LIST2[CONTAINER]) <= MIN_CPU2 and TIME_LIST2[CONTAINER] >= MAX_SEC2):
            json="{'text': 'Container %s used average %.2fpercent of CPU Util. Container was stopped.'}" %(CONTAINER, CPU_LIST[CONTAINER] / TIME_LIST[CONTAINER])
            response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=json)
            stop= "docker stop %s" %(CONTAINER)
            subprocess.run(stop, shell=True)
            del(CPU_LIST2[CONTAINER])
            del(TIME_LIST2[CONTAINER])
        elif(TIME_LIST[CONTAINER] >= MAX_SEC):
            CPU_LIST[CONTAINER] = 0
            MEM_LIST[CONTAINER] = 0
            TIME_LIST[CONTAINER] = 1
        elif(TIME_LIST2[CONTAINER] >= MAX_SEC2):
            CPU_LIST2[CONTAINER] = 0
            TIME_LIST2[CONTAINER] = 1
        else:
            TIME_LIST[CONTAINER] += time.time() - start
            TIME_LIST2[CONTAINER] += time.time() - start
