from __future__ import annotations

import pandas as pd
import re
import logging
from typing import List

_NON_NEGATIVE_NUMBER_PATTERN_STRING = r"(?:[1-9]\d*|0)(?:\.\d*)?|\.\d+"

_PREDEFINED_GROUPS = {
    "column": r"[^\W\d]+",
    "non_negative_number": _NON_NEGATIVE_NUMBER_PATTERN_STRING,
    "operator_blacklist": r"[\*\+\-]\s*\*",
    "operator": r"[\+\-\*]",
    "whitespaces": r"\s+",
    "invalid": r".+?"
}

_COMPLETE_PATTERN_STRING ="|".join([f"(?P<{name}>{pattern})" for name, pattern in _PREDEFINED_GROUPS.items()])
_complete_pattern = re.compile(_COMPLETE_PATTERN_STRING)

_column_pattern = re.compile(f"^{_PREDEFINED_GROUPS['column']}$")

def add_virtual_column(df: pd.DataFrame, role: str, new_column: str, enable_warnings: bool = False) -> pd.DataFrame:
    """
    Adds a new column to a `DataFrame` based on an expression called `role`. The new column's values are calculated
    based on other columns, using the aforementioned *role expression*. That new column will further be referred to as
    the virtual column.

    If *role expression* syntax is invalid or `df` does not contain a column specified in `role`, an empty `DataFrame` is returned.
    Furthermore, a warning may be printed out if warnings are enabled (check the `enable_warnings` parameter).
            
    For example:

        >>>add_virtual_column(df=df, role="radius * 3.1415", new_column="VirtualColumn")


    will show  a warning saying that `df` does not have a column named "radius" as well as
    highlighting the problematic fragment of the *role expression*.

    Args:
        df (pd.DataFrame): The input DataFrame to which the virtual column will be added.
        role (str): The expression used to calculate the new column. This expression must contain a combination
            of operators and column names. Column names must consist entirely of letters and underscores.
            Only "+", "-" and "*" are allowed as operators.

        new_column (str): The name of the virtual column. Must consist only of letters and underscores.
        enable_warnings (bool): Whether to log warnings when `role` is invalid or columns in `role` do not exist on `df`.
            Defaults to `False`.

    Returns:
        pd.DataFrame: A new DataFrame containing the original columns plus the virtual column.


    Examples:
        >>> df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        >>> add_virtual_column(df, role='A + B', new_column='C')
           A  B  C
        0  1  3  4
        1  2  4  6
    """
    try:
        if not _column_pattern.fullmatch(new_column):
            raise ValueError(
                f"Value of \"{new_column}\" is invalid for parameter \"column_name\"."
                + " Column name should consist solely of letters and underscores."
            )
        tokens = _tokenize_and_validate_role(df, role)
        normalized_role = " ".join(tokens)
        new_df = df.copy()
        new_df[new_column] = df.eval(normalized_role)
        return new_df
    except (ValueError, RoleSyntaxError, KeyError) as e:
        if enable_warnings:
            logging.warning(e)
        return pd.DataFrame()


def _tokenize_and_validate_role(df: pd.DataFrame, role: str) -> List[str]:
    if len(role) == 0:
        raise RoleSyntaxError("Role cannot be empty.")
    if len(role.strip()) == 0:
        raise RoleSyntaxError("Role cannot contain only whitespaces.")

    matches = list(_complete_pattern.finditer(role))
    tokens_no_whitespaces = []
 
    number_or_column_not_expected = False
    for idx, match in enumerate(matches):
        for group_name, token in match.groupdict().items():
            if token is not None:
                if group_name == "column":
                    if number_or_column_not_expected:
                        raise RoleSyntaxError(
                            "Invalid role syntax. Numbers and columns need to be separated from other"
                            + " numbers and columns by operators."
                            + f"\n\nProblematic part:\n{_highlight_token(idx, matches)}"
                        )
                    if token not in df.columns:
                        raise KeyError(
                            f"Column \"{token}\" does not exist in DataFrame."
                            + f"\n\nProblematic part:\n{_highlight_token(idx, matches)}"
                        )
                    tokens_no_whitespaces.append(token)
                    
                elif group_name == "non_negative_number":
                    if number_or_column_not_expected:
                        raise RoleSyntaxError(
                            "Invalid role syntax. Numbers and columns need to be separated from other"
                            + " numbers and columns by operators."
                            + f"\n\nProblematic part:\n{_highlight_token(idx, matches)}"
                        )
                    tokens_no_whitespaces.append(token)

                elif group_name == "operator":
                    if idx == len(matches) - 1:
                        raise RoleSyntaxError(
                            "Invalid role syntax. Trailing operators are not allowed."
                            + f"\n\nProblematic part:\n{_highlight_token(idx, matches)}"
                        )
                    tokens_no_whitespaces.append(token)

                elif group_name == "number_blacklist":
                        raise RoleSyntaxError(
                            "Invalid role syntax. Numbers must be separated by operators."
                            + f"\n\nProblematic part:\n{_highlight_token(idx, matches)}"
                        )
                elif group_name == "operator_blacklist":
                    raise RoleSyntaxError(
                        f"Token of \"{token}\" is not recognized as a valid operator use."
                        + f"\n\nProblematic part:\n{_highlight_token(idx, matches)}"
                    )
                elif group_name == "invalid":
                    raise RoleSyntaxError(
                        f"Character \"{token}\" is not allowed."
                        + f"\n\nProblematic part:\n{_highlight_token(idx, matches)}"
                    )
                
                if group_name in ("column", "non_negative_number"):
                    number_or_column_not_expected = True
                elif group_name in ("operator"):
                    number_or_column_not_expected = False

                break
                    
    return tokens_no_whitespaces


def _highlight_token(idx: int, matches: List[re.Match]) -> str:
    tokens = [match.group(0) for match in matches]
    tokens[idx] = f">>>{tokens[idx]}<<<"
    return "".join(tokens)


class RoleSyntaxError(RuntimeError):
    pass