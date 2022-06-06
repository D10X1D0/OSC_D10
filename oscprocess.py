import asyncio

import janus
from pythonosc import udp_client

import myclasses
from printcolors import bcolors


def printprocess(msg) -> None:
    print(bcolors.HEADER2 + "OSCProc : " + bcolors.ENDC + str(msg))
def printprocesserr(msg) -> None:
    msg = bcolors.WARNING + msg + bcolors.ENDC
    printprocess(msg)

async def pulse(cli: udp_client.SimpleUDPClient, addr: str, timings):
    while True:
        printprocess("pulsing " + addr + str(timings))
        cli.send_message(addr, timings[1])
        await asyncio.sleep(timings[0])


async def startpulse(con: myclasses.MainData, cli: udp_client.SimpleUDPClient, loop) -> None:
    try:
        lconfig = myclasses.OscServerData().proces
        printprocess(lconfig)
        for i in range(len(lconfig) // 3):
            if i != 0:
                # any iteration past the first one
                a = i * 3
            else:
                # first iteration
                a = i
            taskname = lconfig[a+1]
            if taskname == "pulse":
                adres = lconfig[a]
                timing = lconfig[a+2]
                printprocess("registering pulse task " + str(i))
                asyncio.create_task(pulse(cli, adres, timing))
                #pulse(cli, adres, timing)
            printprocess(str(lconfig[a]) + "__" + str(taskname) +  "__" + str(lconfig[a+2]))
    except Exception as e:
        printprocess("Error creating pulse task" + str(e))


async def startrespond(q_com, cli: udp_client.SimpleUDPClient) -> None:
    while True:
        try:
            item = await q_com.get()
            taskname = item[1][0]
            if taskname == "respond":
                oscvalue = item[0]
                datain = item[1][1][0]
                if oscvalue == datain:
                    dataout = item[1][1][1]
                    adressout = item[1][1][2]
                    cli.send_message(adressout, dataout)
                    printprocess("respond : " + str(oscvalue) + " : " + str(adressout) + " : " + str(dataout))
            else:
                printprocess("NOT respond : " + str(taskname))
            q_com.task_done()
        except RuntimeError as e:
            printprocesserr("error in startrespond: " + str(e))
            pass


async def process(q_com: janus.AsyncQueue[int], config: myclasses.MainData, loop):
    try:
        printprocess("Procestask")
        cli = udp_client.SimpleUDPClient(config.mainconfig["OSCSendIP"], config.mainconfig["OSCSendPort"])
        # asyncio.get_running_loop().create_task()
        await startpulse(config, cli, loop)
        await startrespond(q_com, cli)
    except Exception as e:
        printprocess("Shutting down : " +str(e))

