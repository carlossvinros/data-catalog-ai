"""Client for download Kaggle datasets into the raw data layer."""

from pathlib import Path

import kaggle
from rich.console import Console

console = Console()

# diretório padrão para download dos datasets, parents significa que vamos subir 3 níveis de pastas a partir do arquivo atual
_DEFAULT_RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"


class KaggleDatasetClient:
    """Authenticated client that downloads Kaggle datasets to the raw data layer.

    Authentication is resolved automatically from environment variabels
    ``KAGGLE_USERNAME`` and ``KAGGLE_KEY``, or from some .json file in the user's home directory.

    Args:
        raw_data_dir: Root directory for raw datasets. Defaults to ``data/raw/``.
            relative to the project root.
    """

    def __init__(self, raw_data_dir: Path = _DEFAULT_RAW_DIR) -> None:
        self._raw_data_dir = raw_data_dir
        self._api = kaggle.api
        self._api.authenticate()

    def download(self, dataset_slug: str) -> Path:
        """Downloads a dataset if not already present in the local cache.

        Args:
            dataset_slug: Kaggle dataset identifier in ``owner/dataset_name`` format.
                Example: ``arashnic/microsoft-geolife-gps-trajectory-dataset"``.

        Returns:
            Absolute path to the directory containing the dataset files.
        """

        destination = self._resolve_destination(dataset_slug)

        if self._is_cached(destination):
            console.print(f"[green]✔ Cache hit:[/green] {destination}")
            return destination

        destination.mkdir(parents=True, exist_ok=True)
        console.print(f"[blue]↓ Downloading dataset {dataset_slug}")

        self._api.dataset_download_files(
            dataset=dataset_slug,
            path=destination,
            unzip=True,
            quiet=False,  # mostra o progresso do download
        )

        console.print(f"[green]✔ Saved to:[/green] {destination}")
        return destination

    def _resolve_destination(self, dataset_slug: str) -> Path:
        owner, dataset_name = dataset_slug.split(
            "/", maxsplit=1
        )  # maxsplit=1 para quebrar apenas uma vez
        return self._raw_data_dir / owner / dataset_name

    def _is_cached(self, destination: Path) -> bool:
        return destination.exists() and any(
            destination.iterdir()
        )  # verifica se diretório existe e se contém arquivos
