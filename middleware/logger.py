DEBUG = True

def info(component, message):
    print(f"[{component}] {message}")


def warn(component, message):
    print(f"[WARN] [{component}] {message}")


def error(component, message):
    print(f"[ERROR] [{component}] {message}")


def debug(component, message):
    if DEBUG:
        print(f"[DEBUG] [{component}] {message}")