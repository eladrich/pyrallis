<p align="center"><img src="https://raw.githubusercontent.com/eladrich/pyrallis/master/docs/pyrallis_logo.png" alt="logo" width="70%" /></p>


# Pyrallis - Simple Configuration with Dataclasses

> Pyrausta (also called pyrallis (πυραλλίς), pyragones) is a mythological insect-sized dragon from Cyprus.

`Pyrallis` is a simple library, derived from `simple-parsing`, for automagically creating project configuration from a dataclass.


<p align="center"><img src="https://github.com/eladrich/pyrallis/raw/master/docs/argparse2pyrallis.gif" alt="GIF" width="100%" /></p>

## Why `pyrallis`?

With `pyrallis` your configuration is linked directly to your pre-defined `dataclass`, allowing you to easily create different configuration structures, including nested ones, using an object-oriented design. The parsed arguments are used to initialize your `dataclass`, giving you the typing hints and automatic code completion of a full `dataclass` object.


## My First Pyrallis Example 👶
There are several key features to pyrallis but at its core pyrallis simply allows defining an argument parser using a dataclass.

```python 
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

The arguments can then be specified using command-line arguments, a `yaml` configuration file, or both.

```console
$ python train_model.py --CONFIG=some_config.yaml --exp_name=my_first_exp
Training my_first_exp with 42 workers...
```
Assuming the following configuration file
```yaml
exp_name: my_yaml_exp
workers: 42
```

### Key Features
Building on that design `pyrallis` offers some really enjoyable features including 

* Builtin IDE support for autocompletion and linting thanks to the structured config. 🤓
* Joint reading from command-line and a config file, with support for specifying a default config file. 😍
* Support for builtin dataclass features, such as `__post_init__` and `@property` 😁
* Support for nesting and inheritance of dataclasses, nested arguments are automatically created! 😲
* A magical `@pyrallis.wrap()` decorator for wrapping your main class 🪄
* Easy extension to new types using `pyrallis.encode.register` and `pyrallis.decode.register` 👽
* Easy loading and saving of existing configurations using `pyrallis.dump` and `pyrallis.load` 💾
* Magical `--help` creation from dataclasses, taking into account the comments as well! 😎


## Getting to Know The `pyrallis` API in 5 Simple Steps 🐲

The best way to understand the full `pyrallis` API is through examples, let's get started!

###  🐲 1/5 `pyrallis.ArgumentParser` for `dataclass` Parsing 🐲

Creation of an argparse configuration is really simple, just use `pyrallis.ArgumentParser` on your predefined dataclass.

```python
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
    cfg = pyrallis.ArgumentParser(config_class=TrainConfig).parse_args()
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
usage: train_model.py [-h] [--CONFIG str] [--workers int] [--exp_name str]

optional arguments:
  -h, --help      show this help message and exit
  --CONFIG str    Path for a config file to parse with pyrallis (default:
                  None)

TrainConfig ['options']:
   Training config for Machine Learning

  --workers int   The number of workers for training (default: 8)
  --exp_name str  The experiment name (default: default_exp)
```



### 🐲 2/5 The `pyrallis.wrap` Decorator 🐲
The `pyrallis.ArgumentParser` syntax is too cumbersome?
```python
def main():
    cfg = pyrallis.ArgumentParser(config_class=TrainConfig).parse_args()
    print(f'Training {cfg.exp_name} with {cfg.workers} workers...')
```
One can equiavlently use the `pyrallis.wrap` syntax 😎 
```python
@pyrallis.wrap()
def main(cfg: TrainConfig):
    # The decorator automagically uses the type hint to parsers arguments into TrainConfig
    print(f'Training {cfg.exp_name} with {cfg.workers} workers...')
```
We will use this syntax for the rest of our tutorial.


### 🐲 3/5 Better Configs Using Inherent `dataclass` Features 🐲
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


### 🐲 4/5 Building Hierarchical Configurations 🐲
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

### 🐲 5/5 Easy Serialization with `pyrallis.dump` 🐲
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
cfg = pyrallis.ArgumentParser(config_class=TrainConfig,
                              config_path='/share/configs/config.yaml').parse_args()
# or the decorator synrax
@pyrallis.wrap(config_path='/share/configs/config.yaml')

# or with the CONFIG argument
python my_script.py --log.exp_name=readme_exp --CONFIG=/share/configs/config.yaml

# Or if you just want to load from a .yaml without cmd parsing
cfg = pyrallis.load(TrainConfig, '/share/configs/config.yaml')
```
> Command-line arguments have a higher priority and will override the configuration file


