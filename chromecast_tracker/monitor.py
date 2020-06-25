import pychromecast
import cmd
import threading
import time
import os
import pathlib
import datetime
from copy import deepcopy


class MonitorThread(threading.Thread):
    UPDATE_DEVICES_PERIOD = 10.0

    def __init__(self):
        super(MonitorThread, self).__init__()
        self.stop_event = threading.Event()
        self.devices_lock = threading.Lock()
        self._devices = []

    @property
    def devices(self):
        with self.devices_lock:
            return [{key: getattr(cc.device, key) for key in ["friendly_name", "uuid"]}
                    for cc in self._devices]

    def _update_devices(self):
        with self.devices_lock:
            self._devices = pychromecast.get_chromecasts()

    def stop(self):
        self.stop_event.set()

    def run(self) -> None:
        last_devices_update = None
        while not self.stop_event.is_set():
            now = time.clock()
            if (last_devices_update is None) or (
                    now - last_devices_update >= self.UPDATE_DEVICES_PERIOD):
                last_devices_update = now
                self._update_devices()

# class MonitorShell(cmd.Cmd):
#     intro = ('Ready to monitor chromecast and maanage recordings.\n'
#              'Type help or ? to list commands.\n')
#     prompt = '(monitor) '
#     options = {}
#     active = None
#     active_id = None
#     active_title = None
#     destination = None
#     destination_root = os.path.join(pathlib.Path.home(), "Recordings")
#     date_fmt = "%Y-%m-%d_%H-%M-%S"
#
#     def do_bye(self, _):
#         """ Stop recording, close the window, and exit """
#         print('Peace Love Unity Respect')
#         # self.close()
#         return True
#
#     def _print_options(self):
#         print("\n".join(f"({k}): {self.options[k].device.friendly_name}"
#                         for k in sorted(self.options)))
#
#     def do_monitor(self, arg):
#         if self.active:
#             friendly_name = self.active.device.friendly_name
#             print(f"Monitor already active on {friendly_name}")
#             return
#
#         self._update_options()
#
#         try:
#             selection = int(arg)
#             if selection > 0:
#                 friendly_name = self.options[selection]
#             else:
#                 print(f"Selection out of bounds '{arg}'")
#                 self._print_options()
#                 return
#         except ValueError:
#             try:
#                 selection = min(k for k in self.options
#                                 if self.options[k].device.friendly_name == arg)
#                 friendly_name = self.options[selection]
#             except ValueError:
#                 print(f"Failed to parse selection '{arg}'")
#                 self._print_options()
#                 return
#         except KeyError:
#             print(f"Selection out of bounds '{arg}'")
#             self._print_options()
#             return
#
#         self.active = self.options[selection]
#         self._start_thread()
#         print(f"Monitor started on {self.active.device.friendly_name}")
#
#     #-- helper methods
#     def _start_thread(self):
#         self.active_id = None
#         self.active_title = None
#         self.destination = os.path.join(self.destination_root,
#                                         self.active.device.friendly_name)
#         os.makedirs(self.destination, exist_ok=True)
#         thread = threading.Thread(target=self._monitor)
#         thread.start()
#
#     def _set_active_content(self, content_id: str, title: str):
#         if content_id != self.active_id:
#             self.active_id = content_id
#             self.active_title = title
#             now = datetime.datetime.now()
#             print(f"[{now}] Video changed: '{title}' ({content_id})")
#             file_name = now.strftime(self.date_fmt) + ".txt"
#             path_file = os.path.join(self.destination, file_name)
#             with open(path_file, "w") as file:
#                 file.write(f"https://www.youtube.com/watch?v={content_id}\n")
#                 file.write(f"{title}\n")
#
#     def _monitor(self):
#         self.active.wait()
#         mc = self.active.media_controller
#         while True:
#             cur_id = mc.status.content_id
#             if cur_id != self.active_id:
#                 self._set_active_content(cur_id, mc.status.title)
#             time.sleep(1.0)
#
#
# if __name__ == '__main__':
#     MonitorShell().cmdloop()
