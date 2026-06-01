import requests
import re
import json

from pathlib import Path
from tqdm import tqdm

def iiif_url_to_annotation_url(url_manifest: str) -> str:
    """
    Converts a IIIF manifest URL to its corresponding annotation URL.

    :param url_manifest: The IIIF manifest URL.
    :return: The annotation URL derived from the manifest URL.
    :raises ValueError: If the URL does not match the expected pattern.
    """
    match = re.search(r"(^https:\/\/.*)\/(.*)\/(.*\/wit)(\d+)(.*)\/(manifest\.json)", url_manifest)

    if match:
        radical_url = match.group(1)
        instance = match.group(2)
        witness_id = match.group(4)
        url_annotations = f"{radical_url}/{instance}/witness/{witness_id}/regions/canvas"
    else:
        raise ValueError('Invalide link')

    return url_annotations

def downloading_image_from_manifest(url_manifest: str, output_dir: Path) -> None:
    """
    Downloads all images from a IIIF manifest and saves them locally.
    Also builds a dictionary mapping image IDs to their metadata (url, height, width).

    :param url_manifest: The IIIF manifest URL.
    :param output_dir: The directory where images will be saved.
    :return: A tuple containing the image metadata dictionary and the witness name.
    """
    request = requests.get(url_manifest)
    manifest = request.json()
    name = next(
      (i['value'].replace(' ', '') for i in manifest['metadata'] if i['label'] == '@id'),
         None
      )
    if name is None:
         raise ValueError("No '@id' label found in manifest metadata")
         
    images_dir = Path(output_dir) / name / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
            
    canvases = manifest['sequences'][0]['canvases']

    img_dict = {
        i: {
            "url": r.get('@id'),
            "height": r.get('height'),
            "width": r.get('width'),
        }
        for i, canvas in enumerate(canvases, start=1)
        for image in canvas.get('images', [])
        if (r := image.get('resource')) and r.get('@id')
    }

    liste_url = [v["url"] for v in img_dict.values()]
          
    id_img = 0
    for img_id, meta in tqdm(img_dict.items(), desc="Downloading Images"):
        data = requests.get(meta['url']).content
        (images_dir / f"{img_id}.jpg").write_bytes(data)

    return img_dict, name

def iii_annotations_to_yolo(img_dict: dict, url_annotations: str, output_dir: Path, name: str) -> None:
    """
    Fetches annotations from an AIKON API endpoint and converts them to YOLO format label files.
    Each annotation's bounding box is normalized relative to its image dimensions.

    :param img_dict: Dictionary mapping image IDs to their metadata (url, height, width).
    :param url_annotations: The URL of the annotation endpoint.
    :param output_dir: The directory where label files will be saved.
    :param name: The witness name, used to build the output directory path.
    """
    labels_dir = Path(f"{output_dir}/{name}/labels")
    labels_dir.mkdir(parents=True, exist_ok=True)
    resultat_annotations = requests.get(url_annotations)
    annotations_manifest = resultat_annotations.json()
    
    i_index = set()
    
    for i in tqdm(annotations_manifest, desc="Fetching Annotations"):
        annotations = annotations_manifest.get(i)
        page_dictionnaire = img_dict.get(int(i))
        img_height = page_dictionnaire.get('height')
        img_width = page_dictionnaire.get('width')
        
        for annotation in annotations:
            img_id = (annotations.get(annotation).get('canvas'))
            x_tl, y_tl, w, h = annotations.get(annotation).get('xywh')
            x_center = (x_tl + w / 2) / img_width
            y_center = (y_tl + h / 2) / img_height
            width = w / img_width
            height = h / img_height
            line = f'0 {x_center} {y_center} {width} {height}'
            if img_id in i_index:
                with open(f'{labels_dir}/{img_id}.txt', 'a') as f:
                    f.write(f'\n{line}')
            else :
                with open(f'{labels_dir}/{img_id}.txt', 'w') as f:
                    f.write(f'{line}')
                    i_index.add(img_id)

def aikon_to_yolo(url_manifest: str, output_dir: str):
    """
    Orchestrates the full pipeline: converts a IIIF manifest URL to an annotation URL,
    downloads all images, and converts annotations to YOLO format label files.

    :param url_manifest: The IIIF manifest URL.
    :param output_dir: The directory where all outputs will be saved.
    """
    url_annotations = iiif_url_to_annotation_url(url_manifest)
    img_dict, name = downloading_image_from_manifest(url_manifest, output_dir)
    iii_annotations_to_yolo(img_dict, url_annotations, output_dir, name)