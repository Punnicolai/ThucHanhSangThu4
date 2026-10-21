def dangerous_eval(user_input):
    return eval(user_input)

def execute_code(code):
    exec(code)


if __name__ == "__main__":
    dangerous_eval("print('Hello from eval')")
    execute_code("print('Hello from exec')")