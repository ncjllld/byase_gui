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
import os
import gzip

import pandas as pd
import wx
from wx.lib.intctrl import IntCtrl

from .message import QueueMessageCenter
from .long_running import LongRunningTaskProgressPanel


class AnnotationPanel(LongRunningTaskProgressPanel):
    """Annotation Panel.

    Attributes:
        gff_file_picker: GFF file picker.
        gff_gene_id_feature_input: GFF gene ID feature input.
        gff_isoform_feature_input: GFF isoform feature input.
        gff_gene_name_attr_input: GFF gene name attribute input.
        gff_isoform_name_attr_input: GFF isoform name attribute input.
        gff_data_view: GFF data grid for preview.
        vcf_file_picker: VCF file picker.
        vcf_sample_input: VCF sample input.
        vcf_add_chr_check: VCF add chr prefix checkbox.
        vcf_data_view: VCF data grid for preview.
        out_dir_picker: Output directory picker.
    """

    def __init__(self, parent, mc: QueueMessageCenter, log_text_field: wx.TextCtrl):
        super().__init__(parent, False, mc, log_text_field)

        # GFF config.
        gff_file_label = wx.StaticText(self, label='GFF File:')
        self.gff_file_picker = wx.FilePickerCtrl(self)
        self.gff_file_picker.Bind(wx.EVT_FILEPICKER_CHANGED, self.gff_file_changed)

        feature_type_label = wx.StaticText(self, label='Feature Type Name:')
        feature_type_tip = wx.ToolTip('The 3rd column of the GFF file.')
        feature_type_label.SetToolTip(feature_type_tip)

        gff_gene_id_feature_label = wx.StaticText(self, label='Gene:')
        self.gff_gene_id_feature_input = wx.TextCtrl(self, value='gene')

        gff_isoform_feature_label = wx.StaticText(self, label='Isoform:')
        self.gff_isoform_feature_input = wx.TextCtrl(self, value='transcript')

        attr_name_label = wx.StaticText(self, label='Attribute Name:')
        attr_name_tip = wx.ToolTip('Extract from the 9th column of the GFF file.')
        attr_name_label.SetToolTip(attr_name_tip)

        gff_gene_name_attr_label = wx.StaticText(self, label='Gene Name:')
        self.gff_gene_name_attr_input = wx.TextCtrl(self, value='ID')

        gff_isoform_name_attr_label = wx.StaticText(self, label='Isoform Name:')
        self.gff_isoform_name_attr_input = wx.TextCtrl(self, value='ID')

        # GFF3 preview.
        gff_data_panel = wx.Panel(self)
        self.gff_data_view = wx.ListCtrl(gff_data_panel, style=wx.LC_REPORT)
        gff_data_sizer = wx.BoxSizer()
        gff_data_sizer.Add(self.gff_data_view, 1, wx.EXPAND)
        gff_data_panel.SetSizerAndFit(gff_data_sizer)

        # VCF config.
        vcf_file_label = wx.StaticText(self, label='VCF File:')
        self.vcf_file_picker = wx.FilePickerCtrl(self)
        self.vcf_file_picker.Bind(wx.EVT_FILEPICKER_CHANGED, self.vcf_file_changed)

        vcf_ploidy_label = wx.StaticText(self, label='Ploidy:')
        self.vcf_ploidy_input = IntCtrl(self, value=2, min=2)

        vcf_sample_label = wx.StaticText(self, label='Sample Name:')
        self.vcf_sample_input = wx.TextCtrl(self)

        self.vcf_add_chr_check = wx.CheckBox(self, label='Add "chr" prefix to chromosome names')

        # VCF preview.
        vcf_data_panel = wx.Panel(self)
        self.vcf_data_view = wx.ListCtrl(vcf_data_panel, style=wx.LC_REPORT)
        self.vcf_data_view.Bind(wx.EVT_LIST_COL_CLICK, self.vcf_data_view_col_clicked)
        vcf_data_sizer = wx.BoxSizer()
        vcf_data_sizer.Add(self.vcf_data_view, 1, wx.EXPAND)
        vcf_data_panel.SetSizerAndFit(vcf_data_sizer)

        # Output.
        out_label = wx.StaticText(self, label='Output Directory:')
        self.out_dir_picker = wx.DirPickerCtrl(self)

        gff_sizer = wx.BoxSizer(wx.HORIZONTAL)
        gff_config_sizer = wx.GridBagSizer(hgap=5, vgap=5)
        gff_config_sizer.Add(gff_file_label, pos=(0, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        gff_config_sizer.Add(self.gff_file_picker, pos=(0, 1), flag=wx.EXPAND)
        gff_config_sizer.Add(wx.StaticLine(self), pos=(1, 0), span=(1, 2), flag=wx.EXPAND)
        gff_config_sizer.Add(feature_type_label, pos=(2, 0), span=(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        gff_config_sizer.Add(gff_gene_id_feature_label, pos=(3, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        gff_config_sizer.Add(self.gff_gene_id_feature_input, pos=(3, 1), flag=wx.EXPAND)
        gff_config_sizer.Add(gff_isoform_feature_label, pos=(4, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        gff_config_sizer.Add(self.gff_isoform_feature_input, pos=(4, 1), flag=wx.EXPAND)
        gff_config_sizer.Add(wx.StaticLine(self), pos=(5, 0), span=(1, 2), flag=wx.EXPAND)
        gff_config_sizer.Add(attr_name_label, pos=(6, 0), span=(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        gff_config_sizer.Add(gff_gene_name_attr_label, pos=(7, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        gff_config_sizer.Add(self.gff_gene_name_attr_input, pos=(7, 1), flag=wx.EXPAND)
        gff_config_sizer.Add(gff_isoform_name_attr_label, pos=(8, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        gff_config_sizer.Add(self.gff_isoform_name_attr_input, pos=(8, 1), flag=wx.EXPAND)
        gff_config_sizer.AddGrowableCol(1)
        gff_preview_sizer = wx.BoxSizer(wx.VERTICAL)
        gff_preview_sizer.Add(wx.StaticText(self, label='Preview:'), 0, wx.LEFT | wx.TOP, 5)
        gff_preview_sizer.Add(gff_data_panel, 1, wx.ALL | wx.EXPAND, 5)
        gff_sizer.Add(gff_config_sizer, 1, wx.ALL | wx.EXPAND, 5)
        gff_sizer.Add(gff_preview_sizer, 2, wx.ALL | wx.EXPAND, 0)

        vcf_sizer = wx.BoxSizer(wx.HORIZONTAL)
        vcf_config_sizer = wx.GridBagSizer(hgap=5, vgap=5)
        vcf_config_sizer.Add(vcf_file_label, pos=(0, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        vcf_config_sizer.Add(self.vcf_file_picker, pos=(0, 1), flag=wx.EXPAND)
        vcf_config_sizer.Add(wx.StaticLine(self), pos=(1, 0), span=(1, 2), flag=wx.EXPAND)
        vcf_config_sizer.Add(vcf_sample_label, pos=(2, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        vcf_config_sizer.Add(self.vcf_sample_input, pos=(2, 1), flag=wx.EXPAND)
        vcf_config_sizer.Add(vcf_ploidy_label, pos=(3, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        vcf_config_sizer.Add(self.vcf_ploidy_input, pos=(3, 1), flag=wx.EXPAND)
        vcf_config_sizer.Add(self.vcf_add_chr_check, pos=(4, 0), span=(1, 2))
        vcf_config_sizer.AddGrowableCol(1)
        vcf_preview_sizer = wx.BoxSizer(wx.VERTICAL)
        vcf_preview_sizer.Add(wx.StaticText(self, label='Preview:'), 0, wx.LEFT | wx.TOP, 5)
        vcf_preview_sizer.Add(vcf_data_panel, 1, wx.ALL | wx.EXPAND, 5)
        vcf_sizer.Add(vcf_config_sizer, 1, wx.ALL | wx.EXPAND, 5)
        vcf_sizer.Add(vcf_preview_sizer, 2, wx.ALL | wx.EXPAND, 0)

        output_sizer = wx.BoxSizer(wx.HORIZONTAL)
        output_sizer.Add(out_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        output_sizer.Add(self.out_dir_picker, 1, wx.ALL | wx.EXPAND, 5)
        output_sizer.AddStretchSpacer(1)
        output_sizer.Add(self.start_button, 0, wx.ALL | wx.EXPAND, 5)
        output_sizer.Add(self.stop_button, 0, wx.ALL | wx.EXPAND, 5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(gff_sizer, 1, wx.ALL | wx.EXPAND, 0)
        sizer.Add(wx.StaticLine(self), 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        sizer.Add(vcf_sizer, 1, wx.ALL | wx.EXPAND, 0)
        sizer.Add(wx.StaticLine(self), 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        sizer.Add(output_sizer, 0, wx.ALL | wx.EXPAND, 0)
        sizer.Add(self.progress_bar, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(self.progress_label, 0, wx.ALL | wx.EXPAND, 5)
        self.SetSizerAndFit(sizer)

        self.add_disabling_elements([self.gff_data_view, self.gff_file_picker,
                                     self.gff_gene_id_feature_input, self.gff_isoform_feature_input,
                                     self.gff_gene_name_attr_input, self.gff_isoform_name_attr_input,
                                     self.vcf_data_view, self.vcf_file_picker, self.vcf_ploidy_input,
                                     self.vcf_sample_input, self.vcf_add_chr_check,
                                     self.out_dir_picker])

    def gff_file_changed(self, event):
        """GFF file picker callback."""
        assert event
        gff_path = self.gff_file_picker.GetPath()
        cols = ['Seq ID', 'Source', 'Type', 'Start', 'End', 'Score', 'Strand', 'Phase', 'Attributes']
        data = [[] for _ in cols]
        f = None
        try:
            if os.path.splitext(gff_path)[-1].lower() == '.gz':
                f = gzip.open(gff_path, 'rt')
            else:
                f = open(gff_path)
            line_num = -1
            for line in f:
                if line.startswith('#'):
                    continue
                line_num += 1
                if line_num == 20:
                    break
                line = line.strip('\n')
                cells = line.split('\t')
                for i in range(len(cols)):
                    data[i].append(cells[i])
            d = {col: data[i] for i, col in enumerate(cols)}
            df = pd.DataFrame(d)[cols]
            self._set_data_view_with_df(self.gff_data_view, df)
            self.gff_data_view.SetColumnWidth(len(cols) - 1, wx.LIST_AUTOSIZE)

        except Exception as e:
            self.mc.log_error(e)
            df = pd.DataFrame({'Error': ['Fail to open or parse GFF file:\n{}'.format(gff_path)]})
            self._set_data_view_with_df(self.gff_data_view, df)
            self.gff_data_view.SetColumnWidth(0, wx.LIST_AUTOSIZE)

        finally:
            if f is not None:
                f.close()

    def vcf_file_changed(self, event):
        """VCF file picker callback."""
        assert event
        vcf_path = self.vcf_file_picker.GetPath()
        cols = None
        data = None
        f = None
        try:
            if os.path.splitext(vcf_path)[-1].lower() == '.gz':
                f = gzip.open(vcf_path, 'rt')
            else:
                f = open(vcf_path)
            line_num = -1
            for line in f:
                if line.startswith('##'):
                    continue
                line = line.strip('\n')
                if line.startswith('#'):
                    cols = line[1:].split('\t')
                    data = [[] for _ in cols]
                    continue
                line_num += 1
                if line_num == 20:
                    break
                cells = line.split('\t')
                for i in range(len(cols)):
                    data[i].append(cells[i])
            d = {col: data[i] for i, col in enumerate(cols)}
            df = pd.DataFrame(d)[cols]
            self._set_data_view_with_df(self.vcf_data_view, df)

        except Exception as e:
            self.mc.log_error(e)
            df = pd.DataFrame({'Error': ['Fail to open or parse VCF file:\n{}'.format(vcf_path)]})
            self._set_data_view_with_df(self.vcf_data_view, df)
            self.vcf_data_view.SetColumnWidth(0, wx.LIST_AUTOSIZE)

        finally:
            if f is not None:
                f.close()

    @staticmethod
    def _set_data_view_with_df(grid: wx.ListCtrl, df: Optional[pd.DataFrame]):
        """Set data view with data frame."""
        grid.ClearAll()
        if df is None:
            return

        cols = df.columns.tolist()
        n_col = len(cols)
        for i, col in enumerate(cols):
            grid.InsertColumn(i, col)
        for i, row in df.iterrows():
            grid.InsertItem(i, row[cols[0]])
            for n in range(1, n_col):
                grid.SetItem(i, n, row[cols[n]])

    def vcf_data_view_col_clicked(self, event: wx.ListEvent):
        """VCF data view column clicked callback."""
        col = event.GetColumn()
        if col < 8:
            return
        sample_name = self.vcf_data_view.GetColumn(col).GetText()
        self.vcf_sample_input.SetValue(sample_name)

    def provide_tool(self):
        tool = 'gen-task'
        params = {
            'gff': self.gff_file_picker.GetPath(),
            'gene_feature': self.gff_gene_id_feature_input.GetValue(),
            'isoform_feature': self.gff_isoform_feature_input.GetValue(),
            'gene_name_attr': self.gff_gene_name_attr_input.GetValue(),
            'isoform_name_attr': self.gff_isoform_name_attr_input.GetValue(),
            'vcf': self.vcf_file_picker.GetPath(),
            'ploidy': self.vcf_ploidy_input.GetValue(),
            'sample': self.vcf_sample_input.GetValue(),
            'add_chrom_prefix': self.vcf_add_chr_check.IsChecked(),
            'out_dir': self.out_dir_picker.GetPath()
        }
        return tool, params
