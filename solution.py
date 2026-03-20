from __future__ import annotations

import pandas as pd
import re
import logging
from typing import List

_COLUMN_PATTERN = r"[^\W\d]+"
_OPERATOR_PATTERN = r"[\+\-\*]"
_ALLOWED_WHITESPACES = r"\s"

_column_pattern_compiled = re.compile(_COLUMN_PATTERN)
_full_pattern = re.compile(rf"{_COLUMN_PATTERN}|{_OPERATOR_PATTERN}|{_ALLOWED_WHITESPACES}")
_no_whitespaces_pattern = re.compile(rf"({_COLUMN_PATTERN}|{_OPERATOR_PATTERN})")

def add_virtual_column(df: pd.DataFrame, role: str, new_column: str, enable_warnings: bool = False) -> pd.DataFrame:
    """
    Adds a new column to a `DataFrame` based on an expression. The new column's values are calculated
    based on other columns, using the aforementioned expression. That new column will further be referred to as
    the virtual column.

    If `role` is invalid or `df` does not contain a column specified in `role`, an empty `DataFrame` is returned.
    Furthermore, an error is logged, unless
            
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

        new_column (str): The name of the virtual column.

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
        virtual_column = _get_virtual_column(df, role)
        result = df.copy()
        result[new_column] = virtual_column
        return result
    except (RoleFormatError, KeyError) as e:
        if enable_warnings:
            logging.warning(e)
        return pd.DataFrame()


def _get_virtual_column(df: pd.DataFrame, role: str) -> pd.Series:
    tokens = _tokenize_role(role)
    _verify_token_sequence(df, tokens)
    return df.eval("".join(tokens)) # type: ignore


def _tokenize_role(role: str) -> List[str]:
    if _role_has_invalid_characters(role):
        raise RoleFormatError("Parameter \"role\" contains invalid characters.")

    tokens = _no_whitespaces_pattern.findall(role)
    return tokens


def _role_has_invalid_characters(role: str) -> bool:
    tokens = _full_pattern.findall(role)
    characters_matched = "".join(tokens)
    has_invalid_characters = len(characters_matched) != len(role) 
    return has_invalid_characters


def _verify_token_sequence(df: pd.DataFrame, tokens: List[str]):
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
    return _column_pattern_compiled.fullmatch(token) != None


class RoleFormatError(RuntimeError):
    pass