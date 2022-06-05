import asyncio

import janus
from pythonosc import udp_client

import myclasses
from printcolors import bcolors


def printprocess(msg) -> None:
    print(bcolors.HEADER2 + "OSCProc : " + bcolors.ENDC + str(msg))


async def pulse(cli: udp_client.SimpleUDPClient, addr: str, timings):
    while True:
        printprocess("pulsing " + addr + str(timings))
        cli.send_message(addr, timings[1])
        await asyncio.sleep(timings[0])


async def startpulse(con: myclasses.MainData, loop):
    try:
        lconfig = myclasses.OscServerData().proces
        cli = udp_client.SimpleUDPClient(con.mainconfig["OSCSendIP"], con.mainconfig["OSCSendPort"])
        print(lconfig)
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
            print(str(lconfig[a]) + "__" + str(taskname) +  "__" + str(lconfig[a+2]))
    except Exception as e:
        printprocess("Error creating pulse task" + str(e))


async def process(q_com: janus.AsyncQueue[int], config: myclasses.MainData, loop):
    printprocess("Procestask")
    # asyncio.get_running_loop().create_task()
    await startpulse(config, loop)
    """ loop to process queque items, not used yet
    while True:
        try:
            #printprocess("await q_com.get()")
            item = await q_com.get()
            #printprocess("procestask got an item in the queue")
            #printprocess(item)
            item = str(item) + "_resend"
            q_com.task_done()
        except RuntimeError as e :
            printprocess("error" + str(e))
            pass
    """
