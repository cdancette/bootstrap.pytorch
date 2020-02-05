import ray
from ray import tune
from ray.tune.examples.mnist_pytorch import get_data_loaders, ConvNet, train, test
import os
import argparse
import subprocess
import yaml


def train_func(config):
    # change exp dir

    print("*****************" + os.getcwd())
    option_path = config.pop("option_file")

    os.chdir("/home/dancette/doc/rubi.bootstrap.pytorch")

    command = ["python", "-m", "bootstrap.run",
        "-o", option_path,
        "--exp.resume", "last",
        "--exp.resume_or_start", "true",  # TODO : réfléchir à ce qu'on veut vraiment avoir ici..
    ]

    exp_dir = config.pop("exp_dir_prefix")

    arguments = []
    for name, value in config.items():
        arguments.append(f"--{name}")
        arguments.append(str(value))
        exp_dir += f"--{name.split('.')[-1]}_{value}"
    
    command += ["--exp.dir", exp_dir]
    command += arguments
    print("************* COMMAND", command)

    subprocess.run(command, check=True)
    
    # for i in range(10):
    #     train(model, optimizer, train_loader)
    #     acc = test(model, test_loader)
    #     tune.track.log(mean_accuracy=acc)  # TODO

# TODO
# analysis = tune.run(
#     train_mnist, config={"lr": tune.grid_search([0.001, 0.01, 0.1])})

# print("Best config: ", analysis.get_best_config(metric="mean_accuracy"))

def build_tune_config(option_path):
    with open(option_path, 'r') as yaml_file:
        options = yaml.load(yaml_file)

    config = {}
    for item in options['gridsearch']['params']:
        key = item["name"]
        config[key] = tune.grid_search(item["values"])

    config["exp_dir_prefix"] = os.path.join(os.getcwd(), options["exp"]["dir"])
    config["option_file"] = os.path.join(os.getcwd(), option_path)
    return config, options["gridsearch"]["name"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--path_opts", required=True, help="Main file")
    parser.add_argument("-g", "--gpu-per-trial", type=float, default=0.5, help="Percentage of gpu needed for one training")
    parser.add_argument("-c", "--cpu-per-trial", type=float, default=2, help="Percentage of gpu needed for one training")
    args = parser.parse_args()

    config, name = build_tune_config(args.path_opts)

    ray.init()
    tune.run(
        train_func,
        name=name,
        # stop={"avg_inc_acc": 100},
        config=config,
        resources_per_trial={
            "cpu": args.cpu_per_trial,
            "gpu": args.gpu_per_trial, 
        },
        local_dir="ray_results",
    )

if __name__=="__main__":
    main()
