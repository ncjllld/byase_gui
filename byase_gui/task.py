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

import traceback
from multiprocessing import Process
import time
import psutil

import pandas as pd

from .message import QueueMessageCenter, Instruction
from byase.annotation import generate_annotation
from byase.annotation import AnnotationDB
from byase.inference import inference, inference_resume
from byase.stats import stats
from byase.plot import plot_task


def _load_task(args):
    task_dir = args['task_dir']
    mc = args['mc']  # type: QueueMessageCenter

    cols = ['Number', 'Task ID', 'Gene Name', 'Genomic Location', 'Isoforms', 'Phased', 'SNPs', 'Status']
    d_number = []
    d_task_id = []
    d_gene_name = []
    d_location = []
    d_isoforms = []
    d_phased = []
    d_snps = []
    d_status = []
    d = [d_number, d_task_id, d_gene_name, d_location, d_isoforms, d_phased, d_snps, d_status]

    with AnnotationDB(task_dir) as anno_db:
        n = 0
        for fields in anno_db.tasks_db_fields_iterator():
            n += 1
            d_number.append(n)
            info = anno_db.get_segment_basic_info(fields['segment'])
            d_task_id.append(fields['id'])
            d_gene_name.append(info['gene_name'])
            d_location.append(info['location'])
            d_isoforms.append(info['isoforms_count'])
            phased = fields['phased']
            assert phased == 1 or phased == 0
            d_phased.append('Phased' if phased == 1 else 'Non-Phased')
            d_snps.append(fields['snps_count'])
            d_status.append('Waiting')
    df = pd.DataFrame({col: d[n] for n, col in enumerate(cols)})[cols]
    mc.handle_data(df)


def _load_stats(stats_path: dict, mc: QueueMessageCenter):
    ase_gene_level_stats_path = stats_path['gene-level path']
    ase_isoform_level_stats_path = stats_path['isoform-level path']
    df_gene_level = pd.read_csv(ase_gene_level_stats_path)
    df_isoform_level = pd.read_csv(ase_isoform_level_stats_path)

    def _rename_diff_cols(df: pd.DataFrame):
        rename_dict = {}
        for col in df.columns:
            if 'Difference' in col:
                new_col = col.replace('Difference ', '')
                if 'HPD' in col:
                    new_col = col.split(') ')[-1]
                rename_dict[col] = new_col
        return df.rename(columns=rename_dict)

    df_gene_level = _rename_diff_cols(df_gene_level)
    df_isoform_level = _rename_diff_cols(df_isoform_level)

    mc.handle_data((df_gene_level, df_isoform_level))


def work(tool: str, params: dict):
    mc = params['mc']  # type: QueueMessageCenter
    try:
        if tool == 'gen-task':
            generate_annotation(params)
        elif tool == 'load-task':
            _load_task(params)
        elif tool == 'inference':
            inference(params)
        elif tool == 'resume':
            inference_resume(params)
        elif tool == 'stats':
            stats_path = stats(params)
            _load_stats(stats_path, mc)
        elif tool == 'plot':
            html_path = plot_task(params)
            mc.handle_data(('html path', html_path))
    except Exception as e:
        mc.handle_progress('Error occurred!')
        mc.log_error(e)
        traceback.print_exc()
    else:
        mc.handle_progress('Process completed!')


def task(mc: QueueMessageCenter):
    """Backend task."""
    while True:
        tool, params = mc.receive_input()
        params['mc'] = mc

        # Inform work has been started.
        mc.signal_task_started()

        work_process = Process(target=work, args=(tool, params))
        work_process.start()

        while work_process.is_alive():
            time.sleep(1)
            instruction = mc.receive_instruction()
            if instruction is Instruction.TERMINATE:
                for child in psutil.Process(work_process.pid).children(recursive=True):
                    child.kill()
                work_process.terminate()
                mc.handle_progress('Process terminated!')
                break

        work_process.join()

        # Inform work has been finished.
        mc.signal_task_finished()
