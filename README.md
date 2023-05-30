## training-prep-tools

A library of useful tools for processing image data for AI image generation training.

Right now the tools are:

* `caption-manager` - A tool for processing a directory tree of YAML files to produce captions for the images in that tree.
* `process-training-images` - Read in `pdfimages`-extracted images and re-assemble, mask, scale them as needed.
  Also performs color map transformations as needed for CMYK (ready-for-print) TIFF images.

### Using `process-training-images`

The `process-training-images` script is designed to work in conjunction with the `pdfimages` program
(part of its own XpdfReader package, and available on many systems). It takes raw images that have
been extracted from PDF files and prepares them for training. This can include:

* Re-assembling "masked" images into transparent PNGs
* Converting transparency to flat images with backgrounds if desired
* Removing duplicate images (with some fuzziness)
* Performing color-table conversions for read-for-print CMYK images
* Scaling to the desired size (512x512 by default)

All of this can be controlled by the script's extensive command-line options.

### Using `caption-manager`

The `caption-manager` tool is designed to help you quickly develop a set of captions for your training images.
In order to use this manager, you need to structure your images in a tree of directories according to
your classification scheme. The specifics of the classification don't matter to the tool. You'll direct
it to understand via YAML files, but this is the basic process it goes through:

1. Read the `caption_config.yaml` in every directory in your source tree
2. Read the `<image>.yaml` file for every `<image>.png` file in your source tree
3. Write an `<image>.txt` file to teh target tree (defaults to the source tree) to go with the `<image>.png`

At step 3, all of the information from all of the `caption_config.yaml` files in the image's directory
and above will be merged and combined with this image's `<image>.yaml` file.

To get more detailed, here's a basic scenario: You have some pictures of mushrooms. These are stored
in a directory tree that:

* Has a top-level `caption_config.yaml`
* Has an `amanita` subdirectory with its own `caption_config.yaml` with 10 images
* Has a `russula` subdirectory with its own `caption_config.yaml` with 10 images
* `russula/russula_01.png` also has its own `russula/russula_01.yaml`

This is the top-level `caption_config.yaml`:

```YAML
topic: "mushroom"
keywords: "mycology, nature"
required: "topic, species"
caption: "{species} {topic}"
```

This is the `amanita/caption_config.yaml`:

```YAML
species: "amanita"
```

This is the `russula/caption_config.yaml`:

```YAML
species: "russula"
```

And this is the `russula/russula_01.yaml`:

```YAML
keywords: "bright red, pinhead mushroom"
```

For most images, the defaults will be gathered up, and as directed by the `caption` entry in the top-level config,
the caption will be the `species` value from the lower level config and the `topic` value ("mushroom") from the
top level config. But then the keywords are added.

Unlike other parameters, keywords are not overridden by lower-level configs. Instead, they are added to.
So the keywords `mycology, nature` will be added on to most captions as-is from the top-level config, but
in our example, the `russula/russula_01.yaml` gives some extra keywords, so for the `russula/russula_01.png`
image's caption, the keywords will be `mycology, nature, bright red, pinhead mushroom` because the two sets
of keywords were merged.

The caption template, `"{species} {topic}"` can be anything you like, but any parameter that you've defined
can be referenced here. You could, for example, have written, `"a {topic} of the {species} species"`. The
braces-enclosed parameters will be replaced by the specific value of that parameter for each image file and
written out to the caption file after all replacements are complete and the keywords are appended to the
caption.

The `required` field directs the tool to understand what fields need to be populated at some level, and is
currently considered advisory, but might result in an error at some point. Generally, anything you use in your
caption template should be in this list.

So in our example, every image in the `amanita` directory will get the same caption:

```
amanita mushroom, mycology, nature
```

While 9 of the images in `russula` will get the caption:

```
russula mushroom, mycology, nature
```

but the `russula/russula_01.png` image with its own YAML file will get:

```
russula mushroom, mycology, nature, bright red, pinhead mushroom
```

Using this system, you can quickly add captions to thousands of image files and then go back and add more
specific caption details as time permits in order to improve the quality of your training data.
