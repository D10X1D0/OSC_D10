from typing import Any
import asyncio
import janus
from pythonosc import udp_client
import printcolors
from printcolors import bcolors
import myclasses


def printprocess(msg) -> None:
    """Helper function to print with colors"""
    print(f"{bcolors.HEADER2} OSCProc : {bcolors.ENDC} {msg}")


def printprocesserr(msg) -> None:
    """Helper function to print with colors"""
    printprocess(f"{bcolors.WARNING} {msg} {bcolors.ENDC}")


async def pulse(cli: udp_client.SimpleUDPClient, addr: str, timings):
    """Sends a value every X seconds to an OSC adress, should be run a task"""
    while True:
        printprocess(f"pulsing {addr}  delay {timings[0]} s : value {timings[1]} : type {type(timings[1]).__name__}")
        cli.send_message(addr, timings[1])
        await asyncio.sleep(timings[0])


async def startpulse(con: myclasses.MainData, cli: udp_client.SimpleUDPClient) -> None:
    """Creates and starts running pulse takss from the configured commands."""
    try:
        lconfig = myclasses.OscServerData().proces
        # printprocess(lconfig)
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
                timings = lconfig[a+2]
                if float(timings[0]) > 0.1:
                    printprocess(f"registering pulse task {i}")
                    asyncio.create_task(pulse(cli, adres, timings))
                    printprocess(f"{lconfig[a]}__{taskname}__{lconfig[a + 2]}")
                else:
                    printprocess(f"{printcolors.bcolors.FAIL}pulse too fast, faster than 0.1s, "
                                 f"skipping it timing: {timings} {printcolors.bcolors.FAIL}")

    except Exception as e:
        printprocess(f"Error creating pulse task {e}")


async def startrespond(q_com, cli: udp_client.SimpleUDPClient) -> None:
    """Starts respond, reads an OSC value and sends another back to the same direction"""
    while True:
        try:
            item = await q_com.get()
            taskname = item[1][0]
            if taskname == "respond":
                oscvalue = item[0]
                if isinstance(oscvalue, float):
                    # if we get a float, we round it to 2 decimals
                    oscvalue = round(oscvalue, 2)
                # printprocesserr(str(oscvalue))
                datain = item[1][1][0]
                if oscvalue == datain:
                    dataout = item[1][1][1]
                    adressout = item[1][1][2]
                    if isinstance(dataout, float):
                        dataout = round(dataout, 2)
                    cli.send_message(adressout, dataout)
                    printprocess("respond : " + str(oscvalue)
                                 + " : " + str(adressout)
                                 + " : " + str(dataout) + str(type(dataout)))
            else:
                printprocess(f"NOT respond : {taskname}")
            q_com.task_done()
        except RuntimeError as e:
            printprocesserr(f"error in startrespond: {e}")
            pass


async def process(q_com: janus.AsyncQueue[Any], config: myclasses.MainData.mainconfig):
    """configures and starts process taks : pulse, and respond"""
    try:
        printprocess("Procestask")
        cli = udp_client.SimpleUDPClient(config.mainconfig["OSCSendIP"], config.mainconfig["OSCSendPort"])
        await startpulse(config, cli)
        await startrespond(q_com, cli)
    except Exception as e:
        printprocess(f"Shutting down : {e}")
