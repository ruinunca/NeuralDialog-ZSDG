import os
from argparse import ArgumentParser
import json
import copy
import shutil


def process_kb(in_kb):
    all_values = set({})
    items = in_kb.get('items', {})
    if items is None:
        items = {}
    for item in items:
        for key, value in item.items():
            all_values.add(value)
    return sorted(all_values, key=len)


def delexicalize_utterance(in_utterance, in_kb_entries):
    for kb_entry in in_kb_entries:
        if kb_entry in in_utterance:
            in_utterance = in_utterance.replace(kb_entry, '__entity__')
    return in_utterance


def delexicalize_dialog(in_dialog):
    result = copy.deepcopy(in_dialog)
    kb_entries = process_kb(in_dialog['scenario'].get('kb', {}))
    for turn_idx, turn in enumerate(result['dialogue']):
        turn['data']['utterance'] = delexicalize_utterance(turn['data']['utterance'], kb_entries)
    return result


def process_dataset(in_dataset_folder):
    datasets = {}
    for dataset_name in ['train', 'dev', 'test']:
        filename = 'kvret_{}_public.json'.format(dataset_name)
        with open(os.path.join(in_dataset_folder, filename)) as dataset_in:
            datasets[filename] = json.load(dataset_in)
    for dataset_name, dataset in datasets.items():
        for idx, dialog in enumerate(dataset):
            dataset[idx] = delexicalize_dialog(dialog)
    return datasets


def save_dataset(in_src_folder, in_tgt_folder, in_datasets):
    if not os.path.exists(in_tgt_folder):
        os.makedirs(in_tgt_folder)
    for filename in os.listdir(in_src_folder):
        if filename not in in_datasets:
            if os.path.isdir(os.path.join(in_src_folder, filename)):
                shutil.copytree(os.path.join(in_src_folder, filename),
                                os.path.join(in_tgt_folder, filename))
            else:
                shutil.copy(os.path.join(in_src_folder, filename), in_tgt_folder)
        else:
            with open(os.path.join(in_tgt_folder, filename), 'w') as json_out:
                json.dump(in_datasets[filename], json_out)


def configure_argument_parser():
    parser = ArgumentParser()
    parser.add_argument('dataset_folder')
    parser.add_argument('output_folder')
    return parser


if __name__ == '__main__':
    parser = configure_argument_parser()
    args = parser.parse_args()
    datasets = process_dataset(args.dataset_folder)
    save_dataset(args.dataset_folder, args.output_folder, datasets)
