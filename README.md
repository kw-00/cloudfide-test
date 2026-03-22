### Implementation: [solution.py](./solution.py)


**Note:** I used *Python 3.11* while working on this project, but I would expect it to work on versions 3.10 and later.

## About the solution
The only dependency apart from standard Python libraries is the *Pandas* library.

The function's contract looks like this:
```python
def add_virtual_column(
    df: pd.DataFrame, 
    role: str, new_column: str, 
    enable_warnings: bool = False
) -> pd.DataFrame:
```
I added an optional `enable_warnings` parameter. When set to `True`, the function prints out appropriate warnings in event when something goes wrong. These warnings explain what happened and also show which part of `role` is the problem. Useful for debugging. `False` is default, as I wanted to adhere to the instructions as closely as possible.

### Function workflow
My implementation works as follows:
1. Use a single regular expression to split `role` into tokens and classify each token (columns, operators, etc.).
1. Validate syntax by analyzing the tokens. 
1. Use `df.eval(...)` to create a `Series` based on `role`.
1. Return a copy of `df` with the newly created `Series` added as a column.

### Extensible behaviour
The code is efficient and easy to extend or modify. Right at the beginning of the module, there is a dictionary that defines how
each token type is matched. Here it is in its current form:

```python
_PREDEFINED_GROUPS = {
    "column": r"[^\W\d]+",
    "non_negative_number": _NON_NEGATIVE_NUMBER_PATTERN_STRING,
    "operator_blacklist": r"[\*\+\-]\s*\*",
    "operator": r"[\+\-\*]",
    "whitespaces": r"\s+",
    "invalid": r".+?"
}
```

Here's an overview:
- **column** — matches tokens that are to be considered DataFrame column names (such as "employee_id"),
- **non_negative_number** — matches non-negative numbers to enable expressions such as "salary * 100" or "weight * .01",
- **operator_blacklist** — matches disallowed operator combinations (for example, "**" or "+*"),
- **operator** — matches allowed operators (currently "+", "-" and "*"),
- **whitespaces** — matches parts of the string that are to be considered whitespaces (currently "\s+"),
- **invalid** — matches invalid characters.

<br>

This allows you to change the function's behaviour easily. In many cases, you won't need to look any further than the aforementioned dictionary.

For example, to add the "/" operator, you only need to:
1. Modify the regex under key of "operator" to match "/",
1. Modify the regex under key of "operator_blacklist" to match invalid operator combinations containing "/". This is necessary to handle invalid expressions such as "column_one +/ column_two".

## Caveat
I made it possible to include numbers in the `role` expression. I am not entirely sure whether I was supposed to do that. I decided to add this feature, as it could have many uses and does not create any conflicts or security issues.