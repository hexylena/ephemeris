#!/usr/bin/env python
"""Helper script for IDC - not yet meant for public consumption.

This script splits genomes.yml into tasks that are meant to be sent to
run_data_managers.py - while excluding data managers executions specified
by genomes.yml that have already been executed and appear in the target
installed data table configuration.
"""
import logging
import os
import re
from copy import deepcopy
from typing import (
    Callable,
    Dict,
    List,
)

import yaml
from galaxy.util import safe_makedirs

from . import get_galaxy_connection
from .common_parser import (
    get_common_args,
)
from ._data_managers_to_tools import (
    DataManager,
    read_data_managers_configuration,
)
from .ephemeris_log import (
    disable_external_library_logging,
    setup_global_logger,
)

IsBuildComplete = Callable[[str, str], bool]


class SplitOptions:
    merged_genomes_path: str
    split_genomes_path: str
    data_managers_path: str
    is_build_complete: IsBuildComplete


def tool_id_for(indexer: str, data_managers: Dict[str, DataManager]) -> str:
    data_manager = data_managers[indexer]
    assert data_manager, f"Could not find a target data manager for indexer name {indexer}"
    return data_manager.tool_id


def split_genomes(split_options: SplitOptions) -> None:
    data_managers = read_data_managers_configuration(split_options.data_managers_path)
    split_genomes_path = split_options.split_genomes_path
    if not os.path.exists(split_options.split_genomes_path):
        safe_makedirs(split_genomes_path)
    with open(split_options.merged_genomes_path) as f:
        genomes_all = yaml.safe_load(f)
    genomes = genomes_all["genomes"]
    for genome in genomes:
        build_id = genome["id"]
        indexers = genome.get("indexers", [])
        for indexer in indexers:
            if split_options.is_build_complete(build_id, indexer):
                continue

            data_manager = {}
            run_task_yaml = {"data_managers": [data_manager]}
            tool_id = tool_id_for(indexer, data_managers)
            data_manager["id"] = tool_id
            params = [
                {"all_fasta_source": "{{ item.id }}"},
                {"sequence_name": "{{ item.name }}"},
                {"sequence_id": "{{ item.id }}"},
            ]
            if re.search("bwa", tool_id):
                data_manager["params"].append({"index_algorithm": "bwtsw"})
            if re.search("color_space", data_manager["id"]):
                continue

            data_manager["params"] = params

            item = deepcopy(genome)
            item.pop("indexers", None)
            item.pop("skiplist", None)

            data_manager["items"] = [item]

            task_file_dir = os.path.join(split_genomes_path, build_id, indexer)
            safe_makedirs(task_file_dir)
            task_file = os.path.join(task_file_dir, "run_data_managers.yaml")
            with open(task_file, "w") as of:
                yaml.safe_dump(run_task_yaml, of)


class GalaxyHistoryIsBuildComplete:

    def __init__(self, history_names: List[str]):
        self._history_names = history_names

    def __call__(self, build_id: str, indexer_name: str) -> bool:
        target_history_name = f"idc-{build_id}-{indexer_name}"
        return target_history_name in self._history_names


def _parser():
    """returns the parser object."""
    # login required to check history...
    parser = get_common_args(login_required=True)

    parser.add_argument('--merged-genomes-path', '-m', default="genomes.yml")
    parser.add_argument('--split-genomes-path', '-s', default="data_manager_tasks")
    parser.add_argument('--data-managers-path', default="data_managers.yml")


def get_galaxy_history_names(args) -> List[str]:
    gi = get_galaxy_connection(args, login_required=True)
    return [h["name"] for h in gi.histories.get_histories()]


def main():
    disable_external_library_logging()
    parser = _parser()
    args = parser.parse_args()
    log = setup_global_logger(name=__name__, log_file=args.log_file)
    if args.verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    is_build_complete = GalaxyHistoryIsBuildComplete(get_galaxy_history_names(args))

    split_options = SplitOptions()
    split_options.data_managers_path = args.data_managers_path
    split_options.merged_genomes_path = args.merged_genomes_path
    split_options.split_genomes_path = args.split_genomes_path
    split_options.is_build_complete = is_build_complete

    split_genomes(split_options)


if __name__ == "__main__":
    main()
