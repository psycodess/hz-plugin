"""
Tests for hz-plugin (main.py).

Run with:
    python -m pytest tests/ -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import types

# ---------------------------------------------------------------------------
# Make the lib directory discoverable without a real Flow Launcher runtime
# ---------------------------------------------------------------------------
plugindir = Path(__file__).parent.parent
sys.path.insert(0, str(plugindir))
sys.path.insert(0, str(plugindir / "lib"))

# Stub out win32api and win32con before importing main so we can run tests
# without a Windows environment (CI, etc.)
_win32api = types.ModuleType("win32api")
_win32con = types.ModuleType("win32con")

# Constants used in main.py
_win32con.ENUM_CURRENT_SETTINGS = -1
_win32con.DISP_CHANGE_SUCCESSFUL = 0
_win32con.DISP_CHANGE_RESTART = 1
_win32con.DISP_CHANGE_FAILED = -1
_win32con.DISP_CHANGE_BADMODE = -2
_win32con.DISP_CHANGE_NOTUPDATED = -3
_win32con.DISP_CHANGE_BADFLAGS = -4
_win32con.DISP_CHANGE_BADPARAM = -5
_win32con.DISP_CHANGE_BADDUALVIEW = -6

sys.modules.setdefault("win32api", _win32api)
sys.modules.setdefault("win32con", _win32con)

# Stub flowlauncher
_fl = types.ModuleType("flowlauncher")

class _FlowLauncher:
    rpc_request: dict = {}
    def __init__(self): pass

class _FlowLauncherAPI:
    @staticmethod
    def show_msg(title, subtitle="", iconPath="", useMainWindowAsParent=True):
        pass

_fl.FlowLauncher = _FlowLauncher
_fl.FlowLauncherAPI = _FlowLauncherAPI
sys.modules.setdefault("flowlauncher", _fl)

# Now safe to import
import main  # noqa: E402


# ---------------------------------------------------------------------------
# _disp_change_message
# ---------------------------------------------------------------------------

def test_disp_change_message_known_codes():
    assert "successfully" in main._disp_change_message(0).lower()
    assert "restart" in main._disp_change_message(1).lower()
    assert "driver rejected" in main._disp_change_message(-1).lower()


def test_disp_change_message_unknown_code():
    msg = main._disp_change_message(999)
    assert "999" in msg


# ---------------------------------------------------------------------------
# _parse_keyword
# ---------------------------------------------------------------------------

def _mock_devices(names):
    """Return a context manager that patches get_display_device_names."""
    return patch("main.get_display_device_names", return_value=names)


def test_parse_keyword_hz_no_devices():
    with _mock_devices([]):
        idx, dev = main._parse_keyword("hz")
    assert idx == 0
    assert dev is None


def test_parse_keyword_hz_primary():
    with _mock_devices([r"\\.\DISPLAY1", r"\\.\DISPLAY2"]):
        idx, dev = main._parse_keyword("hz")
    assert idx == 0
    assert dev is None   # primary → None


def test_parse_keyword_hz1_primary():
    with _mock_devices([r"\\.\DISPLAY1", r"\\.\DISPLAY2"]):
        idx, dev = main._parse_keyword("hz1")
    assert idx == 0
    assert dev is None


def test_parse_keyword_hz2_second_monitor():
    with _mock_devices([r"\\.\DISPLAY1", r"\\.\DISPLAY2"]):
        idx, dev = main._parse_keyword("hz2")
    assert idx == 1
    assert dev == r"\\.\DISPLAY2"


def test_parse_keyword_out_of_range_clamps():
    """Asking for hz99 when only 2 monitors exist should return the last monitor."""
    with _mock_devices([r"\\.\DISPLAY1", r"\\.\DISPLAY2"]):
        idx, dev = main._parse_keyword("hz99")
    assert idx == 1


def test_parse_keyword_invalid_suffix():
    with _mock_devices([r"\\.\DISPLAY1"]):
        idx, dev = main._parse_keyword("hzXYZ")
    assert idx == 0


# ---------------------------------------------------------------------------
# get_available_rates / get_current_rate
# ---------------------------------------------------------------------------

def _make_devmode(freq: int):
    dm = MagicMock()
    dm.DisplayFrequency = freq
    return dm


def test_get_available_rates_deduplicates_and_sorts():
    freqs = [60, 60, 144, 120, 120, 240]
    call_count = 0

    def fake_enum(device, i):
        nonlocal call_count
        if i < len(freqs):
            call_count += 1
            return _make_devmode(freqs[i])
        raise Exception("end")

    with patch("main.win32api.EnumDisplaySettings", side_effect=fake_enum):
        rates = main.get_available_rates(None)

    assert rates == [60, 120, 144, 240]


def test_get_current_rate():
    with patch("main.win32api.EnumDisplaySettings", return_value=_make_devmode(144)):
        assert main.get_current_rate(None) == 144


# ---------------------------------------------------------------------------
# set_refresh_rate – validation
# ---------------------------------------------------------------------------

def test_set_refresh_rate_unsupported_raises():
    with patch("main.get_available_rates", return_value=[60, 144]):
        try:
            main.set_refresh_rate(None, 999)
            assert False, "Expected ValueError"
        except ValueError as exc:
            assert "999Hz is not supported" in str(exc)


def test_set_refresh_rate_already_current():
    with patch("main.get_available_rates", return_value=[60, 144]), \
         patch("main.get_current_rate", return_value=144):
        result = main.set_refresh_rate(None, 144)
    assert "already" in result.lower()


def test_set_refresh_rate_successful():
    dm = _make_devmode(60)
    with patch("main.get_available_rates", return_value=[60, 144]), \
         patch("main.get_current_rate", return_value=60), \
         patch("main.win32api.EnumDisplaySettings", return_value=dm), \
         patch("main.win32api.ChangeDisplaySettings", return_value=0) as mock_cds:
        result = main.set_refresh_rate(None, 144)

    assert mock_cds.called
    assert "successfully" in result.lower()


def test_set_refresh_rate_uses_changedisplaysettingsex_for_secondary():
    dm = _make_devmode(60)
    with patch("main.get_available_rates", return_value=[60, 144]), \
         patch("main.get_current_rate", return_value=60), \
         patch("main.win32api.EnumDisplaySettings", return_value=dm), \
         patch("main.win32api.ChangeDisplaySettingsEx", return_value=0) as mock_cdex, \
         patch("main.win32api.ChangeDisplaySettings") as mock_cds:
        main.set_refresh_rate(r"\\.\DISPLAY2", 144)

    assert mock_cdex.called
    assert not mock_cds.called


# ---------------------------------------------------------------------------
# RefreshRatePlugin.query – input validation
# ---------------------------------------------------------------------------

def _make_plugin():
    p = main.RefreshRatePlugin.__new__(main.RefreshRatePlugin)
    p.rpc_request = {"keyword": "hz"}
    return p


def test_query_rejects_non_numeric_input():
    plugin = _make_plugin()
    with patch("main.get_display_device_names", return_value=[]):
        results = plugin.query("abc")
    assert results[0]["title"] == "Invalid input"


def test_query_no_results_for_unmatched_filter():
    plugin = _make_plugin()
    with patch("main.get_display_device_names", return_value=[]), \
         patch("main.get_available_rates", return_value=[60, 144]), \
         patch("main.get_current_rate", return_value=60):
        results = plugin.query("999")
    assert "No" in results[0]["title"]


def test_query_shows_checkmark_for_active_rate():
    plugin = _make_plugin()
    with patch("main.get_display_device_names", return_value=[]), \
         patch("main.get_available_rates", return_value=[60, 144]), \
         patch("main.get_current_rate", return_value=144):
        results = plugin.query("")
    active = [r for r in results if "144" in r["title"] and "✓" in r["title"]]
    assert active, "Active rate should have a checkmark"


def test_query_empty_shows_all_rates():
    plugin = _make_plugin()
    with patch("main.get_display_device_names", return_value=[]), \
         patch("main.get_available_rates", return_value=[60, 120, 144, 240]), \
         patch("main.get_current_rate", return_value=60):
        results = plugin.query("")
    assert len(results) == 4


# ---------------------------------------------------------------------------
# RefreshRatePlugin.change_rate – validation
# ---------------------------------------------------------------------------

def test_change_rate_rejects_zero():
    plugin = _make_plugin()
    with patch.object(main.FlowLauncherAPI, "show_msg") as mock_msg:
        plugin.change_rate("hz", "0")
    mock_msg.assert_called_once()
    assert "Invalid" in mock_msg.call_args[0][0]


def test_change_rate_rejects_non_digit():
    plugin = _make_plugin()
    with patch.object(main.FlowLauncherAPI, "show_msg") as mock_msg:
        plugin.change_rate("hz", "abc")
    mock_msg.assert_called_once()


def test_change_rate_calls_set_refresh_rate():
    plugin = _make_plugin()
    with patch("main.set_refresh_rate", return_value="Refresh rate changed successfully") as mock_set, \
         patch("main.get_display_device_names", return_value=[]), \
         patch.object(main.FlowLauncherAPI, "show_msg"):
        plugin.change_rate("hz", "144")
    mock_set.assert_called_once_with(None, 144)
