from win10toast import ToastNotifier
from api import move_zoom_events
toast = ToastNotifier()
try:
	new_events = move_zoom_events(toast)
	if len(new_events) != 0:
		message = f"{len(new_events)} events were moved to your primary calendar:\n"
		message += "\n".join(new_events)
		toast.show_toast("Events Moved", message, duration=3+3*len(new_events), icon_path="data/MoveZoomEvents.ico", threaded=True)
except BaseException as e:
	toast.show_toast("Error Encountered", str(e), duration=15, icon_path="data/MoveZoomEvents.ico", threaded=True)