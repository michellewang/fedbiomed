#!/usr/bin/env python

import argparse
from pathlib import Path
from types import new_class

import numpy as np
import pandas as pd

PATH_MANIFEST_RELATIVE = Path("manifest.tsv")
PATH_PHENO_RELATIVE = Path("tabular/harmonized.tsv")
PATH_ASEG_RELATIVE = Path(
    "derivatives/freesurfer/7.3.2/idp/fs_stats-0.2.1/fs7.3.2-aseg-volume.tsv"
)
PATH_APARC_RELATIVE = Path(
    "derivatives/freesurfer/7.3.2/idp/fs_stats-0.2.1/fs7.3.2-aparc.DKTatlas-thickness.tsv"
)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "reference_dataset_root",
        type=Path,
        help="Path to the root directory of a reference Nipoppy dataset",
    )
    parser.add_argument(
        "new_dataset_root",
        type=Path,
        help="Path to the root directory of a new Nipoppy dataset",
    )
    args = parser.parse_args()
    reference_dataset_root = args.reference_dataset_root
    new_dataset_root = args.new_dataset_root

    rng = np.random.default_rng(seed=1)

    df_pheno_reference = pd.read_csv(
        reference_dataset_root / PATH_PHENO_RELATIVE,
        sep="\t",
        dtype=str,
    )
    df_aseg_reference = pd.read_csv(
        reference_dataset_root / PATH_ASEG_RELATIVE, sep="\t", dtype=str
    ).set_index(["participant_id", "session_id"])
    df_aparc_reference = pd.read_csv(
        reference_dataset_root / PATH_APARC_RELATIVE, sep="\t", dtype=str
    ).set_index(["participant_id", "session_id"])

    df_pheno_new = df_pheno_reference.copy()
    df_pheno_new = df_pheno_new.query("`nb:SessionID` == '01'")
    df_pheno_new["nb:ParticipantID"] = [
        f"{i:03d}" for i in range(1, len(df_pheno_new) + 1)
    ]
    df_pheno_new = df_pheno_new.set_index(["nb:ParticipantID", "nb:SessionID"])
    df_pheno_new["nb:Age"] = rng.integers(50, 80, size=len(df_pheno_new))

    for col in df_pheno_new.columns:
        idx_col = np.arange(len(df_pheno_new))
        rng.shuffle(idx_col)
        df_pheno_new[col] = df_pheno_new[col].iloc[idx_col].values
    print(df_pheno_new)
    df_pheno_new.to_csv(new_dataset_root / PATH_PHENO_RELATIVE, sep="\t")

    df_manifest_new = pd.DataFrame(
        {
            "participant_id": df_pheno_new.index.get_level_values("nb:ParticipantID"),
            "visit_id": df_pheno_new.index.get_level_values("nb:SessionID"),
            "session_id": df_pheno_new.index.get_level_values("nb:SessionID"),
        }
    )
    df_manifest_new["datatype"] = np.nan
    df_manifest_new = df_manifest_new.set_index(["participant_id", "session_id"])
    print(df_manifest_new)
    df_manifest_new.to_csv(
        new_dataset_root / PATH_MANIFEST_RELATIVE, sep="\t", index=True
    )

    df_aseg_new = pd.DataFrame(
        data=rng.normal(size=(len(df_pheno_new), len(df_aseg_reference.columns))),
        columns=df_aseg_reference.columns,
        index=df_manifest_new.index,
    )
    print(df_aseg_new)
    df_aseg_new.to_csv(new_dataset_root / PATH_ASEG_RELATIVE, sep="\t")

    df_aparc_new = pd.DataFrame(
        data=rng.normal(size=(len(df_pheno_new), len(df_aparc_reference.columns))),
        columns=df_aparc_reference.columns,
        index=df_manifest_new.index,
    )
    print(df_aparc_new)
    df_aparc_new.to_csv(new_dataset_root / PATH_APARC_RELATIVE, sep="\t")
