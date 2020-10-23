$graph:
- baseCommand: burned-area-ref
  hints:
    DockerRequirement:
      dockerPull: eoepca/burned-area-ref:0.2
  class: CommandLineTool
  id: clt
  inputs:
    inp1:
      inputBinding:
        position: 1
        prefix: --pre_event
      type: string
    inp2:
      inputBinding:
        position: 2
        prefix: --post_event
      type: string
    inp3:
      inputBinding:
        position: 3
        prefix: --ndvi_threshold
      type: string
    inp4:
      inputBinding:
        position: 4
        prefix: --ndwi_threshold
      type: string
  outputs:
    results:
      outputBinding:
        glob: .
      type: Directory
  requirements:
    EnvVarRequirement:
      envDef:
        PATH: /opt/anaconda/envs/env_burned_area/bin:/home/fbrito/.nvm/versions/node/v10.21.0/bin:/opt/anaconda/bin:/usr/share/java/maven/bin:/opt/anaconda/bin:/opt/anaconda/bin:/usr/share/java/maven/bin:/opt/anaconda/bin:/opt/anaconda/condabin:/opt/anaconda/envs/notebook/bin:/opt/anaconda/bin:/usr/lib64/qt-3.3/bin:/usr/share/java/maven/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin
        PREFIX: /opt/anaconda/envs/env_burned_area
    ResourceRequirement: {}
  stderr: std.err
  stdout: std.out
- class: Workflow
  doc: Sentinel-2 burned area with NDVI/NDWI threshold
  id: burned-area
  inputs:
    pre_event:
      doc: Sentinel-2 Level-2A pre-event acquisition
      label: Sentinel-2 Level-2A pre-event
      type: string
    post_event:
      doc: Sentinel-2 Level-2A pre-event acquisition
      label: Sentinel-2 Level-2A pre-event
      type: string
    ndvi_threshold:
      doc: NDVI difference threshold
      label: NDVI difference threshold
      type: string
    ndwi_threshold:
      doc: NDVI difference threshold
      label: NDVI difference threshold
      type: string
  label: Sentinel-2 burned area
  outputs:
  - id: wf_outputs
    outputSource:
    - node_1/results
    type:
      Directory
  steps:
    node_1:
      in:
        inp1: pre_event
        inp2: post_event
        inp3: ndvi_threshold
        inp4: ndwi_threshold
      out:
      - results
      run: '#clt'
cwlVersion: v1.0
