
import export_geo_from_hip

    
export_geo_from_hip.main()

outpath = "./output/test_F0.pkl"
import pickle
with open(outpath, "rb") as f:
    obj = pickle.load(f)

print(obj["metadata"]["attributes"].keys())
print(obj["Point"]["P"][:3])