Finally, one can easily extend the serialization to support new types 🔥
```python
# For decoding from cmd/yaml
pyrallis.decode.register(np.ndarray,np.asarray)

# For encoding to yaml 
pyrallis.encode.register(np.ndarray, lambda x: x.tolist())

# Or with the wrapper version instead 
@pyrallis.encode.register
def encode_array(arr : np.ndarray) -> str:
    return arr.tolist()
```

#### 🐲 That's it you are now a `pyrallis` expert! 🐲



## Why Another Parsing Library?
<img src="https://imgs.xkcd.com/comics/standards_2x.png" alt="XKCD 927 - Standards" width="70%" />

> XKCD 927 - Standards 

The builtin `argparse` has many great features but is somewhat outdated :older_man: with one its greatest weakness being the lack of typing. This has led to the development of many great libraries tackling different weaknesses of `argparse` (shout out for all the great projects out there! You rock! :metal:).  

In our case, we were looking for a library that would  support the vanilla `dataclass` without requiring dedicated classes, and would have a loading interface from both command-line and files. The closest candidates were `hydra` and `simple-parsing`, but they weren't exactly what we were looking for. Below are the pros and cons from our perspective:
#### [Hydra](https://github.com/facebookresearch/hydra)
A framework for elegantly configuring complex applications from Facebook Research.
* Supports complex configuration from multiple files and allows for overriding them from command-line.
* Does not support non-standard types, does not play nicely with `datclass.__post_init__`and requires a `ConfigStore` registration.
#### [SimpleParsing](https://github.com/lebrice/SimpleParsing)
A framework for simple, elegant and typed Argument Parsing by Fabrice Normandin
* Strong integration with `argparse`, support for nested configurations together with standard arguments.
* No support for joint loading from command-line and files, dataclasses are still wrapped by a Namespace, requires dedicated classes for serialization.

We decided to create a simple hybrid of the two approaches, building from `SimpleParsing` with some `hydra` features in mind. The result, `pyrallis`, is a simple library that that is relatively low on features, but hopefully excels at what it does.

If `pyrallis` isn't what you're looking for we strongly advise you to give `hydra` and `simpleParsing` a try (where other interesting option include `click`, `ext_argpase`, `jsonargparse`, `datargs` and `tap`). If you do :heart: `pyrallis` then welcome aboard! We're gonna have a great journey together! 🐲

## Design Choices and Some More

### Uniform Parsing Syntax
For parsing files we opted for `yaml` as our format of choice, following `hydra`, due to its concise format. 
Now, let us assume we have the following `.yaml` file which `yaml` successfully handles:
```yaml
compute:
  worker_inds: [0,2,3]
```
Intuitively we would also want users to be able to use the same syntax 
```cmd
python my_app.py --compute.worker_inds=[0,2,3]
```

However, the more standard syntax for an argparse application would be 
```cmd
python my_app.py --compute.worker_inds 0 2 3
```

We decided to use the same syntax as in the `yaml` files to avoid confusion when loading from multiple sources. 

### Beware of Mutable Types (or use pyrallis.field)
Dataclasses are great (really!) but using mutable fields can sometimes be confusing. For example, say we try to code the following dataclass
```python
@dataclass
class OptimConfig:
    worker_inds: List[int] = []
    # Or the more explicit version
    worker_inds: List[int] = field(default=[])
```
As `[]` is mutable we would actually initialize every instance of this dataclass with the same list instance, and thus is not allowed. Instead `dataclasses` would direct you the default_factory function, which calls a factory function for generating the field in every new instance of your dataclass.

```python
worker_inds: List[int] = field(default_factory=list)
```

Now, this works great for empty collections, but what would be the alternative for
```python
worker_inds: List[int] = field(default=[1,2,3])
```
Well, you would have to create a dedicated factory function that regenerates the object, for example
```python
worker_inds: List[int] = field(default_factory=lambda : [1,2,3])
```
Kind of annoying and could be confusing for a new guest reading your code :confused: Now, while this isn't really related to parsing/configuration we decided it could be nice to offer a sugar-syntax for such cases as part of `pyrallis`
```python
from pyrallis import field
worker_inds: List[int] = field(default=[1,2,3], is_mutable=True)
```
The `pyrallis.field` behaves like the regular `dataclasses.field` with an additional `is_mutable` flag. When toggled, the `default_factory` is created automatically, offering the same functionally with a more reader-friendly syntax.



# TODOs:
- [x] Create documentation page
> Create a full documentation with mkdocs
- [x] Improve warnings and logs
> Find a better way to show what failed
- [ ] Think on relative paths
- [ ] Fix error with default Dict and List
>         Underlying error: No decoding function for type ~KT, consider using pyrallis.decode.register
