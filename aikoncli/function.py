import requests
import re
import json

from pathlib import Path
from tqdm import tqdm

def iiif_url_to_annotation_url(url_manifest: str) -> str:
    ''' '''
    match = re.search(r"(^https:\/\/.*)\/(.*)\/(.*\/wit)(\d+)(.*)\/(manifest\.json)", url_manifest)

    if match:
        radical_url = match.group(1)
        instance = match.group(2)
        witness_id = match.group(4)
        url_annotations = f"{radical_url}/{instance}/witness/{witness_id}/regions/canvas"
        print(url_annotations)
    else:
        raise ValueError('Invalide link')

    return url_annotations

def downloading_image_from_manifest(url_manifest: str, output_dir: Path) -> None:
    ''' '''
    request = requests.get(url_manifest)
    manifest = request.json()
    metadata = manifest['metadata']
    
    for i in metadata:
        if i['label'] == '@id':
            print(i)
            name = i['value']
            name = name.replace(' ', '')
            print(name)
            images_dir = Path(f"{output_dir}/{name}/images")
            images_dir.mkdir(parents=True, exist_ok=True)
            
    liste_url = []
    img_dict = {}
    i_id = 0
    
    for canvas in manifest.get('sequences')[0].get('canvases'):
      images = canvas.get('images')
      
      for image in images:
        resource = image.get('resource')
        
        if resource.get('@id'):
          url = resource.get('@id')
          liste_url.append(url)
          i_id += 1
          img_dict[i_id] = {
            "url": url,
            "height": resource.get('height'),
            "width": resource.get('width'),
                            }
          
    id_img = 0
    for i in tqdm(liste_url, desc="Downloading"):
        id_img += 1
        data = requests.get(i).content
        with open(f'{images_dir}/{id_img}.jpg', 'wb') as image_file:
            image_file.write(data)
            
    return img_dict, name

def iii_annotations_to_yolo(img_dict: dict, url_annotations: str, output_dir: Path, name: str) -> None:
    ''' '''
    labels_dir = Path(f"{output_dir}/{name}/labels")
    labels_dir.mkdir(parents=True, exist_ok=True)
    resultat_annotations = requests.get(url_annotations)
    print("Status :", resultat_annotations.status_code)
    print("Contenu :", repr(resultat_annotations.text[:300]))
    annotations_manifest = resultat_annotations.json()
    
    i_index = []
    
    for i in annotations_manifest:
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
                print('already in i_index')
                with open(f'{labels_dir}/{img_id}.txt', 'a') as f:
                    f.write(f'\n{line}')
            else :
                with open(f'{labels_dir}/{img_id}.txt', 'w') as f:
                    print(f'new entry')
                    f.write(f'{line}')
                    i_index.append(img_id)

def aikon_to_yolo(url_manifest: str, output_dir: Path):
    ''' '''
    url_annotations = iiif_url_to_annotation_url(url_manifest)
    img_dict, name = downloading_image_from_manifest(url_manifest, output_dir)
    iii_annotations_to_yolo(img_dict, url_annotations, output_dir, name)