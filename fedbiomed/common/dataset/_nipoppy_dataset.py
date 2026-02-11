# This file is originally part of Fed-BioMed
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Callable, Dict, List, Optional, Tuple

import json
from functools import cached_property
from pathlib import Path
import numpy as np
import pandas as pd

from fedbiomed.common.constants import ErrorNumbers
from fedbiomed.common.dataset._dataset import Dataset
from fedbiomed.common.dataset_types import DataReturnFormat
from fedbiomed.common.exceptions import FedbiomedError
from nipoppy import NipoppyDataRetriever


class NipoppyDataset(Dataset):

    def __init__(
        self,
        target: str,
        phenotypes: List[str],
        derivatives: List[Tuple[str, str, str]],
        transform: Optional[Callable[[pd.Series], pd.Series]] = None,
        target_transform: Optional[Callable[[float], float]] = None,
    ) -> None:
        """Initialize the NipoppyDataset."""
        self.target = target
        self.phenotypes = phenotypes
        self.derivatives = derivatives
        self.transform = transform
        self.target_transform = target_transform

    def complete_initialization(
        self, controller_kwargs: Dict[str, Any], to_format: DataReturnFormat
    ) -> None:
        """Finalize initialization of object to be able to recover items

        Args:
            path: path to dataset
            to_format: format associated to expected return format
        """

        self.path = controller_kwargs.get("root", None)
        if self.path is None:
            raise FedbiomedError(
                f"{ErrorNumbers.FB632.value}: Custom Dataset ERROR: 'root' must be provided in controller_kwargs to specify dataset location."
            )
        self._to_format = to_format

        # Call user defined read function to read the dataset
        try:
            self.read()
        except Exception as e:
            raise FedbiomedError(
                f"{ErrorNumbers.FB632.value}: Failed to read "
                f"from dataset using read method. Please see error: {e}"
            ) from e

        try:
            sample = self[0]
        except Exception as e:
            raise FedbiomedError(
                f"{ErrorNumbers.FB632.value}: Failed to retrieve item "
                f"from dataset using get_item method. Please see error: {e}"
            ) from e
        if not isinstance(sample, tuple) or len(sample) != 2:
            raise FedbiomedError(
                f"{ErrorNumbers.FB632.value}: get_item method must return a tuple of two elements"
                f" (data, target), but got {type(sample).__name__} with"
                f" length {len(sample) if isinstance(sample, (list, tuple)) else 'N/A'}"
            )

        # Following line is just to check that dataset is well implemented
        # and it return correct data type respecting to to_format
        try:
            sample = self[0]
        except Exception as e:
            raise FedbiomedError(
                f"{ErrorNumbers.FB632.value}: Failed to retrieve item "
                f"from dataset using get_item method. Please see error: {e}"
            ) from e

    @cached_property
    def config(self) -> dict:
        dpath_parent = Path(self.path)
        return json.loads((dpath_parent / "global_config.json").read_text())

    def read(self):

        retriever = NipoppyDataRetriever(self.path)
        df = retriever.get_tabular_data(
            phenotypes=self.phenotypes,
            derivatives=self.derivatives,
        )

        self.df: pd.DataFrame = df
        self.y = self.df[[self.target]]
        self.X = self.df.drop(labels=[self.target], axis="columns")

        return self.X, self.y

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx) -> Tuple[np.ndarray, np.ndarray | None]:
        X = self.X.iloc[idx]
        y = self.y.iloc[idx]

        if self.transform:
            X = self.transform(X)
        if self.target_transform:
            y = self.target_transform(y)

        return X.to_numpy(), y.to_numpy()
