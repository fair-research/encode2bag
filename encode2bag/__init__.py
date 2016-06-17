def get_named_exception(e):
    exc = "".join(("[", type(e).__name__, "] "))
    return "".join((exc, str(e)))