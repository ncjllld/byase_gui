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
from typing import List, Optional

import wx
from wx.lib.intctrl import IntCtrl

from .message import QueueMessageCenter
from .long_running import LongRunningTaskIndicatorPanel, LongRunningTaskProgressPanel
from .data_view import DataView


class TaskDataView(DataView):
    """Task data view."""

    def set_task_status(self, task_id: str, status: str):
        """Set task status."""
        for i in range(self.df.shape[0]):
            if self.df.loc[i, 'Task ID'] == task_id:
                self.df.loc[i, 'Status'] = status
                self.RefreshItem(i)
                self.EnsureVisible(i)
                break


class _ConfigPanelDelegate:
    """Config panel delegate."""

    def tasks_start_loading(self):
        """Tasks start loading."""
        pass

    def tasks_loaded(self):
        """Tasks loaded."""
        pass


class _ConfigPanel(LongRunningTaskIndicatorPanel):
    """Config panel.

    Attributes:
        task_dir_input: Task directory input.
        task_data_view: Annotation data view.
        delegate: Delegate.
        bam_paths: Paths of BAMs.
        bams_input: BAM files input.
        select_bams_button: Select BAMs button.
        read_len_input: Read length input.
        se_input: Single-end input.
        pe_input: Paired-end input.
        insert_size_mean_input: Insert-size mean input.
        insert_size_std_input: Insert-size std input.
        resume_checkbox: Resume mode checkbox.
    """

    def __init__(self, parent, mc: QueueMessageCenter, log_text_field: wx.TextCtrl):
        super().__init__(parent, mc, log_text_field)

        self.config_sub_panel = wx.Panel(self)

        # Tasks.
        task_dir_label = wx.StaticText(self.config_sub_panel, label='Task Directory:')
        self.task_dir_input = wx.DirPickerCtrl(self.config_sub_panel)
        self.task_dir_input.Bind(wx.EVT_DIRPICKER_CHANGED, self.on_select_task_dir)
        self.task_data_view = TaskDataView(self, sortable=False)

        # BAMs.
        self.bam_paths = None
        bams_label = wx.StaticText(self.config_sub_panel, label='BAM Files:')
        self.bams_input = wx.TextCtrl(self.config_sub_panel, style=wx.TE_READONLY)
        self.select_bams_button = wx.Button(self.config_sub_panel, label='Browse')
        self.select_bams_button.Bind(wx.EVT_BUTTON, self.on_select_bams)

        read_len_label = wx.StaticText(self.config_sub_panel, label='Read Length:')
        self.read_len_input = IntCtrl(self.config_sub_panel, min=0)
        self.se_input = wx.RadioButton(self.config_sub_panel, label='Single-End', style=wx.RB_GROUP)
        self.se_input.Bind(wx.EVT_RADIOBUTTON, self.on_seq_type_changed)
        self.pe_input = wx.RadioButton(self.config_sub_panel, label='Paired-End')
        self.pe_input.Bind(wx.EVT_RADIOBUTTON, self.on_seq_type_changed)
        insert_size_mean_label = wx.StaticText(self.config_sub_panel, label='Insert-Size Mean:')
        self.insert_size_mean_input = wx.TextCtrl(self.config_sub_panel)
        insert_size_std_label = wx.StaticText(self.config_sub_panel, label='Standard Deviation:')
        self.insert_size_std_input = wx.TextCtrl(self.config_sub_panel)
        self.insert_size_mean_input.Enabled = False
        self.insert_size_std_input.Enabled = False

        # Settings.
        parallel_label = wx.StaticText(self.config_sub_panel, label='Parallel Process:')
        self.parallel_input = wx.SpinCtrl(self.config_sub_panel, min=1)

        self.resume_checkbox = wx.CheckBox(self.config_sub_panel, label='Resume Mode')
        self.resume_checkbox.Hide()

        config_sizer = wx.GridBagSizer(hgap=5, vgap=5)
        setting_sizer = wx.BoxSizer(wx.HORIZONTAL)
        setting_sizer.Add(self.parallel_input, 0)
        setting_sizer.AddStretchSpacer(1)
        setting_sizer.Add(self.resume_checkbox, 0, wx.ALIGN_CENTER_VERTICAL)
        config_sizer.Add(parallel_label, pos=(0, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        config_sizer.Add(setting_sizer, pos=(0, 1), flag=wx.EXPAND)
        config_sizer.Add(wx.StaticLine(self.config_sub_panel), pos=(1, 0), span=(1, 2), flag=wx.EXPAND)
        bams_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bams_sizer.Add(self.bams_input, 1, wx.RIGHT | wx.EXPAND, 5)
        bams_sizer.Add(self.select_bams_button, 0, wx.ALL | wx.EXPAND, 0)
        config_sizer.Add(bams_label, pos=(2, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        config_sizer.Add(bams_sizer, pos=(2, 1), flag=wx.EXPAND)
        reads_sizer = wx.BoxSizer(wx.HORIZONTAL)
        reads_sizer.Add(self.read_len_input, 1, wx.RIGHT | wx.EXPAND, 5)
        reads_sizer.Add(self.se_input, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        reads_sizer.Add(self.pe_input, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        reads_sizer.Add(insert_size_mean_label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        reads_sizer.Add(self.insert_size_mean_input, 1, wx.RIGHT | wx.EXPAND, 5)
        reads_sizer.Add(insert_size_std_label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        reads_sizer.Add(self.insert_size_std_input, 1, wx.EXPAND)
        config_sizer.Add(read_len_label, pos=(3, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        config_sizer.Add(reads_sizer, pos=(3, 1), flag=wx.EXPAND)
        config_sizer.Add(wx.StaticLine(self.config_sub_panel), pos=(4, 0), span=(1, 2), flag=wx.EXPAND)
        task_sizer = wx.BoxSizer(wx.HORIZONTAL)
        task_sizer.Add(self.task_dir_input, 1, wx.EXPAND)
        task_sizer.AddStretchSpacer(1)
        config_sizer.Add(task_dir_label, pos=(5, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        config_sizer.Add(task_sizer, pos=(5, 1), flag=wx.EXPAND)
        config_sizer.AddGrowableCol(1)

        self.config_sub_panel.SetSizerAndFit(config_sizer)
        loading_sizer = self.create_loading_sizer()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.config_sub_panel, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(loading_sizer, 1, wx.ALL | wx.EXPAND, 0)

        self.SetSizerAndFit(sizer)

        self.delegate = None  # type: Optional[_ConfigPanelDelegate]

    def loading_widget(self):
        return self.task_data_view

    def provide_tool(self):
        tool = 'load-task'
        params = {
            'task_dir': self.task_dir_input.GetPath()
        }
        return tool, params

    def handle_data(self, data):
        self.task_data_view.update_df(data)
        for n_col in [2, 3]:
            self.task_data_view.SetColumnWidth(n_col, wx.LIST_AUTOSIZE)

    def set_delegate(self, delegate: _ConfigPanelDelegate):
        self.delegate = delegate

    def on_select_task_dir(self, event):
        """Select task directory callback."""
        assert event
        self.task_data_view.update_df(None)
        self.delegate.tasks_start_loading()
        self.start_task()

    def handle_task_finished(self):
        super().handle_task_finished()
        self.delegate.tasks_loaded()

    def on_select_bams(self, event):
        """Select BAMs callback."""
        assert event
        with wx.FileDialog(self, "Select BAM files", wildcard='*.bam;*.BAM',
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return
            bam_paths = file_dialog.GetPaths()
            self.set_bam_paths(bam_paths)

    def set_bam_paths(self, bam_paths: List[str]):
        """Set BAM paths."""
        self.bam_paths = bam_paths
        bam_names = [os.path.basename(path) for path in self.bam_paths]
        self.bams_input.SetValue('; '.join(bam_names))

    def on_seq_type_changed(self, event):
        """Sequence type changed callback."""
        assert event
        pe = self.pe_input.GetValue()
        self.insert_size_mean_input.Enabled = pe
        self.insert_size_std_input.Enabled = pe


class InferencePanel(LongRunningTaskProgressPanel, _ConfigPanelDelegate):
    """Inference panel.

    Attributes:
        config_panel: Annotation panel.
    """

    def __init__(self, parent, mc: QueueMessageCenter, log_text_field: wx.TextCtrl):
        super().__init__(parent, True, mc, log_text_field)

        # Config.
        self.config_panel = _ConfigPanel(self, mc, log_text_field)
        self.config_panel.delegate = self

        # Output.
        out_label = wx.StaticText(self, label='Output Directory:')
        self.out_dir_picker = wx.DirPickerCtrl(self)

        # Output row.
        output_sizer = wx.BoxSizer(wx.HORIZONTAL)
        output_sizer.Add(out_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        output_sizer.Add(self.out_dir_picker, 1, wx.ALL, 5)
        output_sizer.AddStretchSpacer(1)
        output_sizer.Add(self.start_button, 0, wx.ALL | wx.EXPAND, 5)
        output_sizer.Add(self.stop_button, 0, wx.ALL | wx.EXPAND, 5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.config_panel, 1, wx.ALL | wx.EXPAND, 0)
        sizer.Add(wx.StaticLine(self), 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        sizer.Add(output_sizer, 0, wx.ALL | wx.EXPAND, 0)
        sizer.Add(self.progress_bar, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(self.progress_label, 0, wx.ALL | wx.EXPAND, 5)

        self.SetSizerAndFit(sizer)

        self.add_disabling_elements([self.config_panel.config_sub_panel, self.out_dir_picker])

    def provide_tool(self):
        config_panel = self.config_panel
        resume_mode = config_panel.resume_checkbox.GetValue()
        if resume_mode:
            tool = 'resume'
            params = {
                'out_dir': self.out_dir_picker.GetPath(),
                'process': config_panel.parallel_input.GetValue(),
                'count': None
            }
        else:
            tool = 'inference'
            pe = config_panel.pe_input.GetValue()
            params = {
                'task': config_panel.task_dir_input.GetPath(),
                'bam': config_panel.bam_paths,
                'read_len': config_panel.read_len_input.GetValue(),
                'pe': pe,
                'insert_size_mean': float(config_panel.insert_size_mean_input.GetValue()) if pe else None,
                'insert_size_std': float(config_panel.insert_size_std_input.GetValue()) if pe else None,
                'out_dir': self.out_dir_picker.GetPath(),
                'process': config_panel.parallel_input.GetValue(),
                'count': None
            }

        self.progress_bar.SetRange(config_panel.task_data_view.df.shape[0])

        return tool, params

    def handle_progress(self, progress):
        super().handle_progress(progress)
        assert isinstance(progress, int)
        self.progress_bar.SetValue(progress)

    def handle_data(self, data):
        process_type, task_id = data
        if process_type == 'process_start':
            status = 'Processing'
        else:
            assert process_type == 'process_end'
            status = 'Done'
        self.config_panel.task_data_view.set_task_status(task_id, status)

    def tasks_start_loading(self):
        self.start_button.Enabled = False

    def tasks_loaded(self):
        self.start_button.Enabled = True
