import pandas as pd

from solution import add_virtual_column

allowed_operators = ["+", "-", "*"]
standard_column_names = ["_column_", "x", "y", "z"]
unicode_column_names = ["ą", "ß", "Ж", "你", "あ"]

DEFAULT_NEW_COLUMN_NAME = "new_column"

df = pd.DataFrame()

for i, uni_col in enumerate(standard_column_names + unicode_column_names):
    df[uni_col] = [i] * 100

# HELPER FUNCTIONS =======================================
def assert_new_column_created(new_df: pd.DataFrame):
    old_column_count = df.shape[1]
    new_column_count = new_df.shape[1]
    assert old_column_count + 1 == new_column_count, (
        "Result column count should be equal to original"
        + f" df column count plus 1. Expected: {new_column_count + 1}. Got: {old_column_count}."
    )


def assert_empty_df(new_df: pd.DataFrame):
    assert new_df.shape == (0, 0), f"Resulting DataFrame should be empty. Expected shape {(0, 0)}, got {new_df.shape}"


# TESTS ====================================================
def test_unicode_columns():
    role = "*".join(unicode_column_names)
    new_df = add_virtual_column(df, role, DEFAULT_NEW_COLUMN_NAME)
    assert_new_column_created(new_df)


def test_no_operators():
    role = "x"
    new_df = add_virtual_column(df, role, DEFAULT_NEW_COLUMN_NAME)
    assert_new_column_created(new_df)


def test_unseparated_columns_and_numbers():
    for role in ("x y", "x 1", "1 x", "1 1"):
        new_df = add_virtual_column(df, role, DEFAULT_NEW_COLUMN_NAME)
        assert_empty_df(new_df)


def test_trailing_operators():
    for operator in allowed_operators:
        for i in range(1, 10):
            role = operator * i
            new_df = add_virtual_column(df, role, DEFAULT_NEW_COLUMN_NAME)
            assert_empty_df(new_df)


def test_invalid_operator_use():
    for operators in ("* *", "+ *", "- *"):
        role = f"x {operators} y"
        new_df = add_virtual_column(df, role, DEFAULT_NEW_COLUMN_NAME)
        assert_empty_df(new_df)
        role = role.replace(" ", "")
        new_df = add_virtual_column(df, role, DEFAULT_NEW_COLUMN_NAME)
        assert_empty_df(new_df)


