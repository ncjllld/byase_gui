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

from typing import Optional, List

import pandas as pd
import wx
from wx.html2 import WebView
from wx.lib.mixins.listctrl import CheckListCtrlMixin

from .message import QueueMessageCenter
from .long_running import LongRunningTaskIndicatorPanel
from .result_panel import ResultPanelDelegate


class TaskDetailDataViewDelegate:
    """Task detail data view delegate."""
    def plot_check_changed(self):
        """When a check item status changed."""
        pass


class TaskDetailDataView(wx.ListCtrl, CheckListCtrlMixin):
    """Task detail data view.

    Attributes:
        df: The data frame.
    """

    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        CheckListCtrlMixin.__init__(self)

        self.df = None  # type: Optional[pd.DataFrame]
        self.delegate = None  # type: Optional[TaskDetailDataViewDelegate]

    def set_delegate(self, delegate: ResultPanelDelegate):
        """Set delegate."""
        self.delegate = delegate

    def OnCheckItem(self, index, flag):
        super().OnCheckItem(index, flag)
        if self.delegate is not None:
            self.delegate.plot_check_changed()

    def get_checked_items(self):
        """Get checked plot items."""
        df = self.df
        idxes = df.index
        items = []
        for i, idx in enumerate(idxes):
            if self.IsChecked(i):
                items.append(idx)
        return items

    def update_df(self, df: Optional[pd.DataFrame]):
        """Update data frame."""
        self.df = df
        self.update_display(None)

        for n_col in [1, 2]:
            self.SetColumnWidth(n_col, wx.LIST_AUTOSIZE)
        for n_col in range(3, df.shape[1]):
            self.SetColumnWidth(n_col, wx.LIST_AUTOSIZE_USEHEADER)

    def update_display(self, checked_items: Optional[List[int]]):
        """Update display."""
        self.ClearAll()
        if self.df is None:
            return
        delegate = self.delegate
        self.delegate = None

        df = self.df
        cols = df.columns.tolist()
        for i, col in enumerate(cols):
            self.InsertColumn(i, col)
        n_row, n_col = df.shape
        for i in range(n_row):
            data = []
            for j in range(n_col):
                val = df.iloc[i, j]
                if isinstance(val, float):
                    val = '{:.3f}'.format(val)
                else:
                    val = str(val)
                data.append(val)
            self.Append(data)
            if checked_items is None or df.index[i] in checked_items:
                self.CheckItem(i)
        for i, col in enumerate(cols):
            self.SetColumnWidth(i, wx.LIST_AUTOSIZE)
        self.delegate = delegate

    def all_checked_status_is_same(self) -> Optional[bool]:
        """If all checked status are the same.
        Returns:
            If all status are the same, return the status (checked / unchecked), else return None.
        """
        all_checked = None
        df = self.df
        n_row = df.shape[0]
        for i in range(n_row):
            checked = self.IsChecked(i)
            if all_checked is None:
                all_checked = checked
            elif all_checked != checked:
                all_checked = None
                break
        return all_checked

    def set_check_all(self, checked: bool):
        """Set check all / none."""
        if self.df is None:
            return
        df = self.df
        n_row = df.shape[0]
        for i in range(n_row):
            self.CheckItem(i, checked)


def _create_web_view(parent):
    """Create a web view."""
    web_view = WebView.New(parent)
    web_view.SetEditable(False)
    web_view.EnableContextMenu(False)
    return web_view


