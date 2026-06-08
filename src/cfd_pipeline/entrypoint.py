#!/usr/bin/env python3

from typing import Union, overload


def main() -> None:
    """Entrypoint for example project."""
    print("Hello World")


# Demonstrate typing
@overload
def to_test(x: int) -> int:
    pass


@overload
def to_test(x: float) -> float:
    pass


def to_test(x: Union[float, int]) -> Union[float, int]:
    """
    Add 1 to the passed parameter.

    This is an example function with a longer docstring to demonstrate style and as a
    function to test with pytest.

    :param x: numeric to add one to
    :return: the input plus one
    """
    return x + 1


if __name__ == "__main__":
    main()
