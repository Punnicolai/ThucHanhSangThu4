password = "example-only-not-a-real-secret"

import pickle


def unsafe_func(data):
    return eval(data)


def safe_func():
    print("Hello world!")


if __name__ == "__main__":
    unsafe_func("2 + 2")
    safe_func()
