lektor-imgutils
===============

lektor-imgutils is a plugin for the `Lektor <https://www.getlektor.com>`_
static site generator
that manipulates image files and image-related markup
after the build is completed.

To use the plugin, add it to your project::

  lektor plugin add lektor-imgutils

The plugin can be configured using the ``configs/imgutils.ini`` file.
Each section specifies a rule that will be applied to selected images.
Each section must have a "selector" key which is a CSS selector
to select the image elements.
The section names are insignificant.

Examples
--------

Set missing width and height attributes to all images::

  [default]
  selector = img
  size = yes

Set lazy loading and async decoding on all images in the ".content" part::

  [content]
  selector = .content img
  loading = lazy
  decoding = async
