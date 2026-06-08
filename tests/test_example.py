from example_project import to_test

# or
# from example_project.entrypoint import to_test


def test_example() -> None:
    """Test the example function to_test."""
    assert to_test(1) == 2
    assert to_test(1) != 3
