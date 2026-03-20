from __future__ import annotations

import pandas as pd
import re
import logging
from typing import Literal, List

import re


_COLUMN_PATTERN = r"[^\W\d]+"
_OPERATOR_PATTERN = r"[\+\-\*]"
_ALLOWED_WHITESPACES = r"\s"

_column_pattern_compiled = re.compile(_COLUMN_PATTERN)
_operator_pattern_compiled = re.compile(_OPERATOR_PATTERN)
_full_pattern = re.compile(rf"({_COLUMN_PATTERN}|{_OPERATOR_PATTERN}|{_ALLOWED_WHITESPACES})")


def add_virtual_column(df: pd.DataFrame, role: str, new_column: str) -> pd.DataFrame:
    try:
        virtual_column = _get_virtual_column(df, role)
        result = df.copy()
        result[new_column] = virtual_column
        return result
    except RoleFormatError as e:
        logging.warning(e)
        return pd.DataFrame()


def _get_virtual_column(df: pd.DataFrame, role: str) -> pd.Series:
    tokens = _tokenize_role(role)

    # A new list of tokens, with column names substituted 
    # with DataFrame queries and whitespace tokens removed.

    # Example: x * y + z ===> df["x"] * df["y"] + df["z"]
    transformed_tokens = [] 

    def get_role_with_token_highlighted(token_index: int):
        idx = token_index
        return "".join(tokens[:idx]) + f">>>{tokens[idx]}<<<" + "".join(tokens[idx + 1:])

    column_expected = True
    operator_expected = False
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
            transformed_tokens.append(f"df[\"{token}\"]")
            column_expected = False
            operator_expected = True

        elif _is_operator(token):
            if not operator_expected:
                raise RoleFormatError(
                    "Parameter \"role\" value is not valid. Expression may not start with an operator,"
                    + " nor can it contain multiple operators in a row. "
                    + "\n\nFor example, the following expressions are invalid for \"role\":"
                    + "\n\t+ col_1 + col_2"
                    + "\n\tcol_1 + + col_2"
                    + f"\n\nProblematic part:\n\t{get_role_with_token_highlighted(idx)}"
                )
            transformed_tokens.append(token)
            column_expected = True
            operator_expected = False

    # Join transformed tokens together into python code and evaluate to get resulting pd.Series
    return eval("".join(transformed_tokens))


def _tokenize_role(role: str) -> List[str]:
    tokens = _full_pattern.findall(role)

    characters_matched = "".join(tokens)
    has_invalid_characters = len(characters_matched) != len(role) 
    if has_invalid_characters:
        raise RoleFormatError("Parameter \"role\" contains invalid characters.")
    return tokens


def _is_column(token: str) -> bool:
    return _column_pattern_compiled.fullmatch(token) != None


def _is_operator(token: str) -> bool:
    return _operator_pattern_compiled.fullmatch(token) != None


class RoleFormatError(RuntimeError):
    pass


