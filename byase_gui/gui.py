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

import multiprocessing as mp

import psutil
import wx

from .message import QueueMessageCenter
from .task import task
from .log_pane import LogPane
from .annotation_panel import AnnotationPanel
from .inference_panel import InferencePanel
from .result_panel import ResultPanel
from .plot_panel import PlotPanel


class Frame(wx.Frame):
    """Main frame.

    Attributes:
        panel: Main panel.
        log_pane: The log pane.
        notebook: The notebook.
    """

    def __init__(self, mc: QueueMessageCenter):
        super().__init__(None, title='BYASE GUI')

        self.panel = wx.Panel(self)

        self.log_pane = LogPane(self.panel)
        self.log_pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.log_pane_toggled)

        log_text_field = self.log_pane.log_text_field

        self.notebook = wx.Notebook(self.panel)
        annotation_panel = AnnotationPanel(self.notebook, mc, log_text_field)
        inference_panel = InferencePanel(self.notebook, mc, log_text_field)
        result_panel = ResultPanel(self.notebook, mc, log_text_field)
        plot_panel = PlotPanel(self.notebook, mc, log_text_field)

        result_panel.set_delegate(plot_panel)

        annotation_panel.add_disabling_elements([inference_panel, result_panel, plot_panel])
        inference_panel.add_disabling_elements([annotation_panel, result_panel, plot_panel])
        result_panel.add_disabling_elements([annotation_panel, inference_panel, plot_panel])
        plot_panel.add_disabling_elements([annotation_panel, inference_panel, result_panel])

        self.notebook.AddPage(annotation_panel, 'Generate Tasks')
        self.notebook.AddPage(inference_panel, 'Inference')
        self.notebook.AddPage(result_panel, 'Results')
        self.notebook.AddPage(plot_panel, 'Plot')

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 3, wx.ALL | wx.EXPAND, 5)
        sizer.Add(self.log_pane, 0, wx.ALL | wx.EXPAND, 5)
        self.panel.SetSizerAndFit(sizer)
        sizer.Fit(self)

        self.SetMinSize(self.GetSize())

    def log_pane_toggled(self, event):
        assert event
        self.panel.Layout()


def main():
    mc = QueueMessageCenter()

    work_process = mp.Process(target=task, args=(mc, ))
    work_process.start()

    app = wx.App()
    frame = Frame(mc)
    frame.Show()
    app.MainLoop()

    for child in psutil.Process(work_process.pid).children(recursive=True):
        child.kill()
    work_process.terminate()
