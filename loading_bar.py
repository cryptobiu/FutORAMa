import sys

def update_loading_bar(progress):
    bar_length = 50
    block = int(round(bar_length * progress))
    progress_percent = progress * 100
    bar = "#" * block + "-" * (bar_length - block)

    sys.stdout.write(f"\r[{bar}] {progress_percent:.1f}%")
    sys.stdout.flush()