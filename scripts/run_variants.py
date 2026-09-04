"""Variant runs on one build of CIGRE-MV-PSCAD (Python 3.7 + mhi.pscad):
  1. base radial case at 12.5 us (time-step check against the 50 us run)
  2. meshed case: S2 and S3 closed (S1 open) at 50 us
Outputs go to pscad/tests/variants/<label>/ ; the 3.11 validator is run afterwards by hand."""
import os, sys, time, shutil, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pscad_session import pscad_session
import build_cigre_mv as B

name = "variants"; cdir = os.path.join(B.ROOT, "pscad", "tests", "variants", name)
with pscad_session() as pscad:
    t0 = time.time()
    prj = B.build(pscad, dt=50.0, dur=1.0, out_dir=cdir, name=name, log=lambda *x: None)
    print("build %.0fs" % (time.time() - t0), flush=True)
    main = prj.canvas("Main")
    consts = {c.parameters()["Name"]: c for c in main.find_all("master:const")}
    def run(label):
        prj.save(); t1 = time.time(); prj.run()
        bad = [m for m in prj.messages() if m.status == "error"]
        if bad:
            print("ERROR", label, [m.text[:100] for m in bad]); return
        src = glob.glob(os.path.join(cdir, name + ".gf81*"))[0]
        dst = os.path.join(B.ROOT, "pscad", "tests", "variants", label, name + ".gf81_x86")
        if os.path.exists(os.path.dirname(dst)): shutil.rmtree(os.path.dirname(dst))
        os.makedirs(os.path.dirname(dst)); shutil.copytree(src, dst)
        print("%s done in %.0fs -> %s" % (label, time.time() - t1, dst), flush=True)
    prj.parameters(time_step=12.5, sample_step=12.5); run("radial_12p5us")
    prj.parameters(time_step=50.0, sample_step=50.0)
    consts["S2_open"].parameters(Value=0.0); consts["S3_open"].parameters(Value=0.0); run("meshed_S2S3_50us")
    consts["S2_open"].parameters(Value=1.0); consts["S3_open"].parameters(Value=1.0); prj.save()
print("variants finished")
