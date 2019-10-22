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

from typing import Optional

import pandas as pd
import wx

from .message import QueueMessageCenter
from .long_running import LongRunningTaskIndicatorPanel
from .data_view import DataView


class ResultPanelDelegate:
    """Result panel delegate."""

    def plot_task(self, result_dir: str, task_id: str, task_detail: pd.DataFrame):
        """Notify to plot task."""
        pass


def _id_key_func(x: str):
    """ID key function."""
    try:
        s = int(x.split('_')[0])
    except ValueError:
        return x
    else:
        return s


def _location_key_func(loc: str):
    """Location key function."""
    chr_str, loc = loc.split(':')
    chrom = _get_chr_key(chr_str)
    start = int(loc.split('-')[0])
    return chrom, start


def _chr_key_func(loc: str):
    """Chrom key function."""
    chr_str = loc.split(':')[0]
    chrom = _get_chr_key(chr_str)
    return chrom


def _get_chr_key(chr_str: str):
    """Get chrom as key."""
    chr_str = chr_str.strip('chr')
    try:
        chrom = int(chr_str)
        chrom = '{:03d}'.format(chrom)
    except ValueError:
        chrom = chr_str
    return chrom


def _get_detail_result(df_gene_level: pd.DataFrame, df_isoform_level: pd.DataFrame, n: int):
    """Get detail result of the n-th task."""
    row = df_gene_level.iloc[n, :]
    task_id = row['Task ID']

    def _find_diff_section_start(_df):
        for _i, _col in enumerate(_df.columns):
            if 'Mean' in _col:
                return _i

    # Get gene-level result.
    diff_section_start = _find_diff_section_start(df_gene_level)
    cols = ['Number', 'ID', 'Name', 'SNPs']
    d = ['Gene', row['Gene ID'], row['Gene Name'], row['SNPs']]
    for i in range(diff_section_start, len(df_gene_level.columns)):
        cols.append(df_gene_level.columns[i])
        d.append(row[i])
    df = pd.DataFrame([d], columns=cols)

    # Merge isoform-level results.
    diff_section_start = _find_diff_section_start(df_isoform_level)
    d = df_isoform_level[df_isoform_level['Task ID'] == task_id]
    col_idx = [list(d.columns).index(col) for col in ['Isoform Number', 'Isoform ID', 'Isoform Name', 'SNP Count']]
    col_idx += list(range(diff_section_start, df_isoform_level.shape[1]))
    d = d.iloc[:, col_idx]
    df = pd.DataFrame([df.iloc[0, :].tolist()] + [d.iloc[i, :].tolist() for i in range(d.shape[0])], columns=df.columns)
    df.index = ['g'] + ['i{}'.format(i) for i in range(df.shape[0] - 1)]
    return df


