"""Helper: launch PSCAD, acquire the Pro certificate, release+quit on exit."""
import contextlib, os, mhi.pscad

# Some automation hosts set this variable; cmd.exe then refuses to find an
# executable in the current directory, which breaks PSCAD's *_30000.bat runner
# ("'case.exe' is not recognized ..."). PSCAD inherits our environment, so drop it.
os.environ.pop("NoDefaultCurrentDirectoryInExePath", None)

@contextlib.contextmanager
def pscad_session(minimize=True):
    pscad = mhi.pscad.launch(minimize=minimize)
    try:
        if not pscad.licensed():
            certs = pscad.get_available_certificates(refresh=True)
            if not certs:
                raise RuntimeError("No PSCAD licence certificates available (logged_in=%s)" % pscad.logged_in())
            pscad.get_certificate(next(iter(certs.values())))
        if not pscad.licensed():
            raise RuntimeError("Could not acquire PSCAD licence")
        yield pscad
    finally:
        try:
            pscad.release_all_certificates()
        except Exception:
            pass
        pscad.quit()
