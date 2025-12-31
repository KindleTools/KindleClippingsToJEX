from PIL import Image
import os


def convert():
    src = os.path.join("resources", "icon.png")
    dst = os.path.join("resources", "icon.ico")

    if os.path.exists(src):
        img = Image.open(src)
        img.save(dst, format="ICO")
        print(f"Created {dst}")
    else:
        print(f"Source {src} not found")


if __name__ == "__main__":
    convert()
