# The pyrallis API

Pyrallis is designed to have a relatively small API, you can get familiar with it below 📚

## Parsing Interface
### pyrallis.parse
```python
def parse(config_class: Type[T], 
          config_path: Optional[Union[Path, str]] = None,
          args: Optional[Sequence[str]] = None) -> T:
```
Parses the available arguments and return an initialized dataclass of type `config_class`.

Each dataclass attribute is mapped to a matching argparse argument, where nested arguments are concatenated with the dot notation. That is, if `config_class` contains a `config_class.compute.workers` attribute, the matching argparse argument will simply be `--compute.workers=42`. The full set of arguments is visible using the `--help` command.

Pyrallis also searches for an optional `yaml` configuration file defined either with the default `config_path` parameter, or specified from command-line using the dedicated `--config_path` argument. The configuration file is mapped according to the `yaml` hierarchy.
That is, if `config_class` contains a `config_class.compute.workers` attribute, the matching `yaml` argument would be
```yaml
compute:
  workers: 42
```

The overloading mechanism is defined so that default values can be overridden by `yaml` values which can be overridden by command-line arguments. The actual dataclass is initialized only once using the final set of arguments.

> Parameters

* **config_class (A dataclass class)** - The dataclass that will define the parser
* **config_path (str)** - An optional path to a default `yaml` configuration file. The parser will first load the arguments from there and will override them with command-line arguments.
* **args** - The arguments to parse, as in the `argparse.ArgumentParser.parse_args()` call. If None, parses from command-line


> Returns

An initialized dataclass of type `config_class`.

> Example:

A small working example would look like that
```python title="train_model.py"  linenums="1"
from dataclasses import dataclass
import pyrallis

@dataclass
class TrainConfig:
    """ Training config for Machine Learning """
    workers: int = 8 # The number of workers for training
    exp_name: str = 'default_exp' # The experiment name

def main():
    cfg = pyrallis.parse(config_class=TrainConfig)
    print(f'Training {cfg.exp_name} with {cfg.workers} workers...')
```
The arguments can then be specified using command-line arguments, a `yaml` configuration file, or both

```console
$ python train_model.py --config_path=some_config.yaml --exp_name=my_first_exp
Training my_first_exp with 42 workers...
```
Not sure what arguments are available? pyrallis also automagically generates the `--help` command 🪄
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

### pyrallis.wrap
```python
def wrap(config_path=None)
```
Inspired by Hydra, Pyrallis also offers an alternative decorator that wraps your main function and automatically initializes a configuration class to match your function signature.

> Parameters

* **config_path (str)** - An optional path to a default `yaml` configuration file. The parser will first load the arguments from there and will override them with command-line arguments.

> Returns

A wrapped function, where the first argument is implicitly initialized with pyrallis.

> Example
=== "@pyrallis.wrap"

    ``` python
    @pyrallis.wrap()
    def main(cfg: TrainConfig):
        print(f'Training {cfg.exp_name} with {cfg.workers} workers...')

    if __name__ == '__main__':
        main() # Notice that cfg is not explicitly passed to main!
    ```

=== "pyrallis.parse"

    ``` python
    def main():
        cfg = pyrallis.parse(config_class=TrainConfig)
        print(f'Training {cfg.exp_name} with {cfg.workers} workers...')

    if __name__ == '__main__':
        main()
    ```

## Types and Registration

### pyrallis.decode
```python
def decode(t: Type[T], raw_value: Any) -> T:
```
Parse a given raw value and produce the corresponding type. This function can parse any of the supported pyrallis types, from standard types to enums and dataclasses.


> Parameters

* **t (Type[T])** - The type to parse into
* **raw_value** - The input to parse

> Returns

A value of type `T` constructed from `raw_value`


> Examples:

Pyrallis can decode a variety of different types

```python
pyrallis.decode(float, '0.7') # Output: 0.7

pyrallis.decode(typing.List[int],['6','3','4']) # Output: [6, 3, 4]

pyrallis.decode(typing.Union[str, float],'2.3') # Output: '2.3'
```

The `pyrallis.decode` function is also used to parse dataclasses from dictionaires.
The dictionary is assumed to have a structure that matches the dataclass, with possibly missing values. 
For example, assuming the following dataclass
```python
@dataclass
class ComputeConfig:
    """ Config for training resources """
    # The number of workers for training
    workers: int = field(default=8)
    # The number of workers for training
    eval_workers: Optional[int] = field(default=None)

@dataclass
class TrainConfig:
    compute: ComputeConfig = field(default_factory=ComputeConfig)
```

A valid dictionary can be
```python
{
    'compute':
     {
         'workers': '6',
         'eval_workers': '16'
     }
}
```

Where `#!python pyrallis.decode(TrainConfig, d)` will generate the matching dataclass. The values will be fed into the dataclass constructor. Values can be missing if they have a default value, otherwise pyrallis will just fail to construct the class.



