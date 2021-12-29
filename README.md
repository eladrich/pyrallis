<p align="center"><img src="https://github.com/eladrich/pyrallis/blob/master/docs/pyrallis_logo.png" alt="logo" width="70%" /></p>


# Pyrallis - Simple Configuration with Dataclasses

> Pyrausta (also called pyrallis (πυραλλίς), pyragones) is a mythological insect-sized dragon from Cyprus.

`Pyrallis` is a simple library, derived from `simple-parsing`, for automagically creating project configuration from a dataclass.


<p align="center"><img src="https://github.com/eladrich/pyrallis/blob/master/docs/argparse2pyrallis.gif" alt="GIF" width="100%" /></p>

## Why `pyrallis`?

With `pyrallis` your configuration is linked directly to your pre-defined `dataclass`, allowing you to easily create different configuration structures, including nested ones, using an object-oriented design. The parsed arguments are used to initialize your `dataclass`, giving you the typing hints and automatic code completion of a full `dataclass` object.



## Getting to Know `pyrallis` in 5 Simple Steps 🐲

The best way to understand `pyrallis` is through examples, let's get started!

###  :dragon: 1/5 `pyrallis.ArgumentParser` for `dataclass` Parsing :dragon:

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



### :dragon: 2/5 The `pyrallis.wrap` Decorator :dragon:
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


### :dragon: 3/5 Better Configs Using Inherent `dataclass` Features :dragon:
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


### :dragon: 4/5 Building Hierarchical Configurations :dragon:
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

### :dragon: 5/5 Easy Serialization with `pyrallis.dump` :dragon:
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
pyrallis.encode.register(np.ndarray, lambda x: str(list(x)))

# Or with the wrapper version instead 
@pyrallis.encode.register
def encode_array(arr : np.ndarray) -> str:
    return str(list(arr))
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

If `pyrallis` isn't what you're looking for we strongly advise you to give `hydra` and `simpleParsing` a try (where other interesting option include `click`, `ext_argpase`, `jsonargparse`, `datargs` and `tap`). If you do :heart: `pyrallis` then welcome aboard! We're gonna have a great journey together! :speedboat: :dragon_face:

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
- [x] Add support for datetime
> Looks like it already works for the yaml file, json has a recursion, might not be work getting into
- [x] Understand who need serialization
> Every subclass!
- [x] See how encoding works for complex objects
> Things can be simply added to the helpers.encoding file using @singledispatch, example:
 ```python
import numpy as np
@encode.register(np.ndarray)
def encode_ndarray(obj: np.ndarray) -> str:
    return str(obj.tolist())
```
- [x] understand how decoding works
> register_decoding_fn(np.ndarray,np.asarray)
- [x] Understand why encoding is with decorators and encoding is with register
> Doesn't seem like there is a good reason
- [x] Investigate the simple-parsing field
> Allow for specific mapping, was removed
```python
exp_int: int = rallis_field(default=3, decoding_fn=lambda x: int(x) ** 2,
encoding_fn=lambda x: 'Elad says: {}'.format(x))
```
> Remove this feature, we are going for a simple config. Special mapping is a rare usecase
- [x] Make decoding work also for argparse
> Getting there, now using the functions
- [x] See how add new objects outside of encoding.py/decoding.py file
> Works when using a factory
- [x] Allow loading config_file as an argument
- [x] Add an hydra-like @decorator
- [x] Decide if the default should be json or yaml
> Probably YAML, does look better and the same choice as Hydra and OmegaConf. Also `yaml.safe_load` looks stronger. For example, yaml.safe_load('False') works while json.loads('False') fails. ('false') works for both 
> Jsonnet is interesting, but I don't think I need the extra features, can get them from the dataclass
- [x] See how to support lists and dicts. Dict[string,int] for example.
> Supported in yaml! Stay with that format!
- [x] See if can work without serialization object. Understand what get registered
> Done, the following now works

```python
d = yaml.full_load(open('examples_more/serialization/config.yaml','r'))
cfg = decoding.decode(TrainConfig, d)
d_back = encoding.encode(cfg)
```
- [x] We don't want to be too dependent on command line vs file, should always read string and parse using the same logic. Merge logic into a single one.
> Done! Make sure didnt miss anything
- [x] Use yaml.safe_load to make sure logic is the same
- [x] Make autocomplete work
> Tested `argcomplete` and `shtab` didn't function properly
- [x] Think whether registration is the right design for collections, or whether they can just stay in the current design
> This is problematic, as a dictionary won't work for decoding, logic is more complicated.
> Some types need other logic, which is fine. External types can be registered now
- [x] singledispatch syntax, allow both directions?
```python
@encoding.encode.register(PathLike)
def encode_path(obj: PathLike) -> str:
    return obj.__fspath__()

encoding.register(np.ndarray, lambda x: x.__fspath__())
```
- [x] Use a factory for encoding/decoding
> The core code shouldn't change, it it written well and solves the problem. Use the factory only to replace the list of functions. Think if there should be a single factory
> Solved using singledispatch
- [x] Remove pyrallis_field
> It's a cool idea, but could be confusing
- [x] Check enum support
> Added
- [x] Think whether should keep the special case for enum in argparse
> Only affects the error message, probably will remove to make sure I'm using the same interface. Removed!
- [x] Update examples in readme
> Need to show `pyrallis.wrap`, `pyrallis.dump`, `pyrallis.ArgumentParser` and option for config_files. Also show how to use `pyrallis.encode` and `pyrallis.decode` as well as register new types
- [x] Simplify code
- [x] Add cycle loss test
- [x] Rename `parsed_class`
- [ ] Save constants such as CONFIG in a matching location
- [x] Improve comparison section
> Currently removed
- [x] Simplify wrappers class?
> Wrappers are built with complex functionality, probably can be simplified
- [x] Think is --is_flag should work, right now an explicit value is required
> Got it to work, decided it is too confusing
- [x] Remove `eval_if_string` from `decoding`
- [x] Get tests to work
> Probably should keep changing things only after tests are working!
- [x] Add tests from yaml
- [x] Improve syntax for mutable types
> An extension of field with is_mutable
- [x] Change how config is loaded
- [ ] Create documentation?
> Maybe just as a section here, not too many things to doc
- [ ] Add a Design Choices section
> For example, yaml is used to parse all stuff
- [ ] Explain the is_mutable option somewhere
- [ ] Improve warnings and logs
> UserWarning is confusing, shows the code and not only the warning, plus I still have some prints instead of warnings
> /mnt/c/Users/eladr/PycharmProjects/pyrallis/pyrallis/parsing.py:183: UserWarning: Overriding default examples/tmp.yaml with examples/tmp_2.yaml
  UserWarning(f'Overriding default {config_path} with {new_config_path}')
- [ ] Think on relative paths
- [ ] Add datetime support as an example
- [ ] Understand the need for metavars
> Kind of got it, looks like it is used for naming
