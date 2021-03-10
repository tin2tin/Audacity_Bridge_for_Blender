import sys, time


# Platform specific constants
if sys.platform == "win32":
    PIPE_TO_AUDACITY = "\\\\.\\pipe\\ToSrvPipe"
    PIPE_FROM_AUDACITY = "\\\\.\\pipe\\FromSrvPipe"
    EOL = "\r\n\0"
else:
    PIPE_TO_AUDACITY = "/tmp/audacity_script_pipe.to." + str(os.getuid())
    PIPE_FROM_AUDACITY = "/tmp/audacity_script_pipe.from." + str(os.getuid())
    EOL = "\n"
try:
    time.sleep(0.01)
    TOPIPE = open(PIPE_TO_AUDACITY, "w")
    print("-- File to write to has been opened")
    FROMPIPE = open(PIPE_FROM_AUDACITY, "r")
    print("-- File to read from has now been opened too\r\n")
except:
    print(
        "Unable to run. Ensure Audacity is running with mod-script-pipe. Or try to restart Blender."
    )


def send_command(command):
    """Send a command to Audacity."""
    print("Send: >>> " + command)
    TOPIPE.write(command + EOL)
    TOPIPE.flush()


def get_response():
    """Get response from Audacity."""
    line = FROMPIPE.readline()
    result = ""
    while True:
        result += line
        line = FROMPIPE.readline()
        print(f"Line read: [{line}]")
        if line == "\n":
            return result


def do_command(command):
    """Do the command. Return the response."""
    send_command(command)
    time.sleep(0.1)  # may be required on slow machines
    response = get_response()
    print("Rcvd: <<< " + response)
    return response