#### pyrallis.decode.register

```python
def register(cls, func, include_subclasses=False)
```
Pyrallis can decode many different types, but there's still a chance you might want to a type that isn't already built-in into pyrallis. This can be easily done using the register mechanism.

??? "The @withregistry wrapper"

    The register method is a result of using the @withregistry wrapper over the pyrallis.decode function, a variant for pyrallis of the @singledispatch that only creates a registry and does not override the default entrypoint.


> Parameters

* **cls** - The type to register
* **func** - The decoding function to register
* **include_subclasses** - Whether to also register the function for the `cls` subclasses. If True, `func` will also expect the type parameter.

> Returns

Registers the function, no return value.

> Examples:

Say we want to add an option to decode a numpy array into pyrallis.

```python
import numpy as np
import pyrallis

pyrallis.decode.register(np.ndarray,np.asarray)
```

The register function can also be used as a wrapper
```python
@pyrallis.decode.register(np.ndarray)
def decode_array(x):
    return np.asarray(x)
```

For inherited types one can either register it directly, or register a parent class
```python
pyrallis.decode.register(SomeClass, lambda x: SomeClass(x))
# or
pyrallis.decode.register(BaseClass, lambda t, x: t(x), include_subclasses=True)
```
Where `t` would be some subclass of `BaseClass`.

### pyrallis.encode
```python
def encode(obj: Any) -> Any:
```
Parse a given object into a yaml compatible object that can be serialized.  


> Parameters

* **obj** - The object to encode

> Returns

A yaml-compatible object. For dataclasses, a matching dictionary will be generated


> Examples:

For many types the encode function will simply return the same object, as they are already yaml-compatible.

```python
pyrallis.encode(0.7) # Output: 0.7

pyrallis.encode(['6','3','4']) # Output: ['6','3','4']

pyrallis.encode((0.2, 0.3)) # Output: [0.2, 0.3]
```

Most of the logic in `pyrallis.encode` is related to encoding of dataclasses. A given dataclass will be encoded to a dictionary representing the same hierarchy and values. 
For example, assuming the following dataclass and its instance
```python

@dataclass
class ComputeConfig:
    """ Config for training resources """
    # The number of workers for training
    workers: int = field(default=8)
    # The number of workers for training
    eval_workers: Optional[int] = field(default=None)

@dataclass
class TrainConfig:
    compute: ComputeConfig = field(default_factory=ComputeConfig)

cfg = TrainConfig(compute=ComputeConfig(workers=2, eval_workers=8))
```

The output of `pyrallis.encode(cfg)` would be
```python
{
    'compute':
     {
         'workers': '2',
         'eval_workers': '8'
     }
}
```

#### pyrallis.encode.register

```python
def register(cls, func)
```
If an object you want to encode is not serializable, you can easily register a function that encodes it into a supported type using the `register` mechanism.

??? "The @singledispatch wrapper"

    The register method is a result of using the @singledispatch wrapper over the pyrallis.encode function, allowing to override it with new encoders.


> Parameters

* **cls** - The type to register
* **func** - The decoding function to register

> Returns

Registers the function, no return value.

> Examples:

Say we want to add an option to encode a numpy array into pyrallis.

```python
import numpy as np
import pyrallis

pyrallis.encode.register(np.ndarray, lambda x: x.tolist())
```

The register function can also be used as a wrapper
```python
@pyrallis.encode.register(np.ndarray)
def encode_array(x):
    return x.tolist()
```

### Supported Types
pyrallis comes with many supported types, as detailed below. Additional types can be added using the `pyrallis.decode.register` and `pyrallis.encode.register` functionality.

#### Standard Types

`str` 

`float`

`int`

`bool`

`bytes`

For each standard type values are converted to the type using the type as constructor (i.e., `#!python float('1.3')`)

#### Collection Types

`tuple`  (or `typing.Tuple`)

`list`  (or `typing.List`)

`dict` (or `typing.Dict`)

`set`  (or `typing.Set`)

When using the collection definition from `typing` the inner types will also be checked recursively. For example, one can define a `#!python typing.Tuple[int,float,typing.List[int]]` type and the conversion will be done accordingly.

Reading sequences and dictionaries is done using the `yaml` syntax. Notice that tuples and sets use the same syntax as lists, where the conversion happens after loading the arguments. For dictionaries, the keys must be space seperated so the entire dictionary should be wrapped in string quotation marks.

```console
$ python train_model.py --worker_inds=[2,18,42] --worker_names="{2: 'George', 18: 'Ben'}"
```

#### Typing Types

`typing.Any`

for `typing.Any` no explicit conversion is applied, this means only the base conversion done when loading a yaml file/string is applied.

`typing.Optional`

Using `typing.Optional` you can pass `None` values to an argument. Following the `yaml` syntax this is specified using the `null` keyword.

