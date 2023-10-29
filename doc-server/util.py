def get_safe_filename(file_name: str) -> str:
    return "".join(
        [c for c in file_name if c.isalpha() or c.isdigit() or c == " " or c == "."]
    ).rstrip()
