# This file is part of BYASE-GUI.
#
# BYASE-GUI is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# BYASE-GUI is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with BYASE-GUI.  If not, see <https://www.gnu.org/licenses/>.
#
# Author: Lili Dong
#

import os
from typing import Tuple, List

import wx
import wx.adv

from .message import QueueMessageCenter, OutputItem, Instruction


_INDICATOR_ANIMATION_PATH = '{}/imgs/Spinner.gif'.format(os.path.dirname(__file__))


class LongRunningTaskPanel(wx.Panel):
    """Panel base class to perform a long running task.

    Attributes:
        mc: Queue message center.
        log_text_field: The text field for logging.
        progress_label: The label for display status messages.
        disabling_elements: Elements that should be disabled when task is running.
        timer: The timer for periodically updating.
    """

    def __init__(self, parent, mc: QueueMessageCenter, log_text_field: wx.TextCtrl):
        super().__init__(parent)

        self.mc = mc
        self.log_text_field = log_text_field
        self.progress_label = None

        self.disabling_elements = []  # type: List[wx.Window]

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)

    def add_disabling_elements(self, elements: List[wx.Window]):
        """Add disabling elements."""
        for e in elements:
            self.disabling_elements.append(e)

    def start_task(self):
        """Start the long running task."""
        self.log_text_field.Clear()

        for e in self.disabling_elements:
            e.Enabled = False

        tools, params = self.provide_tool()
        self.mc.send_input(tools, params)
        self.timer.Start(100)

    def on_timer(self, event):
        """Timer callback."""
        assert event
        while True:
            item = self.mc.receive_output()  # type: OutputItem
            if item is None:
                break

            if item.log is not None:
                self.log_text_field.AppendText(item.log + '\n')
            if item.data is not None:
                self.handle_data(item.data)
            if item.progress_msg is not None:
                self.handle_progress_msg(item.progress_msg)
            if item.progress is not None:
                self.handle_progress(item.progress)

            if item.task_started:
                self.handle_task_started()
            if item.task_finished:
                self.timer.Stop()
                self.handle_task_finished()

    def validate_data(self):
        """Validate data."""
        pass

    def show_message(self):
        """Show message."""

    def handle_task_started(self):
        """Handle when task is started."""
        pass

    def handle_task_finished(self):
        """Handle when task is finished."""
        for e in self.disabling_elements:
            e.Enabled = True

    def provide_tool(self) -> Tuple[str, dict]:
        """Provide tool and params of the long running task."""
        pass

    def handle_data(self, data):
        """Handle when got data."""
        pass

    def handle_progress_msg(self, progress_msg):
        """Handle progress message."""
        self.progress_label.SetLabel(progress_msg)
        self.Layout()

    def handle_progress(self, progress):
        """Handle progress."""
        pass


class LongRunningTaskProgressPanel(LongRunningTaskPanel):
    """Panel for long running task with a progress bar.

    Attributes:
        determinate: The progress is determinate.
        start_button: The start task button.
        stop_button: The stop task button.
        progress_bar: The progress bar.
    """

    def __init__(self, parent, determinate: bool, mc: QueueMessageCenter, log_text_field: wx.TextCtrl):
        super().__init__(parent, mc, log_text_field)

        self.determinate = determinate

        self.progress_label = wx.StaticText(self, style=wx.ALIGN_CENTER)

        self.start_button = wx.Button(self, label='Start')
        self.start_button.Bind(wx.EVT_BUTTON, self.on_start_button)

        self.stop_button = wx.Button(self, label='Stop')
        self.stop_button.Bind(wx.EVT_BUTTON, self.on_stop_button)
        self.stop_button.Enabled = False

        self.progress_bar = wx.Gauge(self)

    def on_timer(self, event):
        super().on_timer(event)
        if not self.determinate:
            self.progress_bar.Pulse()

    def on_start_button(self, event):
        """Start button callback."""
        assert event
        self.start_button.Enabled = False
        self.handle_progress_msg('Processing...')
        self.handle_progress(0)
        self.start_task()

    def on_stop_button(self, event):
        """Stop button callback."""
        assert event
        self.stop_button.Enabled = False
        self.mc.handle_progress('Waiting backend process to respond...')
        self.mc.send_instruction(Instruction.TERMINATE)

    def handle_task_started(self):
        super().handle_task_started()
        self.stop_button.Enabled = True

    def handle_task_finished(self):
        super().handle_task_finished()
        self.start_button.Enabled = True
        self.stop_button.Enabled = False


class LongRunningTaskIndicatorPanel(LongRunningTaskPanel):
    """Panel for long running task with an indicator.

    Attributes:
        indicator: The running indicator.
        indicator_panel: The panel holding the indicator and progress label.
    """

    def __init__(self, parent, mc: QueueMessageCenter, log_text_field: wx.TextCtrl):
        super().__init__(parent, mc, log_text_field)

        self.indicator_panel = wx.Panel(self)

        self.indicator = wx.adv.AnimationCtrl(self.indicator_panel)
        self.indicator.LoadFile(_INDICATOR_ANIMATION_PATH)

        self.progress_label = wx.StaticText(self.indicator_panel, style=wx.ALIGN_CENTER)

        indicator_sizer = wx.BoxSizer(wx.VERTICAL)
        indicator_sizer.AddStretchSpacer(1)
        indicator_sizer.Add(self.indicator, 0, wx.ALL | wx.EXPAND, 0)
        indicator_sizer.Add(self.progress_label, 0, wx.ALL | wx.EXPAND, 0)
        indicator_sizer.AddStretchSpacer(1)

        self.indicator_panel.SetSizerAndFit(indicator_sizer)

    def create_loading_sizer(self) -> wx.BoxSizer:
        """Create a loading sizer.

        Note:
            The loading_widget must be created before the method call.
        """
        loading_sizer = wx.BoxSizer(wx.VERTICAL)
        loading_sizer.Add(self.loading_widget(), 1, wx.ALL | wx.EXPAND, 0)
        loading_sizer.Add(self.indicator_panel, 1, wx.ALL | wx.EXPAND, 0)
        self.indicator_panel.Hide()
        return loading_sizer

    def loading_widget(self) -> wx.Window:
        """Return the widget for which the long running task performs."""
        pass

    def start_task(self):
        super().start_task()
        self.loading_widget().Hide()
        self.indicator_panel.Show()
        self.indicator.Play()
        self.handle_progress_msg('Loading...')
        self.Layout()

    def handle_task_finished(self):
        super().handle_task_finished()
        self.loading_widget().Show()
        self.indicator_panel.Hide()
        self.indicator.Stop()
        self.handle_progress_msg('')
        self.Layout()
