## training-prep-tools

A library of useful tools for processing image data for AI image generation training.

Right now the tools are:

* `caption-manager` - A tool for processing a directory tree of YAML files to produce captions for the images in that tree.
* `process-training-images` - Read in `pdfimages`-extracted images and re-assemble, mask, scale them as needed.
  Also performs color map transformations as needed for CMYK (ready-for-print) TIFF images.