class ResultPanel(LongRunningTaskIndicatorPanel):
    """Result panel.

    Attributes:
        res_dir_picker: Result directory picker.
        res_load_button: Results loading button.

        results_data_view: Results data view.
        search_gene_input: Search gene input.

        df_isoform_level: Isoform-level results data frame.
        detail_data_view: Detail data view.

        filter_mean_check: Filter by mean checkbox.
        filter_mean_input: Filter by mean input.
        filter_hpd_check: Filter by HPD checkbox.
        filter_hpd_input: Filter by HPD input.

        detail_label: Detail label.
        plot_button: Plot button.

        delegate: The delegate object.
    """

    def __init__(self, parent, mc: QueueMessageCenter, log_text_field: wx.TextCtrl):
        super().__init__(parent, mc, log_text_field)

        # Load row
        res_dir_label = wx.StaticText(self, label='Result Directory:')
        self.res_dir_picker = wx.DirPickerCtrl(self)
        self.res_dir_picker.Bind(wx.EVT_DIRPICKER_CHANGED, self.on_res_dir_changed)

        self.res_load_button = wx.Button(self, label='Load')
        self.res_load_button.Bind(wx.EVT_BUTTON, self.on_load_button)

        # Results data view.
        self.results_data_view = DataView(self)
        self.results_data_view.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_results_item_selected)
        self.results_data_view.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_results_item_deselected)

        self.results_data_view.set_sorter('Task ID', _id_key_func)
        self.results_data_view.set_sorter('Location', _location_key_func)

        # Detail data view.
        self.df_isoform_level = None
        self.detail_data_view = DataView(self, sortable=False)

        # Data view control row.
        search_gene_id_label = wx.StaticText(self, label='Search Gene:')
        self.search_gene_input = wx.TextCtrl(self)
        self.search_gene_input.Bind(wx.EVT_TEXT, self.on_search_gene_text_changed)
        filter_label = wx.StaticText(self, label='Filter by Difference:')
        self.filter_mean_check = wx.CheckBox(self, label='Mean >')
        self.filter_mean_check.Bind(wx.EVT_CHECKBOX, self.on_filter_mean_checked)
        self.filter_mean_input = wx.SpinCtrlDouble(self, initial=0, min=0, max=1, inc=0.05)
        self.filter_mean_input.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_filter_mean_input_changed)
        self.filter_mean_input.Enabled = False
        self.filter_hpd_check = wx.CheckBox(self, label='95% HPD width <')
        self.filter_hpd_check.Bind(wx.EVT_CHECKBOX, self.on_filter_hpd_checked)
        self.filter_hpd_input = wx.SpinCtrlDouble(self, initial=1, min=0, max=1, inc=0.05)
        self.filter_hpd_input.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_filter_hpd_input_changed)
        self.filter_hpd_input.Enabled = False

        # Detail row.
        self.detail_label = wx.StaticText(self)
        self.set_detail_label(None)
        self.plot_button = wx.Button(self, label='Plot')
        self.plot_button.Enabled = False
        self.plot_button.Bind(wx.EVT_BUTTON, self.on_plot_button)

        self.delegate = None  # type: Optional[ResultPanelDelegate]

        # Load sizer.
        load_sizer = wx.BoxSizer(wx.HORIZONTAL)
        load_sizer.Add(res_dir_label, 0, wx.TOP | wx.BOTTOM | wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        load_sizer.Add(self.res_dir_picker, 1, wx.ALL, 5)
        load_sizer.Add(self.res_load_button, 0, wx.ALL | wx.EXPAND, 5)
        load_sizer.AddStretchSpacer(1)
        load_sizer.Add(search_gene_id_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        load_sizer.Add(self.search_gene_input, 1, wx.ALL | wx.EXPAND, 5)

        # Loading sizer.
        loading_sizer = self.create_loading_sizer()

        # Data view control sizer.
        ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ctrl_sizer.Add(filter_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        ctrl_sizer.AddStretchSpacer(1)
        ctrl_sizer.Add(self.filter_mean_check, 0, wx.TOP | wx.BOTTOM | wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        ctrl_sizer.Add(self.filter_mean_input, 0, wx.TOP | wx.BOTTOM | wx.RIGHT | wx.EXPAND, 5)
        ctrl_sizer.Add(self.filter_hpd_check, 0, wx.TOP | wx.BOTTOM | wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        ctrl_sizer.Add(self.filter_hpd_input, 0, wx.TOP | wx.BOTTOM | wx.RIGHT | wx.EXPAND, 5)

        # Detail sizer.
        detail_sizer = wx.BoxSizer(wx.HORIZONTAL)
        detail_sizer.Add(self.detail_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        detail_sizer.AddStretchSpacer(1)
        detail_sizer.Add(self.plot_button, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(load_sizer, 0, wx.ALL | wx.EXPAND, 0)
        sizer.Add(loading_sizer, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(ctrl_sizer, 0, wx.ALL | wx.EXPAND, 0)
        sizer.Add(wx.StaticLine(self), 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        sizer.Add(self.detail_data_view, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(detail_sizer, 0, wx.ALL | wx.EXPAND, 0)

        self.SetSizerAndFit(sizer)

        self.add_disabling_elements([self.search_gene_input])

    def loading_widget(self):
        return self.results_data_view

    def set_delegate(self, delegate: ResultPanelDelegate):
        """Set delegate."""
        self.delegate = delegate

    def set_detail_label(self, task_id: Optional[str]):
        """Set detail label."""
        label = 'Details of Task'
        if task_id is not None:
            label += ': {}'.format(task_id)
        self.detail_label.SetLabel(label)

    def provide_tool(self):
        tool = 'stats'
        params = {
            'result_dir': self.res_dir_picker.GetPath()
        }
        return tool, params

    def handle_data(self, data):
        df_gene_level, df_isoform_level = data
        self.df_isoform_level = df_isoform_level

        df = df_gene_level.rename(columns={'Isoform Count': 'Isoforms', 'SNP Count': 'SNPs'})

        self.results_data_view.update_df(df)
        for n_col in [2, 3]:
            self.results_data_view.SetColumnWidth(n_col, wx.LIST_AUTOSIZE)
        for n_col in range(6, df.shape[1]):
            self.results_data_view.SetColumnWidth(n_col, wx.LIST_AUTOSIZE_USEHEADER)

    def _reset_details(self):
        """Reset details."""
        self.detail_data_view.update_df(None)
        self.set_detail_label(None)
        self.plot_button.Enabled = False

    def on_res_dir_changed(self, event):
        """Result directory changed callback."""
        assert event
        self.results_data_view.update_df(None)
        self.search_gene_input.SetValue('')
        self._reset_details()

    def on_load_button(self, event):
        """Load button callback."""
        assert event
        self.results_data_view.update_df(None)
        self.res_load_button.Enabled = False
        self._reset_details()
        self.start_task()

    def handle_task_finished(self):
        super().handle_task_finished()
        self.res_load_button.Enabled = True

    def on_results_item_selected(self, event: wx.ListEvent):
        """Results item selected callback."""
        n_row = event.GetIndex()
        df = _get_detail_result(self.results_data_view.df, self.df_isoform_level, n_row)
        self.detail_data_view.update_df(df)
        for n_col in [1, 2]:
            self.detail_data_view.SetColumnWidth(n_col, wx.LIST_AUTOSIZE)
        for n_col in range(4, df.shape[1]):
            self.detail_data_view.SetColumnWidth(n_col, wx.LIST_AUTOSIZE_USEHEADER)

        task_id = self.results_data_view.df.iloc[n_row, :]['Task ID']
        self.set_detail_label(task_id)
        self.plot_button.Enabled = True

    def on_results_item_deselected(self, event: wx.ListEvent):
        """"Results item deselected callback."""
        assert event
        self.detail_data_view.update_df(None)
        self.set_detail_label(None)
        self.plot_button.Enabled = False

    def on_search_gene_text_changed(self, event):
        """Search gene text changed callback."""
        assert event
        if self.results_data_view.df is None:
            return
        text = self.search_gene_input.GetValue()
        gene_names = self.results_data_view.df['Gene Name']
        for i, gene_name in enumerate(gene_names):
            if isinstance(gene_name, str) and (text in gene_name):
                self.results_data_view.Select(i)
                self.results_data_view.EnsureVisible(i)
                break

    def on_filter_mean_checked(self, event):
        """Filter mean checked callback."""
        assert event
        checked = self.filter_mean_check.IsChecked()
        self.filter_mean_input.Enabled = checked
        self.filter_mean(checked)

    def on_filter_hpd_checked(self, event):
        """Filter HPD checked callback."""
        assert event
        checked = self.filter_hpd_check.IsChecked()
        self.filter_hpd_input.Enabled = checked
        self.filter_hpd(checked)

    def on_filter_mean_input_changed(self, event):
        """Filter mean input changed callback."""
        assert event
        self.filter_mean()

    def on_filter_hpd_input_changed(self, event):
        """Filter HPD input changed callback."""
        assert event
        self.filter_hpd()

    def filter_mean(self, toggle_on: bool = True):
        """Filter by mean or toggle off filtering."""
        self.results_data_view.Select(self.results_data_view.GetFirstSelected(), on=0)
        val = self.filter_mean_input.GetValue()
        for col in self.results_data_view.df.columns:
            if 'Mean' in col:
                self.results_data_view.set_filter(col, (lambda x: x > val) if toggle_on else None)

    def filter_hpd(self, toggle_on: bool = True):
        """Filter by HPD or toggle off filtering."""
        self.results_data_view.Select(self.results_data_view.GetFirstSelected(), on=0)
        val = self.filter_hpd_input.GetValue()
        for col in self.results_data_view.df.columns:
            if 'HPD' in col:
                self.results_data_view.set_filter(col, (lambda x: x < val) if toggle_on else None)

    def on_plot_button(self, event):
        """Plot button callback."""
        assert event
        task_id = self.detail_label.GetLabel().split(' ')[-1]
        self.GetParent().SetSelection(3)
        self.delegate.plot_task(self.res_dir_picker.GetPath(), task_id, self.detail_data_view.df)
