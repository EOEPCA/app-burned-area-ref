## Burned-area

### Local installation

```bash
git clone https://github.com/EOEPCA/app-burned-area-ref.git
cd app-burned-area-ref
```

Create the conda environment

```bash
conda env create -f environment.yml
conda activate env_burned_area
```

Install the application with:

```bash
python setup.py install
```
 
Print the help context:

```bash
(env_burned_area) $ burned-area-ref --help
Usage: burned-area-ref [OPTIONS]

Options:
  --pre_event TEXT        Sentinel-2 Level-2A pre-event acquisition
  --post_event TEXT       Sentinel-2 Level-2A post-event acquisition
  --ndvi_threshold FLOAT  NDVI difference threshold
  --ndwi_threshold FLOAT  NDWI difference threshold
  --help                  Show this message and exit.
(env_burned_area)
```

### Deployment as a processing service

Use the payload below to deploy the Application Package with a POST on the /processes endpoint:

```json
{
  "inputs": [
    {
      "id": "applicationPackage",
      "input": {
        "format": {
          "mimeType": "application/cwl"
        },
        "value": {
          "href": "https://raw.githubusercontent.com/EOEPCA/app-burned-area-ref/master/burned-area-ref.cwl"
        }
      }
    }
  ],
  "outputs": [
    {
      "format": {
        "mimeType": "string",
        "schema": "string",
        "encoding": "string"
      },
      "id": "deployResult",
      "transmissionMode": "value"
    }
  ],
  "mode": "auto",
  "response": "raw"
}
```

With Python:

```python
import requests 

token = 'aaa'

endpoint = 'http://wps-eoepca.terradue.com' 

deploy_headers = {'Authorization': f'Bearer {token}',
                  'Content-Type': 'application/json',
                  'Accept': 'application/json', 
                  'Prefer': 'respond-async'} 

deploy_payload = {
  "inputs": [
    {
      "id": "applicationPackage",
      "input": {
        "format": {
          "mimeType": "application/cwl"
        },
        "value": {
          "href": "https://raw.githubusercontent.com/EOEPCA/app-burned-area-ref/master/burned-area-ref.cwl"
        }
      }
    }
  ],
  "outputs": [
    {
      "format": {
        "mimeType": "string",
        "schema": "string",
        "encoding": "string"
      },
      "id": "deployResult",
      "transmissionMode": "value"
    }
  ],
  "mode": "auto",
  "response": "raw"
}

r = requests.post(f'{endpoint}/wps3/processes',
                  json=deploy_payload,
                  headers=deploy_headers)

print(r.status_code, r.reason)
```