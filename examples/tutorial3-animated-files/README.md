Related tutorial is at: https://gmic-py.readthedocs.io/en/latest/tutorials.html#tutorial-3-filtering-gif-and-videos

## ADVANCED NOTES (EXPERT)

```
# # Example of a longer GIF requiring multiple pages
# gmic.run(
#     "https://gmic.eu/gallery/img/codesamples_full_1.gif remove[0] repeat $! blur[$>] {$>*5} done frame 40,3 append_tiles 2,2 display rotate 90 resize_ratio2d 2100,2970 display"
# )
#
# # Example of live window demo
# gmic.run(
#     "w[] https://gmic.eu/gallery/img/codesamples_full_1.gif remove[0] repeat $! blur[$>] {$>*5} w[$>] done"
# )
```
