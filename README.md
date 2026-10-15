A little cli tool to download images and bounding boxes annotations attached to an Aikon IIIF annotation server. The output format follow the YOLO style annotation system with two directory (images, labels) and a pair of documents (1.jpg, 1.txt).

To use me : 

```bash
python aikon.py url_aikon_manifest directory
```

Try me :

```bash
python aikoncli.py https://vhs.huma-num.fr/vhs/iiif/wit2320_img2562/manifest.json Aikon
```
