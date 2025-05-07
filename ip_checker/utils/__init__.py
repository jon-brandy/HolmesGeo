from termcolor import colored

def colored_print(message, color, style=None):
    print(colored(message, color, attrs=[style] if style else []))