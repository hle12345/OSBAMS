"""Run kicad-cli (KiCad 10) through the container wrapper when KC10=1 (default for RC2); host kicad-cli 7 otherwise. Paths under the repo are translated to /work."""
import os, shlex, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
USE10 = os.environ.get("KC10", "1") == "1"
def tr(a): a = str(a); a = os.path.abspath(a) if a.startswith(("/", "./", "../")) and os.path.exists(a.rsplit("/", 1)[0] or "/") else a; return "/work" + a[len(REPO):] if a.startswith(REPO) else a
def kicli(*args):
    if not USE10: return subprocess.run(["kicad-cli", *map(str, args)], capture_output=True, text=True)
    cmd = "kicad-cli " + " ".join(shlex.quote(tr(a)) for a in args)
    return subprocess.run([os.path.join(HERE, "kc10_pi"), "bash", "-c", cmd], capture_output=True, text=True)
def kcpy(script, *args):
    """run a python script of this folder inside the KiCad 10 container (python3 + pcbnew 10)"""
    cmd = f"cd {tr(HERE)} && python3 {script} " + " ".join(shlex.quote(tr(a)) for a in args)
    return subprocess.run([os.path.join(HERE, "kc10_pi"), "bash", "-c", cmd], capture_output=True, text=True)
