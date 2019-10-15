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
from typing import Tuple, Optional
from enum import Enum

from byase.message import MessageCenter, INFO


class MessageCenterError(Exception):
    """Message center base exception."""
    pass


class TerminatedError(MessageCenterError):
    """When instructed to be terminated."""
    pass


class InputItem:
    """Item to be passed to input queue."""
    def __init__(self, tool: str, params: dict):
        self.tool = tool
        self.params = params


class OutputItem:
    """Item to be passed to output queue."""
    def __init__(self, log=None, data=None, progress_msg=None, progress=None, task_started=False, task_finished=False):
        self.log = log
        self.data = data
        self.progress_msg = progress_msg
        self.progress = progress
        self.task_started = task_started
        self.task_finished = task_finished


class Instruction(Enum):
    """Instruction enum."""
    TERMINATE = 1


class QueueMessageCenter(MessageCenter):
    """Message center with queues.

    Attributes:
        _instruction_queue: The queue to receive instructions.
        _input_queue: The queue to transport input.
        _output_queue: The queue to transport output messages and data.
    """

    def __init__(self, level=INFO, log_path=None):
        super().__init__(level, log_path)
        self._instruction_queue = mp.Queue()
        self._input_queue = mp.Queue()
        self._output_queue = mp.Queue()

    def _handle_log(self, log):
        super()._handle_log(log)
        self._output_queue.put(OutputItem(log=log))

    def handle_progress(self, msg, progress=None):
        super().handle_progress(msg, progress)
        self._output_queue.put(OutputItem(progress_msg=msg, progress=progress))

    def handle_data(self, data):
        super().handle_data(data)
        self._output_queue.put(OutputItem(data=data))

    def signal_task_started(self):
        """Signal task has been started."""
        self._output_queue.put(OutputItem(task_started=True))

    def signal_task_finished(self):
        """Signal task has been finished."""
        self._output_queue.put(OutputItem(task_finished=True))

    def send_input(self, tool: str, params: dict):
        """Send input tool and params."""
        self._input_queue.put(InputItem(tool=tool, params=params))

    def receive_input(self) -> Tuple[str, dict]:
        """Receive input tool and params."""
        item = self._input_queue.get()  # type: InputItem
        return item.tool, item.params

    def receive_output(self) -> Optional[OutputItem]:
        """Receive output."""
        if self._output_queue.empty():
            return None
        item = self._output_queue.get()
        return item

    def send_instruction(self, instruction: Instruction):
        self._instruction_queue.put(instruction)

    def receive_instruction(self) -> Optional[Instruction]:
        if self._instruction_queue.empty():
            return None
        instruction = self._instruction_queue.get()
        return instruction
