from pathlib import Path

from ephemeris._split_data_manager_genomes import (
    GalaxyHistoryIsBuildComplete,
    split_genomes,
    SplitOptions,
)

MERGED_YAML_STR = """
genomes:
    - dbkey: hg19_rCRS_pUC18_phiX174
      description: Homo sapiens (hg19 with mtDNA replaced with rCRS, and containing pUC18
        and phiX174)
      id: hg19_rCRS_pUC18_phiX174
      indexers:
      - data_manager_twobit_builder
      - data_manager_star_index_builder

    - dbkey: rn6
      description: Rat Jul. 2014 (RGSC 6.0/rn6) (rn6)
      id: rn6
      indexers:
      - data_manager_twobit_builder
      - data_manager_picard_index_builder
"""

DATA_MANAGER_YAML_STR = """
data_manager_twobit_builder:
  tool_id: 'toolshed.g2.bx.psu.edu/repos/devteam/data_manager_twobit_builder/twobit_builder_data_manager/0.0.2'
  tags:
  - genome
data_manager_picard_index_builder:
  tool_id: 'toolshed.g2.bx.psu.edu/repos/devteam/data_manager_picard_index_builder/data_manager/picard_index_builder/0.0.1'
  tags:
  - genome
data_manager_star_index_builder:
  tool_id: 'toolshed.g2.bx.psu.edu/repos/iuc/data_manager_star_index_builder/rna_star_index_builder_data_manager/0.0.5'
  tags:
  - genome
"""


def test_split_genomes(tmp_path: Path):
    merged = tmp_path / "genomes.yml"
    merged.write_text(MERGED_YAML_STR)

    data_managers = tmp_path / "data_managers.yml"
    data_managers.write_text(DATA_MANAGER_YAML_STR)

    split_path = tmp_path / "split"

    history_names = ["idc-hg19_rCRS_pUC18_phiX174-data_manager_star_index_builder"]
    is_build_complete = GalaxyHistoryIsBuildComplete(history_names)

    split_options = SplitOptions()
    split_options.merged_genomes_path = str(merged)
    split_options.split_genomes_path = str(split_path)
    split_options.data_managers_path = str(data_managers)
    split_options.is_build_complete = is_build_complete
    split_genomes(split_options)
    assert (split_path / "hg19_rCRS_pUC18_phiX174" / "data_manager_twobit_builder").exists()
    assert not (split_path / "hg19_rCRS_pUC18_phiX174" / "data_manager_star_index_builder").exists()
