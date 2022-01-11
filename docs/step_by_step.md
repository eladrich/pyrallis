# Pyrallis Step by Step

The best way to understand `pyrallis` is through examples, let's get started!

##  Basic Parsing

Creation of an argparse configuration is really simple, just use `pyrallis.parse` on your predefined dataclass.

```python title="train_model.py"  linenums="1"
from dataclasses import dataclass, field
import pyrallis


@dataclass
class TrainConfig:
    """ Training config for Machine Learning """
    # The number of workers for training
    workers: int = field(default=8)
    # The experiment name
    exp_name: str = field(default='default_exp')


def main():
    cfg = pyrallis.parse(config_class=TrainConfig)
    print(f'Training {cfg.exp_name} with {cfg.workers} workers...')


if __name__ == '__main__':
    main()
```

> Not familiar with `dataclasses`? you should probably check the [Python Tutorial](https://docs.python.org/3/library/dataclasses.html) and come back here.

The config can then be parsed directly from command-line
```console
$ python train_model.py --exp_name=my_first_model
Training my_first_model with 8 workers...
```
Oh, and `pyrallis` also generates an `--help` string automatically using the comments in your dataclass 🪄

```console
$ python train_model.py --help
usage: train_model.py [-h] [--config_path str] [--workers int] [--exp_name str]

optional arguments:
  -h, --help      show this help message and exit
  --config_path str    Path for a config file to parse with pyrallis (default:
                  None)

TrainConfig ['options']:
   Training config for Machine Learning

  --workers int   The number of workers for training (default: 8)
  --exp_name str  The experiment name (default: default_exp)
```


 
Don't like the `pyrallis.parse` syntax?
```python
def main():
    cfg = pyrallis.parse(config_class=TrainConfig)
    print(f'Training {cfg.exp_name} with {cfg.workers} workers...')
```
One can equivalently use the `pyrallis.wrap` syntax 😎 
```python
@pyrallis.wrap()
def main(cfg: TrainConfig):
    # The decorator automagically uses the type hint to parsers arguments into TrainConfig
    print(f'Training {cfg.exp_name} with {cfg.workers} workers...')
```
We will use this syntax for the rest of our tutorial.


## Using Inherent `dataclass` Features
When using a dataclass we can add additional functionality using existing `dataclass` features, such as the `post_init` mechanism or `@properties` :grin:
```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import pyrallis


@dataclass
class TrainConfig:
    """ Training config for Machine Learning """
    # The number of workers for training
    workers: int = field(default=8)
    # The number of workers for evaluation
    eval_workers: Optional[int] = field(default=None)
    # The experiment name
    exp_name: str = field(default='default_exp')
    # The experiment root folder path
    exp_root: Path = field(default=Path('/share/experiments'))

    def __post_init__(self):
        # A builtin method of dataclasses, used for post-processing our configuration.
        self.eval_workers = self.eval_workers or self.workers

    @property
    def exp_dir(self) -> Path:
        # Properties are great for arguments that can be derived from existing ones
        return self.exp_root / self.exp_name


@pyrallis.wrap()
def main(cfg: TrainConfig):
    print(f'Training {cfg.exp_name}...')
    print(f'\tUsing {cfg.workers} workers and {cfg.eval_workers} evaluation workers')
    print(f'\tSaving to {cfg.exp_dir}')
```

```console
$ python -m train_model.py --exp_name=my_second_exp --workers=42
Training my_second_exp...
    Using 42 workers and 42 evaluation workers
    Saving to /share/experiments/my_second_exp
```
> Notice that in all examples we use the explicit `dataclass.field` syntax. This isn't a requirement of `pyrallis` but rather a style choice. As some of your arguments will probably require `dataclass.field` (mutable types for example) we find it cleaner to always use the same notation.


## Building Hierarchical Configurations
Sometimes configs get too complex for a flat hierarchy 😕, luckily `pyrallis` supports nested dataclasses 💥

```python

@dataclass
class ComputeConfig:
    """ Config for training resources """
    # The number of workers for training
    workers: int = field(default=8)
    # The number of workers for evaluation
    eval_workers: Optional[int] = field(default=None)

    def __post_init__(self):
        # A builtin method of dataclasses, used for post-processing our configuration.
        self.eval_workers = self.eval_workers or self.workers


@dataclass
class LogConfig:
    """ Config for logging arguments """
    # The experiment name
    exp_name: str = field(default='default_exp')
    # The experiment root folder path
    exp_root: Path = field(default=Path('/share/experiments'))

    @property
    def exp_dir(self) -> Path:
        # Properties are great for arguments that can be derived from existing ones
        return self.exp_root / self.exp_name

# TrainConfig will be our main configuration class.
# Notice that default_factory is the standard way to initialize a class argument in dataclasses

@dataclass
class TrainConfig:
    log: LogConfig = field(default_factory=LogConfig)
    compute: ComputeConfig = field(default_factory=ComputeConfig)

@pyrallis.wrap()
def main(cfg: TrainConfig):
    print(f'Training {cfg.log.exp_name}...')
    print(f'\tUsing {cfg.compute.workers} workers and {cfg.compute.eval_workers} evaluation workers')
    print(f'\tSaving to {cfg.log.exp_dir}')
```
The argument parse will be updated accordingly
```console
$ python train_model.py --log.exp_name=my_third_exp --compute.eval_workers=2
Training my_third_exp...
    Using 8 workers and 2 evaluation workers
    Saving to /share/experiments/my_third_exp
```

## Easy Serialization
As your config get longer you will probably want to start working with configuration files. Pyrallis supports encoding a dataclass configuration into a `yaml` file 💾

The command `pyrallis.dump(cfg, open('run_config.yaml','w'))` will result in the following `yaml` file
```yaml
compute:
  eval_workers: 2
  workers: 8
log:
  exp_name: my_third_exp
  exp_root: /share/experiments
```
> `pyrallis.dump` extends `yaml.dump` and uses the same syntax.

Configuration files can also be loaded back into a dataclass, and can even be used together with the command-line arguments.
```python
cfg = pyrallis.parse(config_class=TrainConfig,
                              config_path='/share/configs/config.yaml')

# or the decorator synrax
@pyrallis.wrap(config_path='/share/configs/config.yaml')

# or with the CONFIG argument
python my_script.py --log.exp_name=readme_exp --config_path=/share/configs/config.yaml

# Or if you just want to load from a .yaml without cmd parsing
cfg = pyrallis.load(TrainConfig, '/share/configs/config.yaml')
```
> Command-line arguments have a higher priority and will override the configuration file


Finally, one can easily extend the serialization to support new types 🔥
```python
# For decoding from cmd/yaml
pyrallis.decode.register(np.ndarray,np.asarray)

# For encoding to yaml 
pyrallis.encode.register(np.ndarray, lambda x: str(list(x)))

# Or with the wrapper version instead 
@pyrallis.encode.register
def encode_array(arr : np.ndarray) -> str:
    return str(list(arr))
```
That's it you are now a `pyrallis` expert!