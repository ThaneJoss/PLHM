from __future__ import annotations

from pathlib import Path

import hydra
from hydra.utils import get_original_cwd
from omegaconf import DictConfig

from plhm.app import run_training
from plhm.hydra_loader import load_app_settings


@hydra.main(config_path="conf", config_name="config", version_base="1.3")
def main(cfg: DictConfig) -> None:
    app_settings = load_app_settings(cfg)
    project_root = Path(get_original_cwd())
    run_training(app_settings, project_root)


if __name__ == "__main__":
    main()
