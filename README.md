# Houdini Geometry I/O Schema

This repo attempts to provide a way to export all attributes in Houdini Geometry Spreadsheet in simple custom schema. 

It will parse attribute to a tree structure like below:

```
<Name>_F<Frame>
  │  metadata.json
  │
  ├─Detail
  │      testdetail.txt
  │
  ├─Point
  │      P.npy
  │      testpoint.npy
  │
  ├─Primitive
  │      testprim.npy
  │
  └─Vertex
          nvertices_rle.npy
          pointref.npy
          vertexcount.npy
```

`<Name>` : Geometry name
`<Frame>` : Frame number
The file could be ".npy", "ASCII" format or any others as needed.

This tree structure can be dumped into single pickle file(`format=single`) or multiple files in folders(`format=binary/npy/ASCII`).


There are three ways to read/write bgeo files:
1. hython: Slow, can read from hip/geo/bgeo, but slow. Must install the Houdini.
3. hgeo: Slow, can read from bgeo/geo. No need to install the Houdini. 
2. hjson: Fast, can read from bgeo/geo. Must install the Houdini.

To be simple, We use the first method in this repo and read from hip file. This is flexible because you can use it either inside Houdini or outside Houdini. We plan to support hgeo in the future.



## Usage1: Call outside Houdini, from hip file
Hython is Houdini specialized Python interpreter. It probably located at:
`C:\Program Files\Side Effects Software\Houdini 21.0.440\bin\hython.exe`

In the following, use this python instead of your own python. In the project dir(this repo), run:

```
& "C:\Program Files\Side Effects Software\Houdini 21.0.440\bin\hython.exe" `
  "export_geo_from_hip.py" `
  --config "config\export_test.json"
```
(This is a powershell command)

Run `install.py` to copy geoschema.py to Houdini user python libs folder(`C:\Users\<YourUsername>\Documents\houdini21.0\python3.11libs`), then you can run it anywhere other than this repo as well.


## Usage2: Call inside Houdini, from python SOP node
Use a python SOP node and copy all the code from `geoschema.py` to the node.

In the beginning and end of the code, add the following lines:

```python
node = hou.pwd()
geo = node.geometry()
...(copy geoschema.py here)...
hip_dir = hou.expandString("$HIP")
export_geo_schema(node,hip_dir,"test",1,"ascii")
```

It will automatically export the geometry named "test" at frame 1 to the folder of hip file in ASCII format.

## Usage3: Call outside Houdini, from geo/bgeo file

hgeo can do this. 

Try a naive solution:

```
python hgeo.py
```


This script is from 
`C:\Program Files\Side Effects Software\Houdini 21.0.440\houdini\public\hgeo` with only minor modification (including bugfix for reading bgeo file).

I haven't parsed it to the custom schema yet, and it is still in houdini's schema but this is not difficult to do.


## References
[Official HDK doc](https://www.sidefx.com/docs/hdk/_h_d_k__g_a__using.html#HDK_GA_FileFormat)

## TODO
- [x] read from hip by hython
- [] read from python sop node
- [] read from bgeo/geo by hgeo 
- [] read from bgeo/geo by hjson