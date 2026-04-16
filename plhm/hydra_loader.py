from __future__ import annotations

from omegaconf import DictConfig, OmegaConf

from plhm.settings import AppSettings, DataSettings, MlflowSettings, ModelSettings, TrainerSettings


def load_app_settings(cfg: DictConfig) -> AppSettings:
    resolved = OmegaConf.to_container(cfg, resolve=True)
    if not isinstance(resolved, dict):
        raise TypeError("Hydra config must resolve to a mapping.")

    return AppSettings(
        seed=int(resolved["seed"]),
        data=DataSettings(**resolved["data"]),
        model=ModelSettings(**resolved["model"]),
        trainer=TrainerSettings(**resolved["trainer"]),
        mlflow=MlflowSettings(**resolved["mlflow"]),
    )
