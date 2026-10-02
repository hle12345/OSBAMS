import json, sys, os, urllib.request, tarfile, io, subprocess
repo, tag = "kicad/kicad", sys.argv[1]
def get(url, tok=None, accept=None, raw=False):
    req = urllib.request.Request(url)
    if tok: req.add_header("Authorization", "Bearer " + tok)
    if accept: req.add_header("Accept", accept)
    return urllib.request.urlopen(req, timeout=120)
tok = json.load(get(f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{repo}:pull"))["token"]
acc = "application/vnd.oci.image.index.v1+json,application/vnd.docker.distribution.manifest.list.v2+json,application/vnd.oci.image.manifest.v1+json,application/vnd.docker.distribution.manifest.v2+json"
m = json.load(get(f"https://registry-1.docker.io/v2/{repo}/manifests/{tag}", tok, acc))
if "manifests" in m:
    for x in m["manifests"]:
        p = x.get("platform", {})
        if p.get("architecture") == "amd64" and p.get("os") == "linux":
            m = json.load(get(f"https://registry-1.docker.io/v2/{repo}/manifests/{x['digest']}", tok, acc)); break
layers = m["layers"]
print("layers", len(layers), sum(l["size"] for l in layers)/1e6, "MB")
for i, l in enumerate(layers):
    dest = f"/tmp/kd/layer{i}.tar"
    print(i, l["digest"][:19], l["size"]/1e6, flush=True)
    r = get(f"https://registry-1.docker.io/v2/{repo}/blobs/{l['digest']}", tok)
    with open(dest + ".gz", "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b: break
            f.write(b)
    subprocess.run(["tar", "-xzf", dest + ".gz", "-C", "/opt/kicad10", "--exclude=dev/*", "--no-same-owner"], check=False)
    os.remove(dest + ".gz")
print("done")
