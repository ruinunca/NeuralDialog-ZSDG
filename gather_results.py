from __future__ import print_function

import os
import argparse
import json
from collections import defaultdict
import sys
import re

import numpy as np


def parse_report_file(in_lines, in_eval_domain):
    result = defaultdict(lambda: 0)
    for line in in_lines:
        bleu_match = re.match('Domain: {} BLEU (.+)'.format(in_eval_domain), line)
        if bleu_match:
            result['BLEU'] = float(bleu_match.group(1))
        ent_match = re.match(' Entity precision (.+) recall (.+) and f1 (.+)', line)
        if ent_match:
            result['Ent_p'], result['Ent_R'], result['Ent_F1'] = list(map(float, [ent_match.group(1), ent_match.group(2), ent_match.group(3)]))
    return result


def gather_metrics(in_src_folder, in_eval_domain):
    result_gathered = defaultdict(lambda: [])

    for session_folder in os.listdir(in_src_folder):
        report_files = [name
                        for name in os.listdir(os.path.join(in_src_folder, session_folder))
                        if os.path.splitext(name)[1] == '.txt']
        assert len(report_files) == 1
        with open(os.path.join(in_src_folder, session_folder, report_files[0])) as report_in:
            report_content = report_in.readlines()
        report = parse_report_file(report_content, in_eval_domain)
        for key, value in report.items():
            result_gathered[key].append(value)
    return result_gathered


def write_report(in_report, in_domain, in_output_stream):
    value_lens = [len(value) for value in in_report.values()]
    assert len(set(value_lens)) == 1
    print('Domain: {}, {} measurements'.format(in_domain, value_lens[0]))
    for key, value in in_report.items():
        print('{}:\t min {:.3f}\tmax {:.3f}\tmean {:.3f} stddev {:.3f}'.format(key,
                                                                               np.min(value),
                                                                               np.max(value),
                                                                               np.mean(value),
                                                                               np.std(value)),
              file=in_output_stream)

def get_option_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_folder')
    parser.add_argument('eval_domain')

    return parser


if __name__ == '__main__':
    parser = get_option_parser()
    args = parser.parse_args()
    results = gather_metrics(args.input_folder, args.eval_domain)
    write_report(results, args.eval_domain, sys.stdout)
