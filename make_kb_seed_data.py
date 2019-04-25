import os
from argparse import ArgumentParser
import json
import copy
import shutil
from collections import defaultdict

import nltk

tokenizer = nltk.RegexpTokenizer(r'\w+|#\w+|<\w+>|%\w+|[^\w\s]+').tokenize


def process_kb(in_kb):
    all_values = set({})
    items = in_kb.get('items', {})
    if items is None:
        items = {}
    for item in items:
        for key, value in item.items():
            all_values.add(value)
    return sorted(all_values, key=len)


def flatten_entities(in_entities_map):
    result = []
    for key, values_list in in_entities_map.items():
        for value in values_list:
            if isinstance(value, dict):
                result += map(lambda x: str(x).lower(), value.values())
            else:
                result.append(str(value).lower())
    return sorted(result, key=len, reverse=True)


def extract_entities(in_utterance, in_kb_entries):
    result = set([])
    for kb_entry in in_kb_entries:
        if kb_entry in in_utterance:
            in_utterance = in_utterance.replace(kb_entry, '__entity__')
            result.add(kb_entry)
    return result


def flatten_kb_entry(in_entry):
    result = []
    for key, value in in_entry.items():
        result.append(key)
        if isinstance(value, list):
            result += value
        elif isinstance(value, dict):
            result += flatten_kb_entry(value)
        else:
            result.append(str(value))
    return result


def get_closest_kb_entry(in_kb, in_utterance):
    jaccard_sim = lambda x, y: len(set(x).intersection(y)) // len(set(x).union(y))
    max_sim, max_idx = -1.0, -1
    for idx, entry in enumerate(in_kb):
        sim = jaccard_sim(entry, in_utterance)
        if max_sim < sim:
            max_sim, max_idx = sim, idx
    return in_kb[max_idx]


def extract_seed_data(in_dialog, in_kb_entities):
    result = []
    kb_entries = in_dialog['scenario']['kb']['items']
    if not kb_entries:
        return []
    kb_items_processed = [tokenizer(' '.join(flatten_kb_entry(entry))) for entry in kb_entries]
    for utterance in in_dialog['dialogue']:
        utterance_entities = extract_entities(utterance['data']['utterance'], in_kb_entities)
        if not len(utterance_entities):
            continue
        utterance_processed = tokenizer(utterance['data']['utterance'])
        kb_entry = get_closest_kb_entry(kb_items_processed, utterance_processed)
        result.append([kb_entry, utterance['data']['utterance']])
    return result


def extract_seed_data_from_dataset(in_dataset, in_kb_entities):
    result = defaultdict(lambda: [])
    for dialog in in_dataset:
        domain = dialog['scenario']['task']['intent']
        kb_utt_pairs = extract_seed_data(dialog, in_kb_entities)
        result[domain] += kb_utt_pairs
    return result


def process_dataset(in_dataset_folder):
    datasets = {}
    for dataset_name in ['train', 'dev', 'test']:
        filename = 'kvret_{}_public.json'.format(dataset_name)
        with open(os.path.join(in_dataset_folder, filename)) as dataset_in:
            datasets[filename] = json.load(dataset_in)
    with open(os.path.join(in_dataset_folder, 'kvret_entities.json')) as entities_in:
        entities = json.load(entities_in)
    entities_flat = flatten_entities(entities)

    seed_data_map = extract_seed_data_from_dataset(datasets['kvret_train_public.json'], entities_flat)
    return seed_data_map


def configure_argument_parser():
    parser = ArgumentParser()
    parser.add_argument('dataset_folder')
    parser.add_argument('output_file')
    return parser


if __name__ == '__main__':
    parser = configure_argument_parser()
    args = parser.parse_args()
    seed_data = process_dataset(args.dataset_folder)
    with open(args.output_file, 'w') as file_out:
        json.dump(seed_data, file_out)
