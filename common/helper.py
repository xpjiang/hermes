import asyncio
import threading

import graphyte


# Global variable to broadcast when the process should terminate
terminate = False
loop = asyncio.get_event_loop()


def triggerTerminate():
    """Trigger that the processing loop should terminate after finishing the currently active task."""
    global terminate
    terminate = True


def isTerminated():
    """Checks if the process will terminate after the current task."""
    return terminate


async def sendToGraphite(*args, **kwargs):
    """Wrapper for asynchronous graphite call to avoid wait time of main loop."""
    if graphyte.default_sender == None:
        return
    graphyte.default_sender.send(*args, **kwargs)


def g_log(*args, **kwargs):
    """Sends diagnostic information to graphite (if configured)."""
    asyncio.run_coroutine_threadsafe(sendToGraphite(*args, **kwargs), loop)


class RepeatedTimer(object):
    """
    Helper class for running a continuous timer that is suspended
    while the worker function is running
    """
    def __init__(self, interval, function, exit_function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.exit_function = exit_function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False

    def _run(self):
        """Callback function for the timer event. Will execute the defined function and restart
           the timer after completion, unless the eventloop has been asked to shut down."""
        global terminate
        self.is_running = False
        self.function(*self.args, **self.kwargs)
        if not terminate:
            self.start()
        else:
            self.exit_function(*self.args, **self.kwargs)

    def start(self):
        """Starts the timer for triggering the calllback after the defined interval."""
        if not self.is_running:
            self._timer = threading.Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        """Stops the timer and executes the defined exit callback function."""
        self._timer.cancel()
        self.is_running = False
        self.exit_function(*self.args, **self.kwargs)
