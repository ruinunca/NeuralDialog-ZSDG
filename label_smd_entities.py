from __future__ import print_function

import os
from argparse import ArgumentParser
import json
import copy

WARN_COUNTER = 0


def canonicalize_kb_entries(in_kb):
    global WARN_COUNTER
    result = []
    item_set = set([]) 
    main_column = in_kb['column_names'][0]
    if in_kb.get('items', []) is None:
        return result
    for item in in_kb.get('items', []):
        for column in in_kb['column_names'][1:]:
            key = item[main_column].replace(' ', '_')
            rel = column.replace(' ', '_')
            val = item[column]
            if '{}_{}'.format(key, rel) in item_set:
                print('[WARN] Non-unique canonical KB entries!')
                WARN_COUNTER += 1
            item_set.add('{}_{}'.format(key, rel))
            result.append(('{}_{}'.format(key, rel), val))
        main_key = item[main_column].replace(' ', '_')
        main_rel = main_column.replace(' ', '_')
        main_val = item[main_column]
        result.append(('{}_{}'.format(main_key, main_rel), main_val))
    return result


def canonicalize_dialog(in_dialog):
    result = copy.deepcopy(in_dialog)
    kb_entries_canonicalized = canonicalize_kb_entries(in_dialog['scenario'].get('kb', {}))
    for turn_idx, turn in enumerate(result['dialogue']):
        for kb_entry_key, kb_entry_value in kb_entries_canonicalized:
            if kb_entry_value in turn['data']['utterance']:
                # print '[Turn {}] {} ---> {}'.format(turn_idx, kb_entry_value, kb_entry_key)
                turn['data']['utterance'] = turn['data']['utterance'].replace(kb_entry_value, kb_entry_key)
    result['scenario']['kb']['item_canonical'] = {key: value for key, value in kb_entries_canonicalized}
    return result


def main(in_src_folder, in_dst_folder):
    with open(os.path.join(in_src_folder, 'kvret_entities.json')) as entities_in:
        entities = json.load(entities_in)
    if not os.path.exists(in_dst_folder):
        os.makedirs(in_dst_folder)
    datasets = {}
    for dataset_name in ['train', 'dev', 'test']:
        filename = 'kvret_{}_public.json'.format(dataset_name)
        with open(os.path.join(in_src_folder, filename)) as dataset_in:
            datasets[filename] = json.load(dataset_in)
        for idx, dialog in enumerate(datasets[filename]):
            datasets[filename][idx] = canonicalize_dialog(dialog)
        with open(os.path.join(in_dst_folder, filename), 'w') as dataset_out:
            json.dump(datasets[filename], dataset_out)
    with open(os.path.join(in_dst_folder, 'kvret_entities.json'), 'w') as entities_out:
        json.dump(entities, entities_out)
    print('Processing finished with {} warnings'.format(WARN_COUNTER))


def get_argument_parser():
    parser = ArgumentParser()
    parser.add_argument('source_folder')
    parser.add_argument('result_folder')
    return parser


if __name__ == "__main__":
    parser = get_argument_parser()
    args = parser.parse_args()

    main(args.source_folder, args.result_folder)
