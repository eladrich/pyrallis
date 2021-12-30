
<p align="center"><img src="pyrallis_logo.png" alt="logo" width="70%" /></p>

# Pyrallis - Simple Configuration with Dataclasses

> Pyrausta (also called pyrallis (πυραλλίς), pyragones) is a mythological insect-sized dragon from Cyprus.
 
`Pyrallis` is a simple library, derived from `simple-parsing`, for automagically creating project configuration from a dataclass.

![](argparse2pyrallis.gif)

## Why `pyrallis`?

With `pyrallis` your configuration is linked directly to your pre-defined `dataclass`, allowing you to easily create different configuration structures, including nested ones, using an object-oriented design. The parsed arguments are used to initialize your `dataclass`, giving you the typing hints and automatic code completion of a full `dataclass` object.

## Installing `pyrallis`
Installing `pyrallis` is super-easy via PyPi
```bash
pip install pyrallis
```

## My First Pyrallis Example :baby:
There are several key features to pyrallis but at its core pyrallis simply allows defining an argument parser using a dataclass.
=== "pyrallis"

    ``` python title="train_model.py"  linenums="1"
    from dataclasses import dataclass
    from pyrallis import ArgumentParser
    
    
    @dataclass
    class TrainConfig:
        """ Training config for Machine Learning """
        workers: int = 8 # The number of workers for training
        exp_name: str = 'default_exp' # The experiment name

    def main():
        cfg = ArgumentParser(config_class=TrainConfig).parse_args()
        print(f'Training {cfg.exp_name} with {cfg.workers} workers...')

    ```

=== "argparse"

    ``` python title="train_model.py"  linenums="1"
    from argparse import ArgumentParser, Namespace


    def get_config() -> Namespace:
        parser = ArgumentParser(description='Training config for Machine Learning')
        parser.add_argument('--workers', type=int, default=8,
                            help='The number of workers for training')
        parser.add_argument('--exp_name', type=str, default='default_exp',
                            help='The experiment name')
        return parser.parse_args()

    def main():
        cfg = get_config()
        print(f'Training {cfg.exp_name} with {cfg.workers} workers...')

    ```
The arguments can then be specified using command-line arguments, a `yaml` configuration file, or both

```console
$ python train_model.py --CONFIG=some_config.yaml --exp_name=my_first_exp
Training my_first_exp with 42 workers...
```
Assuming the following configuration file
``` yaml title="some_config.yaml"
exp_name: my_yaml_exp
workers: 42
```

### Key Features
Building on that design pyrallis offers some really enjoyable features including 

* Builtin IDE support for autocompletion and linting thanks to the structured config.
* Joint reading from command-line and a config file, with support for specifying default config_path for the ArgumentParser
```python
cfg = ArgumentParser(config_class=TrainConfig,config_path='/configs/default_config.yaml').parse_args()
```
* Support for builtin dataclass features, such as `__post_init__` and `@property`
* Support for nesting and inheritance of dataclasses, nested arguments are automatically created!
* A magical `@pyrallis.wrap()` decorator for wrapping your main class
=== "@pyrallis.wrap"

    ``` python
    @pyrallis.wrap()
    def main(cfg: TrainConfig):
        print(f'Training {cfg.exp_name} with {cfg.workers} workers...')
    ```

=== "pyrallis.ArgumentParser"

    ``` python
    def main():
        cfg = ArgumentParser(config_class=TrainConfig).parse_args()
        print(f'Training {cfg.exp_name} with {cfg.workers} workers...')
    ```
* Easy extension to new types using `pyrallis.encode.register` and `pyrallis.decode.register`
* Easy loading and saving of existing configurations using `pyrallis.dump` and `pyrallis.load`
* Magical `--help` creation from dataclasses, taking into account the comments as well!

That's basically it, see the rest of this documentation for more complete tutorial and info.

