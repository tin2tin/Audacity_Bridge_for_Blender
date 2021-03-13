import bpy, sys, time, os

from .addon_prefs import get_addon_preferences


TOPIPE = FROMPIPE = EOL = None

def return_audacity_pipe():
    TOPIPE = None
    FROMPIPE = None
    EOL = None       
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
        # print("Audacity Tools --- File to write to has been opened")
        FROMPIPE = open(PIPE_FROM_AUDACITY, "r")
        # print("Audacity Tools --- File to read from has now been opened too\r\n")
    except:
        pass
        # print("Audacity Tools --- Unable to run. Ensure Audacity is running with mod-script-pipe. Or try to restart Blender.")
    
    return TOPIPE, FROMPIPE, EOL


def check_set_pipe(launch=True):
    print("Audacity Tools --- Looking for Audacity pipe")

    winman = bpy.data.window_managers[0]

    global TOPIPE
    global FROMPIPE
    global EOL

    if TOPIPE is not None:
        try:
            TOPIPE.write("ToggleScrubRuler:" + EOL)
            TOPIPE.write("ToggleScrubRuler:" + EOL)
            TOPIPE.flush()
            winman.audacity_tools_pipe_available = True
            return True
        except OSError:
            pass

    _to, _from, _eol = return_audacity_pipe()
    if _to is not None:
        TOPIPE = _to
        FROMPIPE = _from
        EOL = _eol
        winman.audacity_tools_pipe_available = True
        return True

    elif launch:
        print("Audacity Tools --- Trying to launch Audacity")
        if launch_audacity():
            time.sleep(get_addon_preferences().audacity_waiting_time)
            _to, _from, _eol = return_audacity_pipe()
            if _to is not None:
                TOPIPE = _to
                FROMPIPE = _from
                EOL = _eol
                winman.audacity_tools_pipe_available = True
                return True

    winman.audacity_tools_pipe_available = False
    return False


def check_pipe():
    winman = bpy.data.window_managers[0]
    if TOPIPE is not None:
        try:
            TOPIPE.write("ToggleScrubRuler:" + EOL)
            TOPIPE.write("ToggleScrubRuler:" + EOL)
            TOPIPE.flush()
            winman.audacity_tools_pipe_available = True
            return True
        except OSError:
            pass
    winman.audacity_tools_pipe_available = False   
    return False


def launch_audacity():
    app_path = get_addon_preferences().audacity_executable
    if os.path.isfile(app_path):
        os.startfile(app_path)
        return True
    else:
        return False


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
        #print(f"Line read: [{line}]")
        if line == "\n":
            return result


def do_command(command):
    """Do the command. Return the response."""
    send_command(command)
    time.sleep(0.1)  # may be required on slow machines
    response = get_response()
    print("Rcvd: <<< " + response)
    return response