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

import wx


class LogPane(wx.CollapsiblePane):
    """Log pane which is collapsible.

    Attributes:
        log_text_field: The text field for logging.
    """

    def __init__(self, parent):
        super().__init__(parent, label='Logs')
        pane = self.GetPane()
        self.log_text_field = wx.TextCtrl(pane, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL, size=(-1, 200))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.log_text_field, 0, wx.ALL | wx.EXPAND, 0)
        pane.SetSizerAndFit(sizer)
        self.Expand()
