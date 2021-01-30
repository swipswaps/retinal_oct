"""W&B Sweep Functionality."""
import os
import signal
import subprocess
import sys
import json
from typing import Tuple
from ast import literal_eval
import pdb

DEFAULT_CONFIG = {
    "dataset": "RetinaDatasetWrapper", 
    "train_args": {
        "learning_rate": 0.01,
        "epochs": 10,
        "learning_rate_scaling": "linear",
        "warmup_epochs": 10,
        "batch_size": 256,
        "num_classes": 4,
        "use_blur": True,
        "proj_head_mode": "nonlinear",
        "proj_out_dim" : 128,
        "num_proj_layers": 3,
        "ft_proj_selector": 0,
        "resnet_depth": 18,
        "resnet_width_multiplier": 1,
        "resnet_se_ratio": 0.0,
        "resnet_sk_ratio": 0.0,
        "hidden_norm": True,
        "temperature" :1.0,
        "IMG_SIZE": 128
    }
}


def args_to_json(default_config: dict, preserve_args: tuple = ("gpu", "save")) -> Tuple[dict, list]:
    """Convert command line arguments to nested config values

    i.e. run_sweep.py --dataset_args.foo=1.7

    {
        "dataset_args": {
            "foo": 1.7
        }
    }

    """
    args = []
    config = default_config.copy()
    key, val = None, None
    for arg in sys.argv[1:]:
        if "=" in arg:
            key, val = arg.split("=")
        elif key:
            val = arg
        else:
            key = arg
        if key and val:
            parsed_key = key.lstrip("-").split(".")
            if parsed_key[0] in preserve_args:
                args.append("--{}={}".format(parsed_key[0], val))
            else:
                nested = config
                for level in parsed_key[:-1]:
                    nested[level] = config.get(level, {})
                    nested = nested[level]
                try:
                    # Convert numerics to floats / ints
                    val = literal_eval(val)
                except ValueError:
                    pass
                nested[parsed_key[-1]] = val
            key, val = None, None
    return config, args


def main():
    config, args = args_to_json(DEFAULT_CONFIG)
    env = {k: v for k, v in os.environ.items() if k not in ("WANDB_PROGRAM", "WANDB_ARGS")}
    print ('args', *args)

    # pylint: disable=subprocess-popen-preexec-fn
    run = subprocess.Popen(
        ["python", "training/run_simclr_experiment.py", *args, json.dumps(config)], env=env, preexec_fn=os.setsid,
    )  # nosec
    signal.signal(signal.SIGTERM, lambda *args: run.terminate())
    run.wait()

if __name__ == "__main__":
    main()