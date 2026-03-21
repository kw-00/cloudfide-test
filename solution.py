from __future__ import annotations

import pandas as pd
import re
import logging
from typing import List

_COLUMN_PATTERN = r"[^\W\d]+"
_OPERATOR_PATTERN = r"[\+\-\*]"
_ALLOWED_WHITESPACES = r"\s"

_column_pattern_compiled = re.compile(rf"^{_COLUMN_PATTERN}$")
_full_role_pattern = re.compile(rf"^(?:{_COLUMN_PATTERN}|{_OPERATOR_PATTERN}|{_ALLOWED_WHITESPACES})+$")
_tokenizing_pattern = re.compile(rf"{_COLUMN_PATTERN}|{_OPERATOR_PATTERN}")

def add_virtual_column(df: pd.DataFrame, role: str, new_column: str, enable_warnings: bool = False) -> pd.DataFrame:
    """
    Adds a new column to a `DataFrame` based on an expression called `role`. The new column's values are calculated
    based on other columns, using the aforementioned *role expression*. That new column will further be referred to as
    the virtual column.

    If `role` is invalid or `df` does not contain a column specified in `role`, an empty `DataFrame` is returned.
    Furthermore, a warning may be printed out if warnings are enabled (check the `enable_warnings` parameter).
            
    For example:

        >>>add_virtual_column(df=df, role="col_1 * col_2", new_column="VirtualColumn")


    will throw KeyError if `df` does not have a column named "col_1" or "col_2".

    Args:
        df (pd.DataFrame): The input DataFrame to which the virtual column will be added.
        role (str): The expression used to calculate the new column.

            The format is as follows:
            <column_name> { <whitespace> } (<operator> { <whitespace> } <column_name>)+


            Where:
            * column_name can consist only of letters and underscores,
            * valid operators are +, -, *.

        new_column (str): The name of the virtual column. Must consist only of letters and underscores.
        enable_warnings (bool): Whether to log warnings when `role` is invalid or columns in `role` do not exist on `df`.
            Defaults to `False`.

    Returns:
        pd.DataFrame: A new DataFrame containing the original columns plus the virtual column.


    Examples:
        >>> df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        >>> add_virtual_column(df, role='sum', new_column='C')
           A  B  C
        0  1  3  4
        1  2  4  6
    """
    try:
        if not _is_column(new_column):
            raise ValueError(
                f"Value of \"{new_column}\" is invalid for parameter \"column_name\"."
                + " Column name should consist solely of letters and underscores."
            )
        virtual_column = _get_virtual_column(df, role)
        result = df.copy()
        result[new_column] = virtual_column
        return result
    except (ValueError, RoleFormatError, KeyError) as e:
        if enable_warnings:
            logging.warning(e)
        return pd.DataFrame()


def _get_virtual_column(df: pd.DataFrame, role: str) -> pd.Series:
    if _role_has_invalid_characters(role):
        raise RoleFormatError("Parameter \"role\" contains invalid characters.")
    tokens = _tokenize_role(role)
    _validate_syntax_and_check_columns(df, tokens)
    return df.eval("".join(tokens)) # type: ignore


def _role_has_invalid_characters(role: str) -> bool:
    """Returns True when *role expression* has invalid characters, False otherwise."""

    return _full_role_pattern.fullmatch(role) is None


def _tokenize_role(role: str) -> List[str]:
    """
    Turns a *role expression* into tokens, ignoring whitespaces.
    Role parameter should not contain invalid characters.
    """

    tokens = _tokenizing_pattern.findall(role)
    return tokens


def _validate_syntax_and_check_columns(df: pd.DataFrame, tokens: List[str]) -> None:
    """
    Accepts a tokenized *role expression* and verifies its syntax.
    Throws `RoleFormatError` if syntax is invalid and `KeyError` if any of the columns
    featured in the role expression does not exist on `df`.
    
    """

    def get_role_with_token_highlighted(token_index: int):
        idx = token_index
        before = " ".join(tokens[:idx])
        after = " ".join(tokens[idx + 1:])
        return before + f">>>{tokens[idx]}<<<" + after

    column_expected = True
    for idx, token in enumerate(tokens):
        if _is_column(token):
            if not column_expected:
                raise RoleFormatError(
                    "Parameter \"role\" value is not valid. Column names may only contain letters"
                    + " and underscores and must be separated with an operator, e.g. col_1 * col_2."
                    + "\n\nFor example, the following expressions are invalid for \"role\":"
                    + "\n\tcol_1 col_2 + col_3"
                    + "\n\tcol_& + col_2"
                    + f"\n\nProblematic part:\n\t{get_role_with_token_highlighted(idx)}"
                )
            column_expected = False
            if token not in df.columns:
                raise KeyError(f"DataFrame does not contain a column named \"{token}\"")
        # If token is not column, it must be operator
        else:
            if column_expected:
                raise RoleFormatError(
                    "Parameter \"role\" value is not valid. Expression may not start with an operator,"
                    + " nor can it contain multiple operators in a row. "
                    + "\n\nFor example, the following expressions are invalid for \"role\":"
                    + "\n\t+ col_1 + col_2"
                    + "\n\tcol_1 + + col_2"
                    + f"\n\nProblematic part:\n\t{get_role_with_token_highlighted(idx)}"
                )
            column_expected = True


def _is_column(token: str) -> bool:
    return _column_pattern_compiled.fullmatch(token) is not None


class RoleFormatError(RuntimeError):
    pass