def validate_result(result, plan):
    """
    Validate that an execution result is structurally
    consistent with the requested operation.
    """

    operation = plan.operation.lower()

    if operation in {
        "count",
        "sum",
        "average",
        "minimum",
        "maximum",
    }:
        if result is None:
            raise ValueError(
                f"{operation} returned no result."
            )

        if not isinstance(
            result,
            (int, float),
        ):
            raise ValueError(
                f"{operation} returned an invalid "
                f"result: {result}"
            )

    elif operation in {
        "search",
        "filter",
        "sort",
    }:
        if not isinstance(result, list):
            raise ValueError(
                f"{operation} should return a list."
            )

    else:
        raise ValueError(
            f"Unsupported operation: {plan.operation}"
        )

    return True