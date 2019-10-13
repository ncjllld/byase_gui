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

from typing import Dict, Callable, Optional

import pandas as pd
import wx


class DataView(wx.ListCtrl):
    """Data view to display data frame.

    Attributes:
        src_df: The source data frame.
        df: The data frame which is displayed by the data view.
        sorter_mapper: Sort mapper, column name to (key extract function, ascending).
        filter_mapper: Filter mapper, column name to filter function.
        sort_col_name: The name of column to sort.
        sort_ascending: If the column is sorted in ascending order.
        last_sorted_col_name: The name of the last sorted column.
    """

    def __init__(self, parent, sortable: bool = True):
        super().__init__(parent, style=wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL)

        self.src_df = None  # type: Optional[pd.DataFrame]
        self.df = None  # type: Optional[pd.DataFrame]

        self.sorter_mapper = {}  # type: Dict[str, Optional[Callable]]
        self.filter_mapper = {}  # type: Dict[str, Callable]

        self.sort_col_name = None  # type: Optional[str]
        self.sort_ascending = True
        self.last_sorted_col_name = None  # type: Optional[str]

        if sortable:
            self.Bind(wx.EVT_LIST_COL_CLICK, self.on_col_click)

    def OnGetItemText(self, item, column):
        cell = self.df.iloc[item, column]
        if isinstance(cell, float):
            cell = '{:.3f}'.format(cell)
        else:
            cell = str(cell)
        return cell

    def on_col_click(self, event):
        """When column header is clicked."""
        n_col = event.GetColumn()
        self.last_sorted_col_name = self.sort_col_name
        self.sort_col_name = self.src_df.columns[n_col]

        ascending = True
        if (self.last_sorted_col_name is not None) and (self.last_sorted_col_name == self.sort_col_name):
            ascending = not self.sort_ascending
        self.sort_ascending = ascending

        self._update_display()

    def _update_display(self):
        """Update display."""
        if self.src_df is None:
            return

        df = self.src_df

        # Apply filters.
        for col_name, filter_func in self.filter_mapper.items():
            col_data = df[col_name].tolist()
            sel = [filter_func(data) for data in col_data]
            df = df[sel]

        # Apply sorter.
        if self.sort_col_name is not None:
            key_func = None
            if self.sort_col_name in self.sorter_mapper:
                key_func = self.sorter_mapper[self.sort_col_name]

            if key_func is not None:
                col_data = df[self.sort_col_name].tolist()
                order = sorted(range(len(col_data)), key=lambda x: key_func(col_data[x]),
                               reverse=not self.sort_ascending)
                df = df.iloc[order, :]
            else:
                df = df.sort_values(self.sort_col_name, ascending=self.sort_ascending)

        # Update displayed data frame.
        self.df = df
        self.SetItemCount(self.df.shape[0])

    def update_df(self, df: Optional[pd.DataFrame]):
        """Update data frame."""
        self.ClearAll()
        self.sort_col_name = None

        if df is None:
            self.src_df = None
            self.df = None
            return

        self.src_df = df
        for i, col in enumerate(self.src_df.columns.tolist()):
            self.InsertColumn(i, col)

        self._update_display()

    def set_sorter(self, col_name: str, key_func: Optional[Callable]):
        """Set sorter for specific column name."""
        self.sorter_mapper[col_name] = key_func

    def set_filter(self, col_name: str, filter_func: Optional[Callable]):
        """Set or remove a filter.

        Args:
            col_name: The name of column to filter.
            filter_func: The filter function, if it is None, the corresponding filter will be removed.
        """
        if filter_func is not None:
            self.filter_mapper[col_name] = filter_func
        else:
            if col_name in self.filter_mapper:
                del self.filter_mapper[col_name]

        self._update_display()