```console
$ python train_model.py --worker_names=null
```

`typing.Union`

For unions `pyrallis` sequentially tries to apply conversion to each type and sticks with the first one that works. This means there could be cases where the order of values in the Union affects the end result (i.e. `#!python typing.Union[int, float]`).




#### Other Types

`Enum`

Enums can be really useful for configurations, `pyrallis` inherently supports the `enum.Enum` class and parses enums using the matching keyword values.

`pathlib.Path`

The `pathlib.Path` type is useful for path manipulation, and hence a useful type for our configuration dataclasses. `pyrallis` inherently supports the class and can convert an `str` to `Path` and back, according to the type hints.

`dataclasses`
`Dataclasses` are also supported by `pyrallis.decode` and `pyrallis.encode`. In fact, this is how pyrallis operates behind the scenes.

## Working with Files

### pyrallis.dump
```python
def dump(config: Dataclass, stream=None, omit_defaults: bool = False, **kwargs)
```
Serialize a configuration dataclass into a file stream. If stream is None, return the produced string instead. Additional arguments are passed along to the `dump` function of the current configuration format.
In practice this function uses pyrallis.encode to create a standard dictionary from the dataclass which is then passed along to the configuration parser.

> Parameters

* **config (dataclass)** - The dataclass to serialize
* **omit_defaults** - If true, does not dump values that are equal to the default Dataclass values.
* **stream** - An output stream to dump into. If None, the produced string is returned.


> Returns

If no stream is provided, returns the produced string. Otherwise, no return value.

> Example:

```python
@pyrallis.wrap()
def main(cfg: TrainConfig):
    print('The generated config is:')
    print(pyrallis.dump(cfg))
    # Saving to file
    pyrallis.dump(cfg, open('/configs/train_config.yaml','w'))
```


### pyrallis.load
```python
def load(t: Type[Dataclass], stream):
```
Parse the document from the stream and produce the corresponding dataclass
In practice this function first loads a dictionary from the stream and then uses `pyrallis.decode` to generate a valid dataclass from it.

> Parameters

* **t (Type[dataclass])** - The dataclass type to load into
* **stream** - The input stream to load


> Returns

A dataclass instance from type `t`.

> Example:

```python
cfg = pyrallis.load(TrainConfig, open('/configs/train_config.yaml','r'))
print('Loaded config has {cfg.workers} workers')
```

### pyrallis.set_config_type
```python
def set_config_type(type_val: Union[ConfigType, str])
```
By default, pyrallis uses `yaml` for parsing string and files and this is its recommended format. However, pyrallis also supports `json` and `toml`. When using `pyrallis.set_config_type` the global context of pyrallis will change so that the matching configuration format will be used for  `pyrallis.parse`, `pyrallis.dump` and `pyrallis.load`.

To change the configuration type for a specific context use the  `with` context

```python
with pyrallis.config_type('json'):
    pyrallis.dump(cfg)
```

!!! info

    Note that the `pyrallis.parse` function is also dependent on the configuration format as strings from cmd are first parsed based on the current configuration format. This ensures a unified behavior when parsing from files and cmd arguments.

> Parameters

* **type_val** - A string representing the desired format (`#!python "json", "yaml", "toml"`) or the matching enum value (`#!python pyrallis.ConfigType.YAML`)


> Example

```python
import pyrallis
pyrallis.set_config_type('json')

@dataclass
class TrainConfig:
    """ Training config for Machine Learning """
    workers: int = 8 # The number of workers for training
    exp_name: str = 'default_exp' # The experiment name

@pyrallis.wrap()
def main(cfg: TrainConfig):
    pyrallis.dump(cfg)
    
    with pyrallis.config_type('yaml'):
        pyrallis.dump(cfg)
```

## Helper Functions
### pyrallis.field

```python
def field(*, default=dataclasses.MISSING, default_factory=dataclasses.MISSING, init=True, repr=True,
          hash=None, compare=True, metadata=None, is_mutable=False)
```

Extends the standard dataclass.field with an additional `is_mutable` flag. If this flag is set to `True` the default value is considered as mutable and a matching default_factory is generated instead.

> Parameters

All the standard dataclasses.field parameters with the additional

* **is_mutable** - Whether the specified default value is mutable

> Returns

An object to identify dataclass fields, same as in dataclasses.field

> Example

say we try to code the following dataclass
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
Kind of annoying and could be confusing for a new guest reading your code :confused:. This is where `pyrallis.field` can be helpful
```python
from pyrallis import field
worker_inds: List[int] = field(default=[1,2,3], is_mutable=True)
```
The `pyrallis.field` behaves like the regular `dataclasses.field` with an additional `is_mutable` flag. When toggled, the `default_factory` is created automatically, offering the same functionally with a more reader-friendly syntax.

