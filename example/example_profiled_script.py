from line_profiler import profile


@profile
def foo():
    for i in range(3):
        x = i * 2
    return x


foo()