class PlotPanel(LongRunningTaskIndicatorPanel, ResultPanelDelegate, TaskDetailDataViewDelegate):
    """Plot panel.

    Attributes:
        loading_panel: Loading panel.
        task_label: Segment info label.

        toggle_select_all_check: Toggle select all button.
        task_data_view: Stats data view.

        plot_allele_1_input: Plot allele 1 input.
        plot_allele_2_check: Plot allele 2 checkbox.
        plot_allele_2_input: Plot allele 2 input.
        plot_expr_check: Plot expression checkbox.
        plot_cov_check: Plot coverages checkbox.
        plot_diff_check: Plot difference checkbox.

        zoom_original_size_input: Zoom to original size input.
        zoom_fit_width_input: Zoom to fit width input.

        plot_view: Plot view.
        reloading_without_cache: If the plot view is reloading without cache.
    """

    def __init__(self, parent, mc: QueueMessageCenter, log_text_field: wx.TextCtrl):
        super().__init__(parent, mc, log_text_field)

        self.result_dir = None
        self.task_id = None

        # loading panel.
        self.loading_panel = wx.Panel(self)
        self.task_label = wx.StaticText(self.loading_panel)

        # Plot options.
        self.plot_allele_1_input = wx.ComboBox(self.loading_panel)
        self.plot_allele_1_input.SetEditable(False)
        self.plot_allele_1_input.Bind(wx.EVT_COMBOBOX, self.on_plot_allele_1_input_changed)
        self.plot_allele_2_check = wx.CheckBox(self.loading_panel, label='vs')
        self.plot_allele_2_check.Bind(wx.EVT_CHECKBOX, self.on_plot_allele_2_checked)
        self.plot_allele_2_input = wx.ComboBox(self.loading_panel)
        self.plot_allele_2_input.SetEditable(False)
        self.plot_allele_2_input.Bind(wx.EVT_COMBOBOX, self.on_plot_allele_2_input_changed)

        self.plot_expr_check = wx.CheckBox(self.loading_panel, label='Show Expression')
        self.plot_cov_check = wx.CheckBox(self.loading_panel, label='Show Coverages')
        self.plot_diff_check = wx.CheckBox(self.loading_panel, label='Show Difference')
        for ctrl in [self.plot_expr_check, self.plot_cov_check, self.plot_diff_check]:
            ctrl.SetValue(True)
            ctrl.Bind(wx.EVT_CHECKBOX, self.on_plot_expr_cov_diff_checked)

        # Zoom options.
        zoom_label = wx.StaticText(self.loading_panel, label='Zoom:')
        self.zoom_original_size_input = wx.RadioButton(self.loading_panel, label='Original Size', style=wx.RB_GROUP)
        self.zoom_fit_width_input = wx.RadioButton(self.loading_panel, label='Fit Page Width')
        self.zoom_original_size_input.Bind(wx.EVT_RADIOBUTTON, self.on_zoom_changed)
        self.zoom_fit_width_input.Bind(wx.EVT_RADIOBUTTON, self.on_zoom_changed)
        self.zoom_fit_width_input.SetValue(True)

        # Stats data view.
        self.toggle_select_all_check = wx.CheckBox(self.loading_panel, label='Select All')
        self.toggle_select_all_check.SetValue(True)
        self.toggle_select_all_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_select_all_checked)
        self.task_data_view = TaskDetailDataView(self.loading_panel)
        self.task_data_view.SetMinSize((-1, 200))
        self.task_data_view.delegate = self

        # Plot view.
        self.plot_view = _create_web_view(self.loading_panel)
        self.plot_view.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.on_plot_view_loaded)
        self.reloading_without_cache = False

        # Plot control sizer.
        plot_control_sizer = wx.BoxSizer(wx.HORIZONTAL)
        plot_control_sizer.Add(self.toggle_select_all_check, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        plot_control_sizer.Add(self.plot_cov_check, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        plot_control_sizer.Add(self.plot_expr_check, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        plot_control_sizer.Add(self.plot_diff_check, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        plot_control_sizer.AddStretchSpacer(1)
        plot_control_sizer.Add(self.plot_allele_1_input, 0, wx.ALL, 5)
        plot_control_sizer.Add(self.plot_allele_2_check, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        plot_control_sizer.Add(self.plot_allele_2_input, 0, wx.ALL, 5)

        # Plot top sizer.
        plot_top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        plot_top_sizer.Add(self.task_label, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        plot_top_sizer.Add(zoom_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        plot_top_sizer.Add(self.zoom_original_size_input, 0, wx.ALL, 5)
        plot_top_sizer.Add(self.zoom_fit_width_input, 0, wx.ALL, 5)

        # Loading panel sizer.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(plot_top_sizer, 0, wx.ALL | wx.EXPAND, 0)
        sizer.Add(self.plot_view, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(wx.StaticLine(self.loading_panel), 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        sizer.Add(self.task_data_view, 0, wx.ALL | wx.EXPAND, 0)
        sizer.Add(plot_control_sizer, 0, wx.ALL | wx.EXPAND, 0)
        self.loading_panel.SetSizerAndFit(sizer)

        # Loading sizer.
        loading_sizer = self.create_loading_sizer()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticLine(self), 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        sizer.Add(loading_sizer, 1, wx.BOTTOM | wx.EXPAND, 0)
        self.SetSizerAndFit(sizer)

    def loading_widget(self):
        return self.loading_panel

    def plot_task(self, result_dir: str, task_id: str, task_detail: pd.DataFrame):
        self.result_dir = result_dir
        self.task_id = task_id

        self.start_task()
        self.plot_view.LoadURL('about:blank')
        self.reloading_without_cache = False

        self.task_label.SetLabel('Task ID: {}'.format(task_id))
        self.task_data_view.update_df(task_detail)

        ploidy = len([col for col in task_detail.columns if 'Allele 1 &' in col]) + 1
        self.plot_allele_1_input.Clear()
        self.plot_allele_2_input.Clear()
        for i in range(ploidy):
            self.plot_allele_1_input.Append('Allele {}'.format(i + 1))
            self.plot_allele_2_input.Append('Allele {}'.format(i + 1))
        self.plot_allele_1_input.Append('All alleles')
        self.plot_allele_1_input.SetSelection(ploidy)
        self.plot_allele_2_input.SetSelection(1)
        self.plot_allele_2_check.Enabled = False
        self.plot_allele_2_input.Enabled = False
        self.toggle_select_all_check.SetValue(True)

    def provide_tool(self):
        tool = 'plot'
        params = {
            'result_dir': self.result_dir,
            'task_id': self.task_id
        }
        return tool, params

    def handle_task_finished(self):
        super().handle_task_finished()

    def handle_data(self, data):
        if isinstance(data, tuple):
            key, val = data
            if key == 'html path':
                self.plot_view.LoadURL('file://' + val)

    def on_plot_view_loaded(self, event):
        """Plot web view loaded callback."""
        assert event
        if not self.reloading_without_cache:
            self.reloading_without_cache = True
            self.plot_view.Reload(wx.html2.WEBVIEW_RELOAD_NO_CACHE)
        else:
            self.reloading_without_cache = False
            self.update_plots()

    def on_toggle_select_all_checked(self, event):
        """Toggle select all checked callback."""
        assert event
        checked = self.toggle_select_all_check.IsChecked()
        self.task_data_view.set_check_all(checked)

    def plot_check_changed(self):
        all_checked_status = self.task_data_view.all_checked_status_is_same()
        all_checked = all_checked_status is not None and all_checked_status is True
        self.toggle_select_all_check.SetValue(all_checked)
        self.update_plots()

    def on_zoom_changed(self, event):
        """Zoom changed callback."""
        assert event
        self.update_plots()

    def on_plot_allele_1_input_changed(self, event):
        """Plot allele 1 changed callback."""
        assert event
        can_enable_plot_allele_2_input = self.plot_allele_1_input.GetValue() != 'All alleles'
        self.plot_allele_2_check.Enabled = can_enable_plot_allele_2_input
        self.plot_allele_2_input.Enabled = can_enable_plot_allele_2_input and self.plot_allele_2_check.IsChecked()
        self.update_plots()

    def on_plot_allele_2_input_changed(self, event):
        """Plot allele 2 changed callback."""
        assert event
        self.update_plots()

    def on_plot_allele_2_checked(self, event):
        """Plot allele 2 checked callback."""
        assert event
        self.plot_allele_2_input.Enabled = self.plot_allele_2_check.IsChecked()
        self.update_plots()

    def on_plot_expr_cov_diff_checked(self, event):
        """Plot expression, coverages, difference changed callback."""
        assert event
        self.update_plots()

    def update_plots(self):
        """Update plots."""
        if self.task_data_view.df is None:
            return

        if self.zoom_original_size_input.GetValue() is True:
            zoom = ''
        elif self.zoom_fit_width_input.GetValue() is True:
            zoom = '100%'
        else:
            assert False
        items = self.task_data_view.get_checked_items()

        plot_expr = self.plot_expr_check.IsChecked()
        plot_cov = self.plot_cov_check.IsChecked()
        plot_diff = self.plot_diff_check.IsChecked()

        all_alleles_selected = self.plot_allele_1_input.GetValue() == 'All alleles'
        if all_alleles_selected:
            if plot_expr:
                items.append('hist')
            if plot_cov:
                items.append('cov')
            if plot_diff:
                items.append('diff')
        else:
            allele_1 = int(self.plot_allele_1_input.GetValue().split(' ')[-1]) - 1
            if plot_expr:
                items.append('hist_{}'.format(allele_1))
            if plot_cov:
                items.append('cov_{}'.format(allele_1))
            if self.plot_allele_2_check.IsChecked():
                allele_2 = int(self.plot_allele_2_input.GetValue().split(' ')[-1]) - 1
                if plot_expr:
                    items.append('hist_{}'.format(allele_2))
                if plot_cov:
                    items.append('cov_{}'.format(allele_2))
                if plot_diff:
                    items.append('diff_{}_{}'.format(allele_1, allele_2))

        items = ['"{}"'.format(item) for item in items]
        script = 'update_plots("{}", [{}]);'.format(zoom, ', '.join(items))
        self.plot_view.RunScript(script)
