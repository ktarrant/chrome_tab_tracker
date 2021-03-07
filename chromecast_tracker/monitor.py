import pychromecast
import threading
import time
import logging
import pprint
from typing import List, Dict

logger = logging.getLogger(__name__)


def get_device_info(cast: pychromecast.Chromecast) -> Dict[str, str]:
    return {'uuid': cast.device.uuid, 'name': cast.device.friendly_name}


def find_differences(actual: Dict, expected: Dict):
    differences = {}
    for key in actual:
        actual_value = actual[key]
        if isinstance(actual_value, dict):
            expected_value = expected.get(key, {})
            difference = find_differences(actual_value, expected_value)
            if difference:
                differences[key] = difference
        else:
            try:
                expected_value = expected[key]
                if expected_value != actual_value:
                    differences[key] = actual_value
            except KeyError:
                differences[key] = actual_value
    return differences


class MonitorThread(threading.Thread):
    UPDATE_DEVICES_PERIOD = 10.0
    UPDATE_STATUS_PERIOD = 1.0

    def __init__(self):
        super(MonitorThread, self).__init__()
        self.stop_event = threading.Event()
        self.cast_list_lock = threading.Lock()
        self.cast_list = []
        self.last_statuses = {}

    def update_devices(self):
        last_list = [cast.device.friendly_name for cast in self.cast_list]
        with self.cast_list_lock:
            self.cast_list, cast_browser = pychromecast.get_chromecasts()
        name_list = [cast.device.friendly_name for cast in self.cast_list]
        casts_added = [cast.device.friendly_name for cast in self.cast_list
                       if cast.device.friendly_name not in last_list]
        casts_removed = [name for name in last_list if name not in name_list]
        rv = {}
        if casts_added:
            logger.info(f"Casts added: {casts_added}")
            rv["added"] = casts_added
        if casts_removed:
            logger.info(f"Casts removed: {casts_removed}")
            rv["removed"] = casts_removed
        return rv

    def update_statuses(self, retries=1):
        cur_statuses = {}
        with self.cast_list_lock:
            for cast in self.cast_list:
                for i in range(retries + 1):
                    cast.wait()
                    mc = cast.media_controller
                    if mc.status.last_updated is None:
                        continue
                    cur_statuses[cast.device.friendly_name] = {
                        'content_id': mc.status.content_id,
                        'content_type': mc.status.content_type,
                        'duration': mc.status.duration,
                        'title': mc.status.title,
                    }

        status_changes = find_differences(cur_statuses, self.last_statuses)
        self.last_statuses = cur_statuses

        if status_changes:
            logger.info("Updated statuses:\n" + pprint.pformat(status_changes))

        return status_changes

    def stop(self):
        self.stop_event.set()

    def run(self) -> None:
        last_devices_update = None
        last_status_update = None
        while not self.stop_event.is_set():
            now = time.perf_counter()
            if (last_devices_update is None) or (
                    now - last_devices_update >= self.UPDATE_DEVICES_PERIOD):
                last_devices_update = now
                self.update_devices()

            if (last_status_update is None) or (
                    now - last_status_update >= self.UPDATE_STATUS_PERIOD):
                last_status_update = now
                self.update_statuses()

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


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    thread = MonitorThread()
    thread.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Stopping thread...")
        thread.stop()
