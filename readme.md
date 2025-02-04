# PyGame-Slides
A small personal project to render markdown files as slideshows using pygame.

The reason I built this is that I needed a very simple slides format that I could automate the creation of.

# Setup
I will try to add PyGame-Slides to pypi in the near future.

In the meantime;

```
$ git clone ....
$ cd pygame-slides
$ pip3 install -r pip-requirements.txt
$ python3 pyslides.py readme.md
```

# Limitations.
Since PyGame-Slides rely on [pygame-markdown](https://github.com/CribberSix/pygame-markdown) the support for markdown is not complete, but should be sufficient to make OK presentations.

# Formatting
Will be implemented eventually.

# The Slide
A slide is started with the top heading, i.e. # Title.

Everything written until the next slide is started or EOF belongs to that slide.

Textual elements will be formatted according to the style used. Images will be rendered into the image area of the slide.

## Remeber
* Depending on the style you might only have room for one image
* To many textual elements might lead to some elements that are rendered off-screen.

# Did you notice?
This readme can be presented with pyslides!
