# Contriubting to Diskord
First off, We would like to thank you for showing interest in contributing to this library, it really helps us a lot. :grin:

## What this isn't for.
This issue tracker is not for general code help. For code help and other discussion, Consider
asking in our [discord server](https://dsc.gg/diskord-dev)

## Reporting bugs
One of the core things are bug reports, they help us discover the problems that may cause problem.

Fortunately, we welcome all kind of bug reports in this repository. We use GitHub issues for this purpose.

To submit a bug report, [Open an issue](https://github.com/diskord-dev/diskord/issues/new).

Your bug report must have the following things.

- A brief of the bug (Issue Title)
- A descriptive summary of the bug
- Steps to reproduce, i.e what are the things that you did to discover the bug.
- Simple Reproducible code (If any.)
- Expected Results; What did you expect to happen?
- Actual Results; What exactly happened?
- System information
    - Intents (`diskord.Intents`)
    - Your Python Version (`python -v`)
    - The library version (`python -m diskord --version`)
    - The OS you are on.

The fields above may not be exact same, You will be given a sample template which would have to be filled.

## Suggesting features
We also love the feature requests, Thankfully, the process of submitting a feature request is straightforward. Courtesy to GitHub issues.

To submit a feature request, [Open an issue](https://github.com/diskord-dev/diskord/issues/new).

Your feature request should have:

- The feature title
- The feature description
- Benefits of feature, How will it help? What problem does it solve?
- Current Solution (if any)
- Ideal Solution (if any)
- Some additional context (if any)


The fields above may not be exact same, You will be given a sample template which would have to be filled.


----

**Before submitting bug reports or feature requests, Please check the open issues first to find any duplicates.**

## Contributing Directly
We live in the world of open source where you are free to contribute to one's software, That's the case with this library.

We appreciate all the contributions, from minor to major.

To ensure the best quality, there are some points that must be noted before opening a pull request.

### Consistency
This library relvoves around the concept of consistency. We have an API that is focused to be as consistent to be possible.

Let's have an example of this code:

```py
def get_foo(id):
    return foo_list[id]

def getBar(barId):
    return barList[barId]
```
in the above code, we can clearly see a major inconsistency; The naming.

In comparison, We have consistent code:
```py
def get_foo(id):
    return foo_list[id]

def get_bar(id):
    return bar_list[id]
```
This is much more consistent as it follows same naming conventions in the function names.

This was a pretty simple example but can lead to many confusions that's why we encourage the pull requests to be consistent with the rest of the API.

----

- Use only underscore case `get_foo` is valid but `getFoo` is not.
- Follow PEP-8 conventions.
- Follow the docstring format (Library uses Sphinx for documentation) i.e
- Major changes must be tested locally.
```py
def get_cake(id: int) -> Cake:
    """Gets a cake.

    :param id: The ID of the cake.
    :type id: :class:`int`

    :returns: The resolved cake.
    :rtype: :class:`Cake`

    :raises CakeNotFound: The cake not found.
    """
    ...
```

### Deprecation & Removal

Any feature that is intended to be removed sometime in the future must undergo a "deprecation period" to give the users time to migrate to alternatives.

Internally, the library provides `utils.deprecated` to decorate methods that are deprecated and will be removed in near future. You might also add `.. versiondeprecated::` in the docstring

```py
from . import utils

@utils.deprecated(instead='get_bar')
def get_foo():
    """Gets foo.

    .. versiondeprecated:: 1.0
    """
```
The `get_foo` function would work as usual but would result in a warning when called.
```py
>>> diskord.get_foo()
DeprecationWarning: get_foo has been deprecated, Use get_bar instead.

# normal function working here...
```
The function will be removed after the deprecation period is over. A deprecation period's length depends on the how breaking the change is. Major breaking changes have large deprecation periods.

There're few exceptions in this process; Deprecation process may be omitted in a major version release and few other exceptions.

## Pro tips
These aren't hard rules but just some guidelines.

- Use present tense in commit messages.
    - :x: `Fixed x in y`
    - :green_circle: `Fix x in y`
- Have short yet descriptive commit messages.
    - :x: `Fix a bug`
    - :green_circle: `Fix foo being None`

----